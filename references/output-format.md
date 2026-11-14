# Output format — Obsidian note

Load this file in Round 2 before drafting. Copy [assets/template.md](../assets/template.md) as the
skeleton and fill it in place. The section order is fixed.

## Section order

1. YAML frontmatter — `title`, `source`, `created`, `range`, `message_count`, `tags`.
2. `# {会话名} · {日期}` — H1.
3. `## 一、概览` — 2–4 sentences of plain prose, written last.
4. `## 二、关键要点` — 3–6 bullets. Each bullet names a topic, not a generic label.
5. `## 三、决策与待办` — a decision table plus a todo checkbox list.
6. `## 四、未闭环 / 待确认` — questions that were asked but never answered.
7. `## 五、原话摘录` — verbatim quotes with strict line format.
8. `## 六、附录` — mechanical counts, coverage, top-10 speakers, generation note.

Omit a section only when it is genuinely empty (e.g. no open loops). Never pad one with invented
content. Keep section numbers even when a section is omitted so the layout stays stable.

## Speaker names (原始昵称)

Every mention of a chat participant in prose, tables, checkboxes, and excerpt lines uses the
**raw WeChat nickname verbatim**, wrapped in full-width brackets: `【Zhang San (busy)】`,
`【Li Si | AI Marketing】`. Rules:

- Never shorten, translate, or normalize a nickname. No 主名 derivation, no alias mapping, and
  **no `### 发言人对照` table** — the name in the note is already the name in the export.
- Never change text inside `「...」` (verbatim quotes). Never wrap session names or product names.
- Excerpt lines use `- 「原话」 — 【微信原始昵称】 〔MM-DD HH:MM〕`.
- Nicknames containing `|` must be escaped as `\|` only inside markdown table cells; list lines
  keep the raw form.
- `check_quotes.py` matches the bracketed name exactly against `messages.json` speakers.
- To convert a note produced under the old 主名 rule: `scripts/format_names.py <note.md>
  <messages.json>`. It replaces short names with raw nicknames, removes the 发言人对照 table,
  protects frontmatter and `「...」`, and is idempotent.

## Writing rules

- Use standard Markdown (this is an Obsidian note, unlike the plain-text digest of the source skill).
- Name the speaker on first mention in a thread. Keep nicknames verbatim; never abbreviate.
- Use `「」` for direct quotes. Single quotes for nested quotes.
- Preserve product names, versions, and full URLs verbatim.
- Merge a multi-person debate into one bullet; do not emit one line per message.
- Cut pure noise: lone emoji, `好的` / `收到` / `哈哈哈` without follow-on, duplicate forwards.
- Keep vivid expressions and signature moments — they are the retrievable memory.
- Every claim must be supported by a message in `messages.json`. Mark any inference `〔未证实〕`.
- Never infer sleep, time zone, location, health, or private attributes from timestamps.
- Do not infer visual content from `[图片]` / `[语音]` placeholders.

## Decision and todo rules

| Field | Rule |
|-------|------|
| 决策 | Only when a choice was stated out loud. Vague «we should probably» is not a decision. |
| 待办 | Must have an owner and a next step. «回头看看» without an owner goes to 未闭环 instead. |
| 状态 | `已定` / `待确认` / `已完成` / `部分完成` / `〔未证实〕`. `已完成` only when the source says it was done; `部分完成` when something was delivered but still needs verification. Do not upgrade soft language into commitment. |
| 时限 | Copy the stated time verbatim (`周五前`, `下个月`). Never invent a date. |

Todo checkboxes use `- [ ]`. Mark `- [x]` only when the source explicitly says it was completed.

## Quote and attribution rules

Excerpt lines must use this exact shape so `check_quotes.py` can verify both quote and speaker:

```
- 「原话片段」 — 张三 〔11-11 21:10〕
```

- Copy the quote verbatim, character for character, including disfluencies.
- When shortening, cut with `…` on both sides of the removed span. The checker treats each side of
  an ellipsis as a separate fragment and requires both in the source.
- Never smooth over a join. Never paraphrase inside `「」`.
- If the speaker cannot be confirmed from the source, write `说话人待核` and put the statement in
  未闭环 instead of asserting attribution.
- Round 3 audit: run `check_quotes.py`, fix every `[FAIL]`, re-run until `未匹配 0 处`.

## Redaction

When `redact: true`, `parse_chat.py` masks phone numbers, emails, and ID numbers in the normalized
content before the note is written. Apply the same masking to any quote copied into the note;
otherwise the audit will fail. Do not redact nicknames by default — traceability depends on them.

## Appendix rules

- `消息数` / `覆盖区间` / 发言统计 come from `--stats`, never from estimation.
- Exclude `kind: system` and empty messages from counts.
- Incremental runs must state the precise coverage window (`MM-DD HH:MM ~ MM-DD HH:MM`), because
  day-granular ranges share a boundary day with the previous note.
- End with: `本地提炼，未外发；引语已通过 check_quotes.py 校验。`

## Self-check before saving

1. Six sections in the fixed order, with frontmatter?
2. Overview written after the body and consistent with it?
3. Every number traceable to `--stats`?
4. Every `「」` quote in the exact excerpt format?
5. Every inference marked `〔未证实〕`?
6. No invented decisions, owners, deadlines, or image descriptions?
7. `check_quotes.py` exits 0?
8. Filename date-prefixed, `_history.json` updated?
