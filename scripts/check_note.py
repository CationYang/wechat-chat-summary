#!/usr/bin/env python3
"""Validate a distilled note against its profile and the source messages.

Checks frontmatter fields, section order, quote attribution (delegates to check_quotes.py),
message-count consistency, and status enum values in tables with a 状态 column.
Exit code 1 means at least one check failed.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROFILES = {
    "decision": ["一、概览", "二、关键要点", "三、决策与待办", "四、未闭环 / 待确认",
                 "五、原话摘录", "六、附录"],
    "knowledge": ["一、概览", "二、主题梳理", "三、结论与共识", "四、事实与数据",
                  "五、方法与案例", "六、原话摘录", "七、附录"],
    "crm": ["一、概览", "二、客户信息", "三、需求与痛点", "四、异议与回应",
            "五、报价与承诺", "六、下一步动作", "七、原话摘录", "八、附录"],
}
REQUIRED_FM = ("title", "source", "created", "range", "message_count", "tags")
STATUS = {"已定", "待确认", "已完成", "部分完成", "〔未证实〕"}


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def check_sections(text, profile):
    expected = PROFILES[profile]
    heads = [h.strip() for h in re.findall(r"^##\s+(.+)$", text, re.M)]
    present = [h for h in heads if h in expected]
    problems = []
    idx = [expected.index(h) for h in present]
    if idx != sorted(idx):
        problems.append("section order mismatch")
    for required in (expected[0], expected[-1]):
        if required not in present:
            problems.append(f"missing required section: {required}")
    return len(present), len(expected), problems


def check_status(text):
    bad = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("|") or "状态" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if "状态" not in cells:
            continue
        col = cells.index("状态")
        for row in lines[i + 2:]:
            if not row.strip().startswith("|"):
                break
            cs = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cs) <= col:
                continue
            val = cs[col]
            if not val or set(val) <= set("-: "):
                continue
            if val not in STATUS:
                bad.append(val)
    return bad


def main():
    ap = argparse.ArgumentParser(description="Validate a distilled note")
    ap.add_argument("markdown")
    ap.add_argument("messages")
    ap.add_argument("--profile", default="", help="override; else frontmatter profile; else decision")
    args = ap.parse_args()

    text = Path(args.markdown).read_text(encoding="utf-8")
    msgs = json.loads(Path(args.messages).read_text(encoding="utf-8"))
    fm = parse_frontmatter(text)
    problems = []

    if fm is None:
        problems.append("missing frontmatter")
        fm = {}
    for key in REQUIRED_FM:
        if key not in fm:
            problems.append(f"frontmatter missing: {key}")

    profile = args.profile or fm.get("profile") or "decision"
    if profile not in PROFILES:
        print(f"[ERR] unknown profile: {profile}")
        return 2

    n_present, n_expected, sec_problems = check_sections(text, profile)
    problems.extend(sec_problems)

    total = len(msgs)
    declared = fm.get("message_count", "")
    if declared.isdigit() and int(declared) != total:
        problems.append(f"frontmatter message_count={declared} but messages.json has {total}")
    m = re.search(r"消息数[：:]\s*(\d+)", text)
    if m and int(m.group(1)) != total:
        problems.append(f"appendix 消息数={m.group(1)} but messages.json has {total}")

    for lineno, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*[-*]?\s*「.+?」\s*[—–-]+\s*([^〔〕]+?)\s*(?:〔[^〕]+〕)?\s*$", line)
        if m and not re.match(r"^【.+】$", m.group(1).strip()):
            problems.append(f"L{lineno} speaker not in 【】: {m.group(1).strip()}")

    bad_status = check_status(text)
    if bad_status:
        problems.append("illegal status values: " + ", ".join(sorted(set(bad_status))))

    checker = Path(__file__).with_name("check_quotes.py")
    proc = subprocess.run([sys.executable, str(checker), args.markdown, args.messages],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    verdict = [l for l in (proc.stdout or "").splitlines() if l.startswith("归因校验")]
    verdict_line = verdict[-1] if verdict else "归因校验：未取得结果"
    if proc.returncode != 0:
        problems.append("quote audit failed")

    print(f"profile: {profile}")
    print(f"sections: {n_present}/{n_expected}")
    print(f"messages: {total}")
    print(verdict_line)
    print("status: " + ("OK" if not bad_status else "FAIL"))
    if problems:
        for p in problems:
            print("[FAIL] " + p)
        print(f"笔记校验：{len(problems)} 项未通过")
        return 1
    print("笔记校验：全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
