# Output profiles

Three profiles cover daily use. The profile decides **only** the section list and the template;
the parsing, attribution, statistics, naming and incremental layers are shared. Load this file in
Step 1 (profile selection) and Round 2 (template lookup).

| id | 中文名 | 拿走什么 | 典型场景 | 模板 |
|----|--------|----------|----------|------|
| `knowledge` | 干货学习 | 主题脉络、结论共识、事实数据、方法案例 | 行业学习群、课程群、长文讨论、知识复盘 | [assets/template-knowledge.md](../assets/template-knowledge.md) |
| `decision` | 工作 / 项目 | 决策、待办、未闭环 | 工作群、项目群、会后复盘、共创任务 | [assets/template.md](../assets/template.md) |
| `crm` | 客户跟进 | 画像、需求、异议、报价、下一步 | 客户 1v1、询价、销售对话、售后 | [assets/template-crm.md](../assets/template-crm.md) |

`decision` is the fallback and the legacy format (notes without a `profile` frontmatter key are
treated as `decision`).

**`knowledge` is a summary template, not a content-production template.** Its job is to organize
what was said: topic by topic, then conclusions, evidence, methods. It never produces 选题,
titles, writing angles, or "可用于什么内容" suggestions. Turning distilled material into article
topics belongs to a separate workflow.

## Section lists

| profile | fixed sections, in order |
|---------|--------------------------|
| `decision` | 概览 → 关键要点 → 决策与待办 → 未闭环 / 待确认 → 原话摘录 → 附录 |
| `knowledge` | 概览 → 主题梳理 → 结论与共识 → 事实与数据 → 方法与案例 → 原话摘录 → 附录 |
| `crm` | 概览 → 客户信息 → 需求与痛点 → 异议与回应 → 报价与承诺 → 下一步动作 → 原话摘录 → 附录 |

Omit a section only when genuinely empty. Never renumber the remaining sections. `概览` and `附录`
are mandatory in every profile. The last line of `附录` is fixed:
`本地提炼，未外发；引语已通过 check_quotes.py 校验。`

## Selecting a profile

Explicit `--profile` / user request always wins. Otherwise use `default_profile` from EXTEND.md.
When it is `auto`, run `scripts/detect_profile.py <messages.json>`. It is a **single-label**
classifier, not a three-way split of the same conversation:

| Step | Rule |
|------|------|
| 1 | `crm` hard gate: ≤ 3 active speakers **and** ≥ 3 customer-signal messages. A 99-person group is never `crm`, even if 报价/客户 appears often. |
| 2 | Count messages matching the cue lists below. |
| 3 | Pick the denser of `decision` / `knowledge`. Prefer `decision` when counts are close (smaller ≥ 80% of larger) — missing a decision costs more than missing a summary. |
| 4 | No cue at all → `decision` (conservative fallback). |

| Cue set | Keywords |
|---------|----------|
| `crm` | 报价 / 合同 / 客户 / 能不能便宜 / 什么时候能交 / 售后 |
| `decision` | 定了 / 负责人 / 截止 / 排期 / 待办 / 复盘 / 交付 / 谁来做 |
| `knowledge` | 分享 / 报告 / 数据 / 趋势 / 怎么看 / 学到了 / 教程 / 实测 / 为什么 |

Reference run on a real group export: `crm=65` (excluded, many speakers), `decision=26`,
`knowledge=88` → `knowledge`. The earlier first-match-wins rule misclassified it as `decision`.

`auto` is a suggestion, not a silent decision: report the chosen profile **and its signal counts**
so the user can override. To output more than one profile for one conversation, the user must ask
explicitly; the skill then reuses the same `messages.json` with a separate audit and anchor per
note. Never guess a profile from the filename alone.

## Mixed conversations

A real group often contains both learning material and project decisions (one verified export
did). Do **not** generate two notes by default. Rules:

1. Pick one main profile from the cues above. Its section list is the skeleton.
2. If the other kind of content has ≥ 3 substantive messages, append **one** optional section:
   - `knowledge` → optional `待办与共创` (decisions/todos only, no full decision table)
   - `decision` → optional `行业要点` (facts/data only, no 结论 section)
   - `crm` → optional `内部备注` (never mix internal discussion into customer-facing fields)
3. Optional sections go after the main body and before `原话摘录`. They are not numbered and must
   be labelled `（附）`, e.g. `## （附）行业要点`.
4. Only when the user explicitly asks for two outputs, generate two notes from the same
   `messages.json`, each with its own quote audit and its own `_history.json` profile anchor.

## Degraded cases (no fourth template)

- 接龙 / 报名 / 通知 / 纯刷屏: if repeated content exceeds ~30% and there is no substantive
  viewpoint, decision, or customer signal, use a **minimal four-section note**:
  `概览 → 要点 → 统计名单 → 附录`. Run `--dedupe` style filtering in the view before drafting.
  Do not force decisions or todos into it.
- 闲聊 / 家庭群 / 判不准: same minimal shape, `要点` limited to 3–5 bullets.
- Both cases still set `profile: decision` in frontmatter and still run the quote audit.

## Shared invariants (all profiles)

- `messages.json` is the single source of truth; never write from conversation memory.
- Every `「」` quote uses `- 「原话」 — 【微信原始昵称】 〔MM-DD HH:MM〕` and passes `check_quotes.py`.
- Inferences carry `〔未证实〕`. Status enum: `已定 / 待确认 / 已完成 / 部分完成 / 〔未证实〕`.
- All counts come from `parse_chat.py --stats`; media placeholders stay opaque.
- Every speaker mention uses the raw WeChat nickname in `【】`. No shortened 主名, no 发言人对照
  table. See `references/output-format.md`. Quoted text inside `「...」` is never altered.
- Frontmatter fields: `title / source / created / range / message_count / tags`, plus `profile`.
- Filename, `out_dir`, `_history.json`, and the local-only rule are unchanged.

## Incremental state is per profile

`_history.json` holds one anchor per profile under `profiles`, so a `knowledge` run does not
overwrite the `decision` anchor:

```json
{
  "group_name": "会话名",
  "profiles": {
    "decision": { "file": "...", "date_range": "...", "message_count": 1234,
                  "last_message_time": "2026-11-09 12:43:00" },
    "knowledge": { "file": "...", "date_range": "...", "message_count": 1234,
                   "last_message_time": "2026-11-09 12:43:00" }
  },
  "last_digest": { "...": "legacy single-record mirror, kept for backward compatibility" }
}
```

Read `profiles[profile].last_message_time`. Fall back to the legacy `last_digest` when `profiles`
is absent. Write both when updating.

## Validation

Run `scripts/check_note.py <note.md> <messages.json>` for the final pass. It checks frontmatter,
section order, quote attribution (via `check_quotes.py`), message-count consistency, status
enum values, and raw-nickname `【】` formatting on excerpt lines, using the note's `profile` key.
