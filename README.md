# wechat-chat-summary

Turn WeChat chat exports into structured, evidence-backed Obsidian Markdown notes.

**English** | [简体中文](./README.zh-CN.md)

## Highlights

- Three output profiles: `knowledge` (topic-by-topic summary), `decision` (decisions, todos, open loops), `crm` (customer follow-up).
- Every direct quote is verified against the source messages. Invented quotes fail the audit.
- All counts come from a parser, not from estimation.
- Reads `.txt`, `.csv`, `.json`, `.jsonl`, `.html` and WeChat share exports.
- Incremental runs with a separate anchor per profile.
- Local only. No database access, no network calls, no WeChat decryption.

## Scope and disclaimer

This is an **Agent Skill**: a folder of instructions and scripts that an AI agent loads to process
files you provide. It does **not** connect to WeChat, read or decrypt WeChat databases, scrape
messages, or automate collection. Input is always a file you exported yourself or text you pasted.

All processing stays on your machine. Chat records contain other people's personal information;
review and redact before sharing any generated note. This project is provided as-is for personal
knowledge management. It is not affiliated with or endorsed by WeChat or Tencent.

## Profiles

| Profile | Chinese | Produces | Typical input |
|---|---|---|---|
| `knowledge` | 干货学习 | Topic outline, conclusions, facts and data, methods and cases | Study groups, courses, long discussions |
| `decision` | 工作 / 项目 | Decisions, todos, unresolved items, verbatim quotes | Work groups, project threads, post-meeting recaps |
| `crm` | 客户跟进 | Customer profile, needs, objections, pricing, next actions | One-to-one customer conversations |

`knowledge` is a summary template. It organizes what was said; it never produces article topics,
titles, or writing suggestions.

`auto` mode selects one main profile from signal counts. A conversation is not split into three
notes unless you explicitly ask for it.

## Repository layout

```
wechat-chat-summary/
├── README.md                 English (this page)
├── README.zh-CN.md            Simplified Chinese
├── LICENSE                    MIT
├── CONTRIBUTING.md
├── EXTEND.md.example          Configuration template
├── SKILL.md                   Skill metadata and workflow
├── scripts/
│   ├── parse_chat.py          Export parser and statistics
│   ├── detect_profile.py      Profile suggestion
│   ├── check_quotes.py        Quote attribution audit
│   ├── check_note.py          Note structure and consistency check
│   └── format_names.py        Raw-nickname normalization helper
├── references/
│   ├── profiles.md            Profile rules
│   ├── output-format.md       Writing rules
│   ├── input-formats.md       Supported export shapes
│   └── preferences.md         Configuration reference
└── assets/
    ├── template.md            decision skeleton
    ├── template-knowledge.md  knowledge skeleton
    ├── template-crm.md        crm skeleton
    ├── sample-chat.txt        Synthetic regression sample
    └── sample-wx-share.txt    Synthetic share-export sample
```

## Requirements

- Python 3.10 or newer. No third-party packages.
- An agent runtime that supports the Agent Skills format (`SKILL.md` frontmatter plus bundled resources).
- Optional: an Obsidian vault for the generated notes.

On Windows, replace `python3` in the commands below with `py -3` or your Python executable path.

## Install

```
git clone https://github.com/CationYang/wechat-chat-summary.git
cp -r wechat-chat-summary ~/.workbuddy/skills/wechat-chat-distill
```

Windows (PowerShell):

```
git clone https://github.com/CationYang/wechat-chat-summary.git
Copy-Item -Recurse wechat-chat-summary "$env:USERPROFILE\.workbuddy\skills\wechat-chat-distill"
```

Copy `EXTEND.md.example` to `EXTEND.md` in the installed skill directory and edit it. `EXTEND.md`
is ignored by git so local paths never enter the repository.

## Quick start

```
python3 scripts/parse_chat.py <chat-export.txt> --probe
python3 scripts/parse_chat.py <chat-export.txt> --out messages.json --stats --view view.md
python3 scripts/detect_profile.py messages.json
python3 scripts/check_quotes.py <note.md> messages.json
python3 scripts/check_note.py <note.md> messages.json
```

1. Run `--probe` first to confirm the detected format and message count.
2. Let your agent read `SKILL.md`, `references/profiles.md` and the matching `assets/template-*.md`,
   then write the note. Speaker names use the raw WeChat nickname inside `【】`.
3. Run both validators. `check_quotes.py` must report zero unmatched quotes; `check_note.py` must
   print `笔记校验：全部通过`.
4. Open the generated `.md` in Obsidian.

For large exports, use `--view` to produce a chronological, noise-filtered reading view instead of
loading the full JSON into context.

## Configuration

| Key | Default | Purpose |
|---|---|---|
| `vault` | `<your-vault>` | Obsidian vault root |
| `out_dir` | `{vault}/微信提炼` | Where notes and `_history.json` are written |
| `self_name` | (empty) | Normalize your own speaker label |
| `default_range` | `7d` | Range when no time range and no incremental anchor |
| `default_profile` | `auto` | `auto` / `knowledge` / `decision` / `crm` |
| `redact` | `false` | Mask phone numbers, emails and ID numbers |
| `date_prefix` | `true` | Prefix filenames with `YYYY-MM-DD` |

## Validation

```
python3 scripts/parse_chat.py assets/sample-chat.txt --stats
python3 scripts/parse_chat.py assets/sample-wx-share.txt --stats
python3 scripts/check_note.py <note.md> messages.json
```

The two synthetic samples are the regression baseline (8 and 6 messages). `check_note.py` validates
frontmatter, section order, quote attribution, message-count consistency, status values and speaker
formatting for the note's profile.

## Privacy

- No chat record, generated note, `messages.json`, or local path is included in this repository.
- All sample data under `assets/` is synthetic.
- `EXTEND.md`, `messages.json`, `view.md` and generated notes are git-ignored.
- Never commit a real chat export. Use `--redact` and review before sharing any note.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Acknowledgements

The three-pass distillation method and the mandatory attribution audit were adapted from
`baoyu-wechat-summary`. The folder layout follows the open Agent Skills format.

## License

[MIT](./LICENSE)
