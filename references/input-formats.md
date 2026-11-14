# Input formats and parser rules

Load this file when `--probe` returns 0 messages, when speakers/timestamps look wrong, or when a
new export tool shows up. Do not load it for a routine run.

## Detection order

`parse_chat.py` detects format in this order: explicit `--format` → file extension → JSON parse
attempt → HTML tag check → CSV header heuristic → plain text. Run `--probe` first; it prints the
detected format, eight sample lines, the parsed count, and three sample records.

```bash
PY="python3"
"$PY" scripts/parse_chat.py "<input>" --probe
```

A correct probe has: `parsed_messages` close to the number of chat bubbles, speakers that are real
nicknames, and timestamps in `YYYY-MM-DD HH:MM:SS`. Any of these failing means the format needs a
new rule.

## Supported shapes

| Shape | Example line | Notes |
|-------|--------------|-------|
| Timestamp-first | `[2026-11-11 21:10:35] 张三: 内容` | Brackets optional; `/` date separators accepted |
| Block head (WeChat PC copy) | `张三 2026-11-11 21:10:35` followed by content lines | Content accumulates until the next head |
| Markdown export | `**张三** 〔21:10:35〕` followed by content | Time-only stamp kept as-is |
| Simple | `张三: 内容` | Fallback only when no timestamped head exists |
| JSON | `[{"from_nickname":"张三","timestamp":"...","content":"..."}]` | Also accepts `{messages:[...]}` wrappers and `.jsonl` |
| CSV / TSV | header containing speaker/time/content columns | Chinese headers `昵称/时间/内容` accepted |
| HTML | WeChatMsg / 留痕 export | Tags stripped, `<br>` and block ends become newlines, entities unescaped |
| WeChat share export | `·昵称` line, `2026年11月7日 10:37` line, then content lines | Auto-detected as `wx-share`; nested forwarded `[聊天记录]` blocks stay inside the parent message |

Field aliases live in the `SPEAKER_KEYS` / `TIME_KEYS` / `CONTENT_KEYS` tuples at the top of
`parse_chat.py`. Add new aliases there rather than writing a new parser.

## WeChat share export (wx-share)

Detected when the file contains a `·[聊天记录]` separator and Chinese date lines such as
`2026年11月7日 10:37`. Shape: one `·nickname` line, one Chinese date line, then one or more
content lines, with a blank line between messages. Verified on a large multi-week export:
every message parsed with a timestamp, none missing.

Rules specific to this shape:

- Speaker lines are matched only at the shallowest indentation. Deeper-indented `·nickname`
  lines belong to a forwarded `[聊天记录]` block and stay inside the parent message's content.
- `·[聊天记录]` at top level is a section separator, not a message. Nested `[聊天记录]` (without
  the leading `·`) is content.
- HTML entities in nicknames and content (`&amp;` → `&`) are unescaped.
- Chinese dates normalize to `YYYY-MM-DD HH:MM:SS` (seconds always `00`).
- `[动画表情]` / `[视频号]` / `[聊天记录]` are tagged sticker / video / forward.

Regression sample: [assets/sample-wx-share.txt](../assets/sample-wx-share.txt).

## Adding a new format

1. Save 10–20 real lines (redacted) to `assets/sample-<tool>.txt`.
2. Add one head regex near `RE_TS_FIRST` and one branch in `parse_txt()`.
3. Add the shape to the table above and the alias to the tuples.
4. Run `--probe` on the sample and on `assets/sample-chat.txt`; confirm the old sample's count is
   unchanged (regression).
5. Only then run the full export.

Do not special-case a single conversation. The rule must generalize to the tool's output shape.

## Known traps

- **Cue-based transcripts are not chat turns.** VTT / SRT / per-utterance ASR JSON split one
  message into many cues. They are out of scope; use a meeting-transcript skill instead.
- **Continuous lines under one head** belong to that speaker. Do not create a message per line.
- **`昵称: 内容` inside message text** can be mistaken for a head when no timestamped heads exist.
  Prefer exporting with timestamps; if unavailable, verify the probe sample carefully.
- **Media bubbles** arrive as `[图片]`, `[语音]`, `[文件]`, `[链接] <title>`. Preserve the text
  verbatim; never describe unseen images. `[链接]` titles are information — keep them.
- **System / revoked messages** are tagged `kind: system` and excluded from counts. Do not quote
  them as user statements.
- **Unix timestamps** in seconds or milliseconds are normalized automatically.
- **BOM and legacy encodings** (UTF-8 BOM, GB18030, UTF-16) are auto-detected. A UTF-8 BOM on a
  CSV header is stripped.
- **Missing timestamps**: `range: unknown` is the honest output. Never infer a date from the
  filename, file mtime, or chat content.

## Date filtering

`--since` / `--until` are inclusive `YYYY-MM-DD` filters applied to normalized timestamps. Records
without a parseable date are kept (not silently dropped). Re-run `--stats` after filtering so the
note's counts describe exactly the retained set.
