"""
Codex Unified Gateway for LobeChat
Routes requests transparently between:
- GPT / Codex models -> http://100.104.78.117:8765/v1
- Claude / Flash models -> http://100.104.78.117:20128/v1
Includes intelligent aliasing for default OpenAI/Claude/Gemini models to prevent 400 errors.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator

import httpx
# Bypass problematic zstd decoding on Windows for Cloudflare/OceanAPI responses
from httpx._decoders import SUPPORTED_DECODERS
if 'zstd' in SUPPORTED_DECODERS:
    del SUPPORTED_DECODERS['zstd']

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load secrets from Windows Credential Manager
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vds_secret_store import read_secret

VDS_BASE_URL = "http://100.104.78.117:8765/v1"
ROUTER_BASE_URL = "http://100.104.78.117:20128/v1"

VDS_KEY = read_secret("codex_vds")
ROUTER_KEY = read_secret("codex_router")

# Intelligent model aliases to ensure default requests in LobeChat NEVER fail
MODEL_ALIASES = {
    "gpt-4o": "gpt-6-sol",
    "gpt-4o-mini": "ag/gemini-3.8-flash-high",
    "gpt-4": "gpt-6-sol",
    "gpt-4-turbo": "gpt-6-sol",
    "gpt-3.5-turbo": "ag/gemini-3.8-flash-high",
    "claude-3-5-sonnet-20241022": "ag/claude-sonnet-5-5-high",
    "claude-3-5-sonnet-latest": "ag/claude-sonnet-5-5-high",
    "claude-3-7-sonnet": "ag/claude-sonnet-5-5-high",
    "claude-3-5-sonnet": "ag/claude-sonnet-5-5-high",
    "claude-3-opus-latest": "claude-opus-5",
    "claude-3-opus": "claude-opus-5",
    "gemini-1.5-flash": "ag/gemini-3.8-flash-high",
    "gemini-2.0-flash": "ag/gemini-3.8-flash-high",
    "gemini-2.0-flash-exp": "ag/gemini-3.8-flash-high",
}

app = FastAPI(title="Codex Unified Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "gateway": "Codex Unified Gateway for LobeChat", "port": 20130}

@app.get("/v1/models")
async def list_models():
    """Aggregate models from both VDS and Router + provide helpful aliases."""
    merged_models = []
    seen_ids = set()

    headers = {"Accept-Encoding": "gzip, deflate"}
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        # Fetch from VDS (GPT models)
        try:
            r = await client.get(f"{VDS_BASE_URL}/models", headers={"Authorization": f"Bearer {VDS_KEY}"})
            if r.status_code == 200:
                for m in r.json().get("data", []):
                    m_id = m.get("id")
                    if m_id and m_id not in seen_ids:
                        seen_ids.add(m_id)
                        merged_models.append(m)
        except Exception as e:
            print(f"[GATEWAY] VDS models fetch error: {e}", file=sys.stderr)

        # Fetch from Router (Flash & Claude models)
        try:
            r = await client.get(f"{ROUTER_BASE_URL}/models", headers={"Authorization": f"Bearer {ROUTER_KEY}"})
            if r.status_code == 200:
                for m in r.json().get("data", []):
                    m_id = m.get("id")
                    if m_id and m_id not in seen_ids:
                        seen_ids.add(m_id)
                        merged_models.append(m)
        except Exception as e:
            print(f"[GATEWAY] Router models fetch error: {e}", file=sys.stderr)

    # Append alias models so LobeChat UI accepts default picks cleanly
    for alias_id in MODEL_ALIASES:
        if alias_id not in seen_ids:
            seen_ids.add(alias_id)
            merged_models.append({
                "id": alias_id,
                "object": "model",
                "owned_by": "codex-gateway",
                "permission": []
            })

    return {"object": "list", "data": merged_models}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Route chat completion to the correct upstream based on model name."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    raw_model = body.get("model", "")
    # Resolve aliases (e.g. gpt-4o -> gpt-6-sol)
    model_name = MODEL_ALIASES.get(raw_model, raw_model)
    if not model_name:
        model_name = "gpt-6-sol"

    # Update body with resolved model name
    body["model"] = model_name

    # Decide routing target
    is_router_target = (
        model_name.startswith("ag/") or
        model_name.startswith("mmf/") or
        model_name.startswith("oc/")
    )

    if is_router_target:
        target_url = f"{ROUTER_BASE_URL}/chat/completions"
        auth_key = ROUTER_KEY
    else:
        target_url = f"{VDS_BASE_URL}/chat/completions"
        auth_key = VDS_KEY

    print(f"[GATEWAY] Routing model '{raw_model}' -> '{model_name}' via {target_url}", flush=True)

    # Note: Do NOT set Accept-Encoding for SSE streaming to prevent buffering
    headers = {
        "Authorization": f"Bearer {auth_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream, application/json",
    }

    client = httpx.AsyncClient(timeout=180.0)

    try:
        req = client.build_request("POST", target_url, json=body, headers=headers)
        upstream_resp = await client.send(req, stream=True)

        async def stream_generator() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk
            finally:
                await upstream_resp.aclose()
                await client.aclose()

        content_type = upstream_resp.headers.get("content-type", "text/event-stream")
        return StreamingResponse(
            stream_generator(),
            status_code=upstream_resp.status_code,
            headers={
                "Content-Type": content_type,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as exc:
        await client.aclose()
        print(f"[GATEWAY] Upstream error: {exc}", file=sys.stderr, flush=True)
        return JSONResponse(
            status_code=502,
            content={"error": {"message": f"Gateway upstream error: {str(exc)}", "type": "gateway_error"}}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=20130, log_level="info")
