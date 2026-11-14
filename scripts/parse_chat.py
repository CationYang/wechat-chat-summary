#!/usr/bin/env python3
"""WeChat chat export -> normalized messages.json.

Supported inputs: .json / .jsonl / .csv / .tsv / .txt / .html / WeChat share export
(wx-share: `·nick` + Chinese date line + content) / pasted text via '-'.
Always run --probe first to confirm the detected format before trusting the parse.
Output records: {id, speaker, timestamp, content, kind, raw}
"""
import argparse
import csv
import html as html_lib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SPEAKER_KEYS = ("from_nickname", "nickname", "sender", "speaker", "talker",
                "name", "display_name", "from", "user", "author", "昵称", "发送人")
TIME_KEYS = ("timestamp", "create_time", "createTime", "msg_time", "send_time",
             "time", "date", "datetime", "ts", "时间")
CONTENT_KEYS = ("content", "strContent", "text", "msg", "message", "body", "value", "内容")
ID_KEYS = ("msg_id", "message_id", "id", "local_id", "localId")

TS_TOKEN = r"\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(?::\d{2})?"
TS_ONLY = r"\d{1,2}:\d{2}(?::\d{2})?"
CN_DATE = r"\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}"

RE_TS_FIRST = re.compile(r"^\s*[\[\(]?\s*(" + TS_TOKEN + r")\s*[\]\)]?\s+(.+?)\s*[:：]\s*(.*)$")
RE_BLOCK_HEAD = re.compile(r"^\s*(.+?)\s+[\(\[]?\s*(" + TS_TOKEN + r")\s*[\)\]]?\s*[:：]?\s*$")
RE_MD_HEAD = re.compile(r"^\s*\*\*(.+?)\*\*\s*[〔\[\(]?\s*(" + TS_ONLY + r")?\s*[〕\]\)]?\s*[:：]?\s*$")
RE_SIMPLE = re.compile(r"^\s*([^:：]{1,32})\s*[:：]\s*(.*)$")
RE_QUOTE = re.compile(r"^\s*>\s?(.*)$")

RE_WX_SPEAKER = re.compile(r"^(\s*)·(?!\[聊天记录\])(.+?)\s*$")
RE_WX_DATE = re.compile(r"^\s*(" + CN_DATE + r")\s*$")
RE_WX_SEPARATOR = re.compile(r"^\s*·\[聊天记录\]\s*$")

MEDIA_MARKS = (
    ("[图片]", "image"), ("[表情]", "sticker"), ("[动画表情]", "sticker"),
    ("[视频号]", "video"), ("[视频]", "video"), ("[文件]", "file"),
    ("[语音]", "voice"), ("[链接]", "link"), ("[聊天记录]", "forward"),
    ("[位置]", "location"), ("[名片]", "card"), ("[转账]", "transfer"),
)
NOISE_KINDS = {"sticker", "image", "video", "file", "card", "location",
               "transfer", "system", "forward", "voice"}

REDACTIONS = (
    (re.compile(r"1[3-9]\d{9}"), "[手机号]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[邮箱]"),
    (re.compile(r"\b\d{17}[\dXx]\b"), "[证件号]"),
)


def decode_bytes(raw):
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8-sig", "utf-8", "gb18030", "utf-16", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def normalize_ts(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1e12:
            v /= 1000.0
        try:
            return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError, OverflowError):
            return str(value)
    s = str(value).strip()
    if not s:
        return ""
    if re.fullmatch(r"\d{10,13}", s):
        return normalize_ts(int(s))
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if m:
        y, mo, d, h, mi, sec = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d} {int(h):02d}:{mi}:{sec or '00'}"
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})", s)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d} {int(h):02d}:{mi}:00"
    return s


def pick(d, keys, default=""):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def kind_of(content):
    c = (content or "").strip()
    for mark, k in MEDIA_MARKS:
        if c.startswith(mark):
            return k
    if c.startswith("[系统]") or "revokemsg" in c:
        return "system"
    return "text"


def norm_record(obj, idx):
    if not isinstance(obj, dict):
        return {"id": idx, "speaker": "未知", "timestamp": "",
                "content": str(obj), "kind": "text", "raw": ""}
    speaker = str(pick(obj, SPEAKER_KEYS, "")).strip() or "未知"
    ts = normalize_ts(pick(obj, TIME_KEYS, ""))
    content = str(pick(obj, CONTENT_KEYS, "")).strip()
    return {"id": pick(obj, ID_KEYS, idx) or idx, "speaker": speaker,
            "timestamp": ts, "content": content, "kind": kind_of(content), "raw": ""}


def parse_json(text):
    data = json.loads(text)
    if isinstance(data, dict):
        for key in ("messages", "data", "records", "list", "items", "chat"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON root is neither a list nor a recognized wrapper object")
    return [norm_record(o, i + 1) for i, o in enumerate(data)]


def parse_jsonl(text):
    rows = [line for line in text.splitlines() if line.strip()]
    return [norm_record(json.loads(line), i + 1) for i, line in enumerate(rows)]


def parse_csv(text, delimiter=None):
    lines = text.splitlines()
    if not lines:
        return []
    lines[0] = lines[0].lstrip("\ufeff")
    if delimiter is None:
        delimiter = "\t" if lines[0].count("\t") > lines[0].count(",") else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    out = []
    for i, row in enumerate(reader, 1):
        clean = {(k or "").strip().lstrip("\ufeff"): v for k, v in row.items()}
        out.append(norm_record(clean, i))
    return out


def html_to_text(text):
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    return html_lib.unescape(text)


def parse_txt(text):
    lines = text.splitlines()
    structured = any(RE_BLOCK_HEAD.match(l) or RE_TS_FIRST.match(l) or RE_MD_HEAD.match(l)
                     for l in lines)
    messages = []
    if structured:
        cur = None
        buf = []

        def flush():
            nonlocal cur, buf
            if cur is not None:
                content = "\n".join(buf).strip()
                cur["content"] = content
                cur["kind"] = kind_of(content)
                cur["raw"] = content
                messages.append(cur)
            cur, buf = None, []

        for line in lines:
            m = RE_TS_FIRST.match(line)
            if m:
                flush()
                cur = {"id": len(messages) + 1, "speaker": m.group(2).strip(),
                       "timestamp": normalize_ts(m.group(1)), "content": "",
                       "kind": "text", "raw": line}
                buf = [m.group(3).strip()] if m.group(3).strip() else []
                continue
            m = RE_BLOCK_HEAD.match(line)
            if m:
                flush()
                cur = {"id": len(messages) + 1, "speaker": m.group(1).strip(),
                       "timestamp": normalize_ts(m.group(2)), "content": "",
                       "kind": "text", "raw": line}
                buf = []
                continue
            m = RE_MD_HEAD.match(line)
            if m:
                flush()
                cur = {"id": len(messages) + 1, "speaker": m.group(1).strip(),
                       "timestamp": m.group(2) or "", "content": "",
                       "kind": "text", "raw": line}
                buf = []
                continue
            if cur is not None:
                q = RE_QUOTE.match(line)
                buf.append(q.group(1) if q else line)
        flush()
    else:
        for i, line in enumerate(lines, 1):
            m = RE_SIMPLE.match(line)
            if m and m.group(2).strip():
                content = m.group(2).strip()
                messages.append({"id": i, "speaker": m.group(1).strip(),
                                 "timestamp": "", "content": content,
                                 "kind": kind_of(content), "raw": line})
            elif messages and line.strip():
                messages[-1]["content"] += "\n" + line.strip()
                messages[-1]["kind"] = kind_of(messages[-1]["content"])
    for i, m in enumerate(messages, 1):
        m["id"] = i
    return messages


def parse_wx_share(text):
    """WeChat share/history export: `·nick` line, Chinese date line, then content lines."""
    lines = text.splitlines()
    messages = []
    base_indent = None
    cur = None
    buf = []

    def flush():
        nonlocal cur, buf
        if cur is not None:
            content = "\n".join(buf).strip()
            cur["content"] = content
            cur["kind"] = kind_of(content)
            cur["raw"] = content
            messages.append(cur)
        cur, buf = None, []

    for line in lines:
        if RE_WX_SEPARATOR.match(line):
            flush()
            continue
        m = RE_WX_SPEAKER.match(line)
        if m:
            indent = len(m.group(1).expandtabs(4))
            if base_indent is None:
                base_indent = indent
            if indent <= base_indent:
                flush()
                cur = {"id": len(messages) + 1,
                       "speaker": html_lib.unescape(m.group(2).strip()),
                       "timestamp": "", "content": "", "kind": "text", "raw": line}
                buf = []
                continue
            # deeper indent: embedded forwarded chat, keep as content of the current message
        d = RE_WX_DATE.match(line)
        if d and cur is not None and not cur["timestamp"]:
            cur["timestamp"] = normalize_ts(d.group(1))
            continue
        if cur is not None:
            buf.append(html_lib.unescape(line.strip()))
    flush()
    for i, m in enumerate(messages, 1):
        m["id"] = i
    return messages


def detect(ext, text):
    if ext in ("json", "jsonl"):
        return ext
    if ext in ("csv", "tsv"):
        return "csv"
    if ext in ("html", "htm"):
        return "html"
    stripped = text.lstrip()
    if stripped.startswith(("[", "{")):
        try:
            json.loads(stripped)
            return "json"
        except ValueError:
            pass
    if re.search(r"^\s*·\[聊天记录\]", text, re.M) and re.search(CN_DATE, text):
        return "wx-share"
    low = text.lower()
    if "<html" in low or "<div" in low or "<body" in low:
        return "html"
    first = text.splitlines()[0] if text.splitlines() else ""
    if ("," in first or "\t" in first) and re.search(
            r"speaker|sender|nickname|content|message|time|timestamp|昵称|内容|时间", first, re.I):
        return "csv"
    return "txt"


def parse(fmt, text):
    if fmt == "wx-share":
        return parse_wx_share(text)
    if fmt == "json":
        return parse_json(text)
    if fmt == "jsonl":
        return parse_jsonl(text)
    if fmt == "csv":
        return parse_csv(text)
    if fmt == "html":
        return parse_txt(html_to_text(text))
    return parse_txt(text)


def probe(fmt, text, messages):
    lines = text.splitlines()
    print(f"detected_format: {fmt}")
    print(f"lines: {len(lines)}")
    print("sample:")
    for line in lines[:8]:
        print("  | " + line[:120])
    print(f"parsed_messages: {len(messages)}")
    for m in messages[:3]:
        print(f"  - {m['speaker']} | {m['timestamp']} | {m['content'][:60]!r}")
    no_ts = sum(1 for m in messages if not m["timestamp"])
    print(f"missing_timestamp: {no_ts}")
    if not messages:
        print("[WARN] 0 messages parsed. Read references/input-formats.md before continuing.")


def stats(messages):
    valid = [m for m in messages if m["kind"] != "system" and m["content"].strip()]
    substantive = [m for m in valid if m["kind"] not in NOISE_KINDS]
    ts = sorted(m["timestamp"] for m in valid if re.match(r"^\d{4}-", m["timestamp"]))
    print(f"total: {len(messages)}  valid: {len(valid)}  substantive: {len(substantive)}  "
          f"excluded: {len(messages) - len(valid)}")
    if ts:
        print(f"range: {ts[0]} ~ {ts[-1]}")
    else:
        print("range: unknown (no parseable timestamps)")
    for i, (name, n) in enumerate(Counter(m["speaker"] for m in valid).most_common(10), 1):
        print(f"{i}. {name}: {n}")
    kinds = Counter(m["kind"] for m in messages)
    print("kinds: " + ", ".join(f"{k}={v}" for k, v in kinds.most_common()))


def write_view(messages, path, min_chars=10, max_chars=240):
    """Chronological, noise-filtered reading view for large batches."""
    kept = []
    for m in messages:
        if m["kind"] in NOISE_KINDS or len(m["content"]) < min_chars:
            continue
        c = " / ".join(x.strip() for x in m["content"].splitlines() if x.strip())
        kept.append((m["timestamp"], m["speaker"], c[:max_chars], m["kind"]))
    kept.sort(key=lambda x: x[0] or "9999")
    out, day = [], None
    for ts, speaker, content, kind in kept:
        d = ts[:10] or "unknown"
        if d != day:
            day = d
            out.append(f"\n## {d}")
        t = ts[11:16] if len(ts) >= 16 else "--:--"
        tag = f" 〔{kind}〕" if kind not in ("text", "link") else ""
        out.append(f"- {t} {speaker}：{content}{tag}")
    Path(path).write_text("\n".join(out).strip() + "\n", encoding="utf-8")
    print(f"[OK] view: {len(kept)} / {len(messages)} messages -> {path}")


def main():
    ap = argparse.ArgumentParser(description="Parse WeChat chat exports into messages.json")
    ap.add_argument("input", help="file path, or '-' to read pasted text from stdin")
    ap.add_argument("--format", default="auto",
                    choices=("auto", "json", "jsonl", "csv", "txt", "html", "wx-share"))
    ap.add_argument("--out", default="", help="write normalized JSON to this path")
    ap.add_argument("--probe", action="store_true", help="inspect format/sample only")
    ap.add_argument("--stats", action="store_true", help="print mechanical counts")
    ap.add_argument("--view", default="", help="write a chronological noise-filtered view")
    ap.add_argument("--min-chars", type=int, default=10, help="min content length in --view")
    ap.add_argument("--view-chars", type=int, default=240, help="max chars per line in --view")
    ap.add_argument("--since", default="", help="inclusive YYYY-MM-DD")
    ap.add_argument("--until", default="", help="inclusive YYYY-MM-DD")
    ap.add_argument("--self-name", default="", help="normalize the user's own speaker label")
    ap.add_argument("--redact", action="store_true", help="mask phone/email/ID numbers")
    args = ap.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        ext = "txt"
    else:
        p = Path(args.input)
        if not p.exists():
            print(f"[ERR] file not found: {p}")
            return 2
        text = decode_bytes(p.read_bytes())
        ext = p.suffix.lower().lstrip(".")

    fmt = detect(ext, text) if args.format == "auto" else args.format
    try:
        messages = parse(fmt, text)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[ERR] parse failed ({fmt}): {exc}")
        return 2

    if args.probe:
        probe(fmt, text, messages)
        return 0

    if args.since or args.until:
        def in_range(m):
            t = m["timestamp"][:10]
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", t):
                return True
            if args.since and t < args.since:
                return False
            if args.until and t > args.until:
                return False
            return True
        dropped = len(messages)
        messages = [m for m in messages if in_range(m)]
        print(f"date filter: kept {len(messages)} / {dropped}")

    for m in messages:
        if args.self_name and m["speaker"] in ("我", "自己", "self", "me"):
            m["speaker"] = args.self_name
        if args.redact:
            for pat, repl in REDACTIONS:
                m["content"] = pat.sub(repl, m["content"])
            m["raw"] = m["content"]

    if args.stats:
        stats(messages)
    if args.view:
        write_view(messages, args.view, args.min_chars, args.view_chars)

    if args.out:
        Path(args.out).write_text(json.dumps(messages, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"[OK] wrote {len(messages)} messages -> {args.out}")
    elif not args.stats and not args.view:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
