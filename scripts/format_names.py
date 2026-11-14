#!/usr/bin/env python3
"""Normalize speaker names in a distilled note to 【微信原始昵称】 and remove alias rosters.

Earlier versions used shortened 主名 plus a 发言人对照 table. The current rule is simpler: use the
raw WeChat nickname verbatim inside 【】. No derivation, no lookup table. Idempotent.

  format_names.py <note.md> <messages.json> [--out PATH] [--dry-run]
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RE_PROTECT = re.compile(r"「[^」]*」")
RE_BRACKET = re.compile(r"【([^】]+)】")
RE_ROSTER_ROW = re.compile(r"^\|\s*【(.+?)】\s*\|\s*(.+?)\s*\|\s*$")
RE_HOLDER = re.compile(r"\x00P(\d+)\x00")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    ap = argparse.ArgumentParser(description="Use raw WeChat nicknames in 【】")
    ap.add_argument("markdown")
    ap.add_argument("messages")
    ap.add_argument("--out", default="", help="output path; defaults to in-place")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    msgs = json.loads(Path(args.messages).read_text(encoding="utf-8"))
    if isinstance(msgs, dict):
        msgs = msgs.get("messages", [])
    counts = Counter(m.get("speaker", "") for m in msgs)
    speakers = [s for s in counts if s]

    text = Path(args.markdown).read_text(encoding="utf-8")
    aliases = {}
    for line in text.splitlines():
        m = RE_ROSTER_ROW.match(line.strip())
        if m:
            aliases.setdefault(m.group(1).strip(), []).append(
                m.group(2).strip().replace("\\|", "|"))

    def resolve(name):
        clean = name.replace("\\|", "|")
        if clean in aliases:
            return max(aliases[clean], key=lambda s: counts.get(s, 0))
        n = norm(clean)
        for s in speakers:
            if norm(s) == n:
                return s
        if len(n) >= 2:
            cands = [s for s in speakers if norm(s).startswith(n)]
            if cands:
                return max(cands, key=lambda s: counts[s])
        return clean

    lines = text.splitlines()
    out, used, changed, in_fm = [], set(), [0], False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_fm = True
            out.append(line)
            continue
        if in_fm:
            out.append(line)
            if line.strip() == "---":
                in_fm = False
            continue

        holders = []

        def stash(m):
            holders.append(m.group(0))
            return f"\x00P{len(holders) - 1}\x00"

        work = RE_PROTECT.sub(stash, line)
        in_table = line.lstrip().startswith("|")

        def repl(m):
            raw = resolve(m.group(1))
            used.add(raw)
            if raw != m.group(1).replace("\\|", "|"):
                changed[0] += 1
            shown = raw.replace("|", "\\|") if in_table else raw
            return f"【{shown}】"

        work = RE_BRACKET.sub(repl, work)
        out.append(RE_HOLDER.sub(lambda m: holders[int(m.group(1))], work))

    cleaned, skip = [], False
    for line in out:
        t = line.strip()
        if t == "### 发言人对照":
            skip = True
            continue
        if skip:
            if not t or t.startswith("|"):
                continue
            skip = False
        cleaned.append(line)

    dest = Path(args.out) if args.out else Path(args.markdown)
    print(f"[OK] 改用原始昵称 {changed[0]} 处，涉及 {len(used)} 人"
          + (f" -> {dest}" if not args.dry_run else " (dry-run)"))
    if not args.dry_run:
        dest.write_text("\n".join(cleaned).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
