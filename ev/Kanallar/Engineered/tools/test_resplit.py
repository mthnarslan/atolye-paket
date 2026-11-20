"""Offline check: a second failure of a rewritten chunk asks for a split; first failure asks for a reword."""
import sys
sys.path.insert(0, r"C:\Users\meteh\.gemini\scripts")
import documentary_voice_repair as r

cur = "The remaining three victims were inside a home on the western edge of Redding: a seventy-year-old woman and her two young great-grandchildren."
issues = [{"start_sec": 1, "end_sec": 2, "expected": "x", "heard": "y", "reason": "skipped"}]
prompts = []
def flash(split_reply):
    def f(prompt):
        prompts.append(prompt); return {"corrected_text": split_reply}
    return f
good = "Three more victims were inside a home. It stood on the western edge of Redding. They were a seventy-year-old woman and her two young great-grandchildren."
assert r.propose_text(cur, issues, flash(good), split=True) == good
assert "split the sentence" in prompts[-1]
# a reword that is not shorter sentences is refused in split mode, accepted otherwise
reword = "The remaining three victims were in a home on the western edge of Redding: a seventy-year-old woman and her two young great-grandchildren."
assert r.propose_text(cur, issues, flash(reword), split=True) is None
assert r.propose_text(cur, issues, flash(reword)) == reword
assert "split the sentence" not in prompts[-1]
assert r.MAX_REPAIR_ROUNDS == 3
print("OK")
