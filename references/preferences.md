# Preferences — EXTEND.md

Read this file when editing `EXTEND.md` or changing the output vault.

## Location

`EXTEND.md` lives in the skill directory itself:
`EXTEND.md in the skill directory`.

Plain text, one `key: value` per line, `#` starts a comment, keys are case-insensitive. Missing
keys fall back to defaults; a missing file does not block a run.

## Keys

| Key | Default | Notes |
|-----|---------|-------|
| `vault` | `<your-vault>` | Obsidian vault root |
| `out_dir` | `{vault}/微信提炼` | Where notes and `_history.json` go. May be an absolute path outside the vault. |
| `self_name` | (empty) | Replaces `我` / `自己` / `self` / `me` as the speaker label |
| `default_range` | `7d` | Used only when no range is given and no incremental anchor exists |
| `redact` | `false` | Mask phone / email / ID numbers at parse time |
| `date_prefix` | `true` | Prefix filenames with `YYYY-MM-DD` |

`{vault}` inside `out_dir` expands to the value of `vault` at run time. An absolute `out_dir`
overrides it entirely.

## Example vault configuration

Typical values:

| Vault | Path | State |
|-------|------|-------|
| Vault A | `<your-vault>` | example primary vault |
| Vault B | `<another-vault>` | example secondary vault |

Switch by editing `vault` in `EXTEND.md`. Keep `out_dir` as `{vault}/微信提炼` so the switch
carries the output folder with it.

## Windows paths

Use backslashes or forward slashes consistently; both are accepted. A path containing spaces does
not need quoting inside `EXTEND.md` (the whole line after `:` is the value), but always quote it in
shell commands.

## First-time customization

1. Confirm which vault should hold chat notes; edit `vault`.
2. Fill `self_name` with the display name used in exports (optional).
3. Set `redact: true` if notes will be shared outside the local vault.
4. Run one small export end-to-end and verify the note lands in the expected folder.
