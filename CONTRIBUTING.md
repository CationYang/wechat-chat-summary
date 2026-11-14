# Contributing

Thanks for helping improve this skill.

## Ground rules

- Never commit real WeChat exports, distilled notes, `messages.json`, or local absolute paths.
- All sample data must stay synthetic.
- Keep `README.md` and `README.zh-CN.md` in sync: same section order, identical commands, paths,
  code blocks, and configuration keys. The Chinese version is natural technical writing, not a
  word-for-word translation.
- `SKILL.md` frontmatter needs `name`, `description`, and `agent_created: true`. The description
  states when the skill should be used.
- Speaker names in output templates use the raw WeChat nickname inside `【】`. Do not reintroduce
  shortened display names or alias lookup tables.

## Adding an export format

1. Add a small synthetic sample under `assets/`.
2. Add the detection rule and parser branch in `scripts/parse_chat.py`.
3. Document the shape in `references/input-formats.md`.
4. Run both existing samples and confirm their message counts are unchanged.

## Changing a profile template

1. Edit the matching `assets/template-*.md`.
2. Update the section list in `references/profiles.md` and `scripts/check_note.py`.
3. Update both READMEs if the layout or commands change.

## Before opening a pull request

```
python3 scripts/parse_chat.py assets/sample-chat.txt --probe
python3 scripts/parse_chat.py assets/sample-wx-share.txt --probe
python3 scripts/check_quotes.py <note.md> messages.json
python3 scripts/check_note.py <note.md> messages.json
```

Expected: 8 messages in the first sample, 6 in the second, zero unmatched quotes, and
`笔记校验：全部通过` from the note validator.

## Reporting issues

Include the export format, the `--probe` output, and the Python version. Redact all personal
information before pasting any log.
