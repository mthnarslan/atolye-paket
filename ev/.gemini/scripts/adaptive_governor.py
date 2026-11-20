"""Measured, per-channel condition limits shared by production modules."""
from contextlib import contextmanager
from collections import deque
import heapq
import itertools
import json
from pathlib import Path
import threading
import time

PROFILE = Path(__file__).with_name("system_speed_profile.json")

class AdaptiveGovernor:
    def __init__(self, profile=None):
        self.condition = threading.Condition()
        self.channels = {}
        self._tickets = itertools.count()
        self.profile = profile if profile is not None else self._read_profile()

    def _read_profile(self):
        try:
            return json.loads(PROFILE.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, ValueError):
            return {}

    def reload_profile(self):
        try:
            updated = json.loads(PROFILE.read_text(encoding="utf-8-sig"))  # REWRITE: self.path -> PROFILE
        except (OSError,ValueError):
            updated={}
        with self.condition:
            changed=updated!=self.profile
            self.profile=updated
            if changed and not any(s["active"] for s in self.channels.values()):
                self.channels={}
        return self

    def _profile_channel(self, channel):
        if channel in ("flash", "codex", "sonnet", "review"):
            return self.profile.get("api", {}).get("roles", {}).get(channel, {})
        return self.profile.get("hardware", {}).get("channels", {}).get(channel, {})

    def _state(self, channel):
        if channel not in self.channels:
            cfg = self._profile_channel(channel)
            # Without calibration there is no evidence for a higher hardware/API ceiling.
            fallback = {"flash": 15, "flash_review": 10, "gdirect": 20, "codex": 4, "sonnet": 4, "review": 4, "hyperframes": 2, "nvenc": 2, "cpu": 4}.get(channel, 1)
            limit = max(1, int(cfg.get("concurrency", fallback)))
            self.channels[channel] = {"limit": limit, "min_limit": max(1, int(cfg.get("min_concurrency", 1))), "ceiling": max(limit, int(cfg.get("max_concurrency", limit))),
                "active": 0, "peak": 0, "good": 0, "samples": deque(maxlen=32), "adjustments": 0,
                "payload": cfg.get("payload", {"height": 720, "quality": 80}),
                "hedge_after_seconds": cfg.get("hedge_after_seconds")}
        return self.channels[channel]

    def config(self, channel):
        with self.condition:
            state=self._state(channel)
            result={k:v.copy() if isinstance(v,dict) else v for k,v in state.items() if k not in ("samples","waiting")}
            result["waiting"]=len(state.get("waiting",()))
            result["hedge_enabled"]=self._profile_channel(channel).get("hedge_enabled",True)
            return result

    def acquire(self, channel, cancel=None, prio=1):
        """Take one slot of the channel; waiters leave in (prio, arrival) order.

        A lower prio goes first: a shot review (0) holds a shot worker and
        the film behind it, so it never waits behind planning or precheck
        work (1, 2) that arrived earlier (2026-11-06, EP04/EP05 review p90
        126 s behind prechecks). Equal priorities keep their arrival order.
        """
        with self.condition:
            s = self._state(channel)
            waiting = s.setdefault("waiting", [])
            ticket = (prio, next(self._tickets))
            heapq.heappush(waiting, ticket)
            try:
                while s["active"] >= s["limit"] or waiting[0] != ticket:
                    if cancel:
                        cancel()
                    self.condition.wait(.2)
                if cancel:
                    cancel()
            finally:
                waiting.remove(ticket)
                heapq.heapify(waiting)
                self.condition.notify_all()
            s["active"] += 1
            s["peak"] = max(s["peak"], s["active"])

    def try_acquire(self, channel):
        with self.condition:
            s = self._state(channel)
            if s["active"] >= s["limit"] or s.get("waiting"):
                return False
            s["active"] += 1
            s["peak"] = max(s["peak"], s["active"])
            return True

    def release(self, channel):
        with self.condition:
            s = self._state(channel)
            if s["active"] <= 0:
                raise RuntimeError("Unbalanced governor release: " + channel)
            s["active"] -= 1
            self.condition.notify_all()

    @contextmanager
    def slot(self, channel, cancel=None):
        self.acquire(channel, cancel)
        try:
            yield
        finally:
            self.release(channel)

    def observe(self, channel, seconds, success, status=None, error_type=None):
        with self.condition:
            s = self._state(channel)
            cfg = self._profile_channel(channel)
            budget = float(cfg.get("latency_budget_seconds", 25))
            median = sorted(s["samples"])[len(s["samples"])//2] if s["samples"] else budget
            slow = channel in ("flash", "codex") and success and len(s["samples"]) >= 4 and seconds > max(budget, 1.5*median)
            pressure = status in (429, 502, 503, 504) or error_type in ("ReadTimeout", "ConnectTimeout", "Timeout", "TimeoutError", "ResourcePressure") or slow
            if pressure:
                # Flash concurrency is an explicit operator requirement. Keep
                # its calibrated request count fixed; only the request result
                # is recorded so the run can report pressure instead of
                # silently serializing the pipeline.
                if channel == "flash":
                    s["limit"] = s["ceiling"]
                    s["good"] = 0
                    self.condition.notify_all()
                    return
                previous = s["limit"]
                s["limit"] = max(s.get("min_limit", 1), s["limit"]-max(1,min(2,s["limit"]//4)))
                s["adjustments"] += int(s["limit"] != previous)
                s["good"] = 0
                if channel in ("flash", "codex"):
                    smaller = [p for p in cfg.get("qualified_payloads", []) if int(p["height"]) < int(s["payload"]["height"])]
                    if smaller:
                        s["payload"] = max(smaller,key=lambda p:int(p["height"]))
                        s["limit"] = min(s["limit"], s["payload"].get("max_concurrency",s["limit"]))
                        s["ceiling"] = min(s["ceiling"], s["payload"].get("max_concurrency",s["ceiling"]))
            elif success and seconds <= budget:
                s["good"] += 1
                if s["good"] >= max(2,s["limit"]):
                    previous = s["limit"]
                    s["limit"] = min(s["ceiling"],s["limit"]+1)
                    s["adjustments"] += int(s["limit"] != previous)
                    s["good"] = 0
            if success:
                s["samples"].append(float(seconds))
            self.condition.notify_all()

    def snapshot(self):
        with self.condition:
            return {name: self.config(name) for name in self.channels}

_GOVERNOR = AdaptiveGovernor()
def get_governor():
    return _GOVERNOR
