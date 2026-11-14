#!/usr/bin/env python3
"""Suggest an output profile from messages.json using gated signal counts.

crm has a hard gate (a real customer conversation has few speakers); decision and knowledge
compete on signal density, with decision preferred when counts are close.
"""
import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CRM = ("报价", "合同", "客户", "能不能便宜", "什么时候能交", "售后")
DECISION = ("定了", "负责人", "截止", "排期", "待办", "复盘", "交付", "谁来做")
KNOWLEDGE = ("分享", "报告", "数据", "趋势", "怎么看", "学到了", "教程", "实测", "为什么")


def detect(msgs):
    speakers = {m.get("speaker", "") for m in msgs if m.get("speaker", "")}
    counts = {}
    for name, words in (("crm", CRM), ("decision", DECISION), ("knowledge", KNOWLEDGE)):
        counts[name] = sum(1 for m in msgs
                           if any(w in m.get("content", "") for w in words))
    gate = len(speakers) <= 3 and counts["crm"] >= 3
    if gate:
        return "crm", counts, len(speakers), "crm gate passed"
    d, k = counts["decision"], counts["knowledge"]
    if d == 0 and k == 0:
        return "decision", counts, len(speakers), "no cue, conservative fallback"
    if k > d and d < k * 0.8:
        return "knowledge", counts, len(speakers), "knowledge density wins"
    return "decision", counts, len(speakers), "decision wins or counts are close"


def main():
    ap = argparse.ArgumentParser(description="Suggest an output profile")
    ap.add_argument("messages", help="messages.json from parse_chat.py")
    args = ap.parse_args()
    msgs = json.loads(Path(args.messages).read_text(encoding="utf-8"))
    if isinstance(msgs, dict):
        msgs = msgs.get("messages", [])
    profile, counts, n, reason = detect(msgs)
    print(f"profile: {profile}")
    print(f"signals: crm={counts['crm']}, decision={counts['decision']}, "
          f"knowledge={counts['knowledge']}")
    print(f"active_speakers: {n}")
    print(f"reason: {reason}")
    if counts["crm"] >= 3 and n > 3:
        print("crm_gate: excluded (needs <= 3 speakers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
