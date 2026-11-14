#!/usr/bin/env python3
"""Verify every 「quoted sentence」 in the generated Markdown exists verbatim in messages.json.

Also verifies the speaker on excerpt lines of the form:
  - 「原话」 — 【微信原始昵称】 〔MM-DD HH:MM〕
The bracketed name is the raw WeChat nickname and must match the source speaker exactly.
A legacy 发言人对照 table is still honoured for notes produced before the naming rule changed.
Exit code 1 means at least one quote could not be traced to the source.
"""
import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RE_QUOTE = re.compile(r"「([^」]+)」")
RE_EXCERPT = re.compile(r"^\s*[-*]?\s*「(.+?)」\s*[—–-]+\s*([^〔〕]+?)\s*(?:〔([^〕]+)〕)?\s*$")
RE_ELLIPSIS = re.compile(r"…+|\.\.\.")
RE_BRACKET = re.compile(r"^【(.+?)】$")
RE_ROSTER_ROW = re.compile(r"^\|\s*【(.+?)】\s*\|\s*(.+?)\s*\|\s*$")


def load_messages(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("messages", [])
    return data


def load_aliases(md_text):
    aliases, in_roster = {}, False
    for line in md_text.splitlines():
        t = line.strip()
        if t == "### 发言人对照":
            in_roster = True
            continue
        if in_roster:
            if t.startswith("## "):
                break
            m = RE_ROSTER_ROW.match(t)
            if m:
                aliases.setdefault(m.group(1).strip(), []).append(
                    m.group(2).strip().replace("\\|", "|"))
    return aliases


def fragments(quote):
    parts = [p.strip() for p in RE_ELLIPSIS.split(quote) if p.strip()]
    return parts or [quote.strip()]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def speaker_match(speaker, who, aliases):
    raw = speaker.strip()
    m = RE_BRACKET.match(raw)
    name = m.group(1).strip().replace("\\|", "|") if m else raw
    if norm(name) == norm(who):
        return True
    if name in aliases:
        return any(norm(who) == norm(r) for r in aliases[name])
    base = re.sub(r"[（(].*$", "", norm(who))
    return bool(base) and norm(name) == base


def main():
    ap = argparse.ArgumentParser(description="Audit quotes against the source messages")
    ap.add_argument("markdown", help="generated .md file")
    ap.add_argument("messages", help="messages.json from parse_chat.py")
    args = ap.parse_args()

    md = Path(args.markdown).read_text(encoding="utf-8")
    msgs = load_messages(args.messages)
    aliases = load_aliases(md)
    blob = [(norm(m.get("content", "")), norm(m.get("speaker", ""))) for m in msgs]

    quotes = []
    for lineno, line in enumerate(md.splitlines(), 1):
        if not RE_QUOTE.search(line):
            continue
        ex = RE_EXCERPT.match(line)
        speaker = ex.group(2).strip() if ex else ""
        for q in RE_QUOTE.findall(line):
            quotes.append((lineno, q, speaker))

    ok = fail = 0
    for lineno, quote, speaker in quotes:
        frags = fragments(quote)
        matched = []
        for frag in frags:
            nf = norm(frag)
            hits = [1 for content, who in blob
                    if nf and nf in content
                    and (not speaker or speaker_match(speaker, who, aliases))]
            matched.append(bool(hits))
        if all(matched):
            ok += 1
            print(f"[OK] L{lineno} {quote[:48]}")
        else:
            fail += 1
            missing = [f for f, good in zip(frags, matched) if not good]
            print(f"[FAIL] L{lineno} {quote[:48]} | missing: {missing}")

    print(f"归因校验：共 {len(quotes)} 处引用，通过 {ok} 处，未匹配 {fail} 处")
    if not quotes:
        print("[WARN] no quotes found - confirm the note actually cites the source")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
