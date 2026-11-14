---
name: wechat-chat-distill
description: 微信聊天记录提炼为 Obsidian 结构化 Markdown 笔记，支持三种整理模板：knowledge 干货学习（主题梳理/结论共识/事实数据/方法案例）、decision 工作项目（决策/待办/未闭环）、crm 客户跟进（客户信息/需求/异议/报价/下一步）。This skill should be used when the user provides a WeChat chat export (.txt/.csv/.json/.jsonl/.html) or pasted chat text and asks to 提炼、总结、沉淀、整理、梳理 微信聊天记录、群聊记录、单聊记录 into a structured note. Also triggers on 「把这段聊天记到 Obsidian」、「这段群聊有什么结论」、「从聊天记录里提取待办」、「提炼成干货笔记」、「整理客户对话」、「增量提炼上次之后的聊天」、「提炼微信聊天」. Requires no wx-cli, no WeChat database decryption, and no network access; all processing stays local. Adapted from baoyu-wechat-summary.
agent_created: true
---

# 微信聊天记录提炼

## Overview

Convert a WeChat chat export or pasted chat text into one normalized `messages.json`, then write a
structured Obsidian Markdown note. The workflow keeps the three-pass method and mandatory
attribution audit from `baoyu-wechat-summary`, but replaces its `wx-cli` input layer (unavailable on
Windows) and its group-digest output with profile-driven knowledge notes.

Three profiles share the same parsing, evidence, statistics, naming and incremental layers:

| id | 中文名 | 产出 |
|----|--------|------|
| `knowledge` | 干货学习 | 主题脉络、结论共识、事实数据、方法案例 |
| `decision` | 工作 / 项目 | 决策、待办、未闭环（默认与兼容格式） |
| `crm` | 客户跟进 | 客户信息、需求、异议、报价、下一步 |

`knowledge` is a **summary** template. Its job is to organize what was said, not to produce 选题,
titles or writing angles. Turning distilled material into article topics is a separate workflow.

See [references/profiles.md](references/profiles.md) for selection rules, mixed conversations and
degraded cases.

## Principles (hard constraints)

1. Process locally. Never upload chat records, never call a web service on their content.
2. Treat `messages.json` as the single source of truth for the run. Never write the note from
   conversation memory.
3. Verify every direct quote against `messages.json` with `scripts/check_quotes.py`. Fix or delete
   any quote that fails. Never ship an invented quote.
4. Mark inference explicitly as `〔未证实〕`. Do not state an inferred decision as a fact.
5. Compute counts mechanically with `scripts/parse_chat.py --stats`. Never eyeball message totals
   or leaderboards.
6. Preserve names, product names, and URLs verbatim. Never infer sleep habits, time zones, or
   private attributes from timestamps.
7. Keep media placeholders opaque (`[图片]`, `[语音]`). Do not invent their content.
8. Run `scripts/check_note.py` as the final gate. It validates frontmatter, section order, quote
   attribution, message-count consistency, and status enum values for the chosen profile.

## Preferences (EXTEND.md)

Read `EXTEND.md` in the skill directory. Missing file or missing key means «use the built-in
default»; do not block the run with a first-time setup wizard.

| Key | Default | Purpose |
|-----|---------|---------|
| `vault` | `<your-vault>` | Obsidian vault root (your Obsidian vault) |
| `out_dir` | `{vault}/微信提炼` | Where notes and `_history.json` are written |
| `self_name` | (empty) | Normalize the user's own speaker label in the note |
| `default_range` | `7d` | Range when the user omits a time range and no incremental anchor exists |
| `default_profile` | `auto` | `auto` / `knowledge` / `decision` / `crm` |
| `redact` | `false` | Mask phone numbers / emails / ID numbers before parsing |
| `date_prefix` | `true` | Prefix filenames with `YYYY-MM-DD` for chronological sorting |

`{vault}` in `out_dir` expands to the `vault` value at run time. An absolute `out_dir` overrides
it. See [references/preferences.md](references/preferences.md) for alternate vaults and
first-time customization.

## Workflow

### Step 1 — Parse the request

Extract: chat/session name, time range, **profile**, output target, incremental flag, redaction flag.

**Profile resolution**: explicit `--profile` or user wording wins (`干货/学习/梳理/总结/复盘` →
`knowledge`, `工作/项目/待办` → `decision`, `客户/跟进/报价/询价` → `crm`). Otherwise use
`default_profile`; when it is `auto`, run `scripts/detect_profile.py <messages.json>` (gated
signal counts; see [references/profiles.md](references/profiles.md)) and report the chosen profile
**and its signal counts** so the user can override. `auto` selects one main profile; more than one
note per conversation requires an explicit request. Never infer a profile from the filename alone.

Convert relative ranges to absolute `--since` / `--until` pairs using the local date. Interpret
`今天` → 1 day, `最近 3 天` → 3 days, `这周` / `最近 7 天` → 7 days, `最近一个月` → 30 days,
`从上次开始` / `继续` / `接着上次` → incremental mode. When no range is given, use incremental
mode if `_history.json` has an anchor for this profile, otherwise `default_range`.

### Step 2 — Locate the input

Work down this ladder and stop at the first hit:

1. Explicit path given by the user.
2. A file inside the current workspace whose name contains `chat` / `wechat` / 聊天 / 微信.
3. Ask the user to paste the text; save it to a temporary `.txt` and continue.

Do not sweep Desktop, Downloads, or Documents recursively. Do not attempt WeChat database
decryption or screenshot OCR as a default path.

### Step 3 — Probe the format (mandatory)

```bash
PY="python3"
"$PY" SKILL_DIR/scripts/parse_chat.py "<input>" --probe
```

Confirm `detected_format`, the sample lines, and `parsed_messages`. If the count is 0 or speakers
look wrong, read [references/input-formats.md](references/input-formats.md) and add a rule before
continuing. Never silently accept a mis-parse.

### Step 4 — Normalize to messages.json

```bash
"$PY" SKILL_DIR/scripts/parse_chat.py "<input>" \
  --out "<TMPDIR>/messages.json" --stats --view "<TMPDIR>/view.md" \
  --since YYYY-MM-DD --until YYYY-MM-DD \
  --self-name "<self_name>" [--redact]
```

`--view` writes a chronological, noise-filtered reading view (media placeholders, short
agreements, and duplicate forwards removed). For batches > 500 messages, read `view.md` in slices
for Round 1 instead of loading `messages.json` wholesale. Use `--min-chars` / `--view-chars` to
tighten it.

`--stats` output is the authoritative source for message totals, coverage range, and the top-10
speaker list in the appendix.

**Incremental mode**: read `out_dir/_history.json`, take
`profiles[profile].last_message_time` (fall back to the legacy `last_digest` when `profiles` is
absent), drop every message whose timestamp is `<=` that value, and rewrite `messages.json` with
the filtered set. If zero remain, report «上次提炼后没有新消息，已跳过» and exit. Compare by date
semantics, not plain string comparison, across a year boundary.

**Large batches**: with `--view`, one note is acceptable up to ~1500 messages / one month. Above
that, or when topics span unrelated months, split into 3-day slices, distill each, then merge.
For a long mixed thread, apply the mixed-conversation rule in `profiles.md` instead of splitting.

### Step 5 — Distill in three passes

#### Round 1 — Build the skeleton

Read `messages.json` in slices (offset/limit or `jq`), not all at once for large files. Record as
internal working notes (never written into the final note). Tag each candidate with the profile
section it will feed:

```
== 话题清单（共 N 条消息）==
1. [HH:MM-HH:MM] 话题名（参与者：A, B）— 一句话概括（锚点：id=12 张三:"原话片段" → id=14 李四:"回应"）
== 候选：主题脉络 / 结论共识 / 事实数据 / 方法案例 ==   (knowledge)
== 候选：决策 / 待办 / 未闭环 ==            (decision)
== 候选：需求 / 异议 / 报价 / 下一步 ==      (crm)
== 统计 ==
（来自 --stats，机械计算）
```

Topic-switch signals: > 30 min gap, participant change, subject jump. Two or more participants
or substantive content qualifies as a topic; pure emoji banter does not. Pin each key message's
anchor id and a verbatim quote fragment at this stage to prevent misattribution later.

#### Round 2 — Write the note

Read [references/output-format.md](references/output-format.md),
[references/profiles.md](references/profiles.md) and the selected profile's template before
drafting. Fill that profile's fixed section list. Write the body sections first, then `概览`, so
the overview matches what was actually written.

Templates: `assets/template-knowledge.md`, `assets/template.md` (decision),
`assets/template-crm.md`. For `knowledge`, organize the discussion topic by topic, then state
conclusions, evidence and methods. Never add 选题 / 标题 / 写作建议. Mixed conversations use one
optional `（附）` section per `profiles.md`; degraded cases (接龙 / 闲聊 / 判不准) use the minimal
four-section shape described there. Never silently drop the other kind of content.

Use the **raw WeChat nickname** for every speaker mention, wrapped as `【原始昵称】`, in prose,
tables, checkboxes and excerpt lines. No shortened 主名 and no `### 发言人对照` table. Escape `|`
as `\|` inside table cells. Never alter text inside `「...」`. See
[references/output-format.md](references/output-format.md); run `scripts/format_names.py
<note.md> <messages.json>` to convert a note produced under the old naming rule.

#### Round 3 — Validation (mandatory)

```bash
"$PY" SKILL_DIR/scripts/check_quotes.py "<generated.md>" "<TMPDIR>/messages.json"
"$PY" SKILL_DIR/scripts/check_note.py "<generated.md>" "<TMPDIR>/messages.json"
```

`check_quotes.py` extracts every `「...」` quote, splits on `…` / `...` into fragments, and checks
each fragment against the source content, including the speaker on excerpt lines. A `[FAIL]`
means paraphrase drift, an invented quote, or wrong attribution. Fix in place and re-run until
the verdict reads `未匹配 0 处`.

`check_note.py` then validates frontmatter fields, section order for the profile, message-count
consistency, and status enum values. Fix until it prints `笔记校验：全部通过`. Record both verdict
lines in the completion report.

### Step 6 — Save

Filename (date-prefixed by user preference):

- Single day: `YYYY-MM-DD微信提炼 - {会话名}.md`
- Date range: `YYYY-MM-DD_YYYY-MM-DD微信提炼 - {会话名}.md`
- Two profiles requested in one run: append ` - {profile}` before `.md`

Write to `out_dir`. Overwrite only when both the range **and** the profile match. Then update
`out_dir/_history.json` under `profiles[profile]` with `last_message_time`, `message_count`,
`date_range`, and `file`; mirror the same record into the legacy `last_digest` key. Never let a
`knowledge` run overwrite the `decision` anchor.

### Step 7 — Deliver

Open the note with `present_files`. Report: file path, **profile used**, message count and
coverage range, both verdict lines, and the count of open loops / todos / 结论 depending on
profile. Do not restate the whole note in chat.

## Resources (load on demand)

| File | When to load |
|------|--------------|
| [references/profiles.md](references/profiles.md) | Step 1 (selection), Round 2 (mixed / degraded cases) |
| [references/input-formats.md](references/input-formats.md) | `--probe` shows 0 messages, an unknown export shape, or a new source tool |
| [references/output-format.md](references/output-format.md) | Round 2, before drafting the note |
| [references/preferences.md](references/preferences.md) | Editing EXTEND.md or changing the vault |
| `assets/template.md` / `template-knowledge.md` / `template-crm.md` | Round 2, copy the matching skeleton |
| `scripts/parse_chat.py` | Steps 3–4; execute, do not read into context |
| `scripts/format_names.py` | Round 2, use raw WeChat nicknames and remove legacy 发言人对照 |
| `scripts/check_quotes.py` / `check_note.py` | Round 3; execute, do not read into context |

## Completion checklist

- [ ] `--probe` ran and the detected format was confirmed
- [ ] Profile selected and stated in the report
- [ ] `messages.json` written; `--stats` output captured
- [ ] All note numbers come from `--stats`, not estimation
- [ ] `check_quotes.py` exits 0 with `未匹配 0 处`
- [ ] `check_note.py` exits 0 with `笔记校验：全部通过`
- [ ] `knowledge` note contains no 选题 / 标题 / 写作建议
- [ ] Inferences marked `〔未证实〕`; media placeholders left opaque
- [ ] `_history.json` updated under `profiles[profile]`
- [ ] Note delivered via `present_files`

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `parsed_messages: 0` | Read `references/input-formats.md`; add a head regex to `parse_chat.py`, then re-run `--probe` |
| Garbled Chinese | `decode_bytes` tries UTF-8/GB18030/UTF-16; if still broken, convert the file to UTF-8 manually |
| Many `[FAIL]` in audit | Check quote style (must be `「」`), ellipsis style (`…`), and speaker labels (exact nickname, parenthetical remark may be dropped); fix the note, not the checker |
| `range: unknown` | The export has no timestamps; leave the coverage range blank, never guess |
| Script edited | Re-run on both bundled samples (`assets/sample-chat.txt` → 8 messages, `assets/sample-wx-share.txt` → 6) and confirm counts are unchanged |
| Large export (> 500 messages) | Use `--view` to generate a chronological reading view; read it in slices for Round 1 |
| Profile 判不准 / 接龙刷屏 | 用 `decision` 兜底或 `profiles.md` 的降级四节；显式 `--profile` 覆盖 |
| `check_note.py` section mismatch | Omit empty sections but never renumber the rest; optional sections must be labelled `（附）` |
| knowledge 里出现选题 | 删掉；该模板只梳理内容，选题属另一条工作流 |

## Differences from baoyu-wechat-summary

| Dimension | baoyu-wechat-summary | This skill |
|-----------|---------------------|------------|
| Input | `wx-cli` reading the macOS WeChat data dir | Local export file / pasted text, Windows-compatible |
| Output | 群聊精华简报 + 毒舌版 + 群友画像 | Three profile-driven Obsidian notes with frontmatter |
| Focus | Entertainment, portraits, leaderboard | Evidence-backed summaries, decisions, or customer follow-up |
| Cross-run state | history.json + profiles/ + memory.md | `_history.json` with per-profile incremental anchors |
| Privacy | Per-group profiles of real people | No profiles; optional redaction; local-only |
| Setup | BLOCKING EXTEND.md first-time wizard | Defaults work out of the box |
