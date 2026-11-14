# wechat-chat-summary

把微信聊天记录导出文件，提炼成可回溯、结构化的 Obsidian Markdown 笔记。

[English](./README.md) | **简体中文**

## 项目特点

- 三种整理模板：`knowledge` 干货学习（按主题梳理）、`decision` 工作项目（决策 / 待办 / 未闭环）、`crm` 客户跟进（画像 / 需求 / 异议 / 报价 / 下一步）。
- 每条直接引语都会回原文校验，编造的引语无法通过审计。
- 所有统计数字由解析脚本机械计算，不靠目测。
- 支持 `.txt`、`.csv`、`.json`、`.jsonl`、`.html` 以及微信分享导出的聊天记录。
- 增量提炼，且每种模板各有一个独立的时间锚点。
- 全程本地：不访问数据库、不联网、不解密微信数据。

## 边界与免责

这是一个 **Agent Skill**：一组供 AI 智能体按需加载的指令与脚本，用来处理你提供的文件。它**不会**连接微信、读取或解密微信本地数据库、抓取消息，也不做自动化采集。输入始终是你自己导出的文件或粘贴的文本。

所有处理都留在本机。聊天记录包含他人的个人信息，分享任何笔记前请先复核并脱敏。本项目按「原样」提供，用于个人知识管理，与微信及腾讯无关联，也未获其认可。

## 三种模板

| 模板 | 名称 | 产出 | 典型输入 |
|---|---|---|---|
| `knowledge` | 干货学习 | 主题脉络、结论共识、事实数据、方法案例 | 学习群、课程群、长文讨论 |
| `decision` | 工作 / 项目 | 决策、待办、未闭环、逐字原话 | 工作群、项目讨论、会后复盘 |
| `crm` | 客户跟进 | 客户信息、需求痛点、异议回应、报价承诺、下一步 | 一对一客户对话 |

`knowledge` 是总结提炼模板，只梳理内容，不产出选题、标题或写作建议。

`auto` 模式按信号强度选出**一个**主模板；除非你明确要求，否则一段对话不会被拆成三篇笔记。

## 仓库结构

```
wechat-chat-summary/
├── README.md                 英文主页面
├── README.zh-CN.md           简体中文（本页）
├── LICENSE                   MIT
├── CONTRIBUTING.md
├── EXTEND.md.example         配置模板
├── SKILL.md                  技能元数据与工作流
├── scripts/
│   ├── parse_chat.py         导出解析与统计
│   ├── detect_profile.py     模板自动判定
│   ├── check_quotes.py       引语归因校验
│   ├── check_note.py         笔记结构与一致性校验
│   └── format_names.py       原始昵称规范化工具
├── references/
│   ├── profiles.md           三种模板规则
│   ├── output-format.md      写作规范
│   ├── input-formats.md      支持的导出格式
│   └── preferences.md        配置说明
└── assets/
    ├── template.md            decision 骨架
    ├── template-knowledge.md  knowledge 骨架
    ├── template-crm.md        crm 骨架
    ├── sample-chat.txt        合成回归样本
    └── sample-wx-share.txt    合成分享导出样本
```

## 环境要求

- Python 3.10 及以上，无第三方依赖。
- 支持 Agent Skills 格式的智能体运行时（能读取 `SKILL.md` frontmatter 及附带资源）。
- 可选：用于存放笔记的 Obsidian 仓库。

Windows 下请把下列命令中的 `python3` 换成 `py -3` 或你的 Python 路径。

## 安装

```
git clone https://github.com/CationYang/wechat-chat-summary.git
cp -r wechat-chat-summary ~/.workbuddy/skills/wechat-chat-distill
```

Windows（PowerShell）：

```
git clone https://github.com/CationYang/wechat-chat-summary.git
Copy-Item -Recurse wechat-chat-summary "$env:USERPROFILE\.workbuddy\skills\wechat-chat-distill"
```

把 `EXTEND.md.example` 复制为技能目录下的 `EXTEND.md` 并按本机情况修改。`EXTEND.md` 已被 git 忽略，本机路径不会进入仓库。

## 快速开始

```
python3 scripts/parse_chat.py <chat-export.txt> --probe
python3 scripts/parse_chat.py <chat-export.txt> --out messages.json --stats --view view.md
python3 scripts/detect_profile.py messages.json
python3 scripts/check_quotes.py <note.md> messages.json
python3 scripts/check_note.py <note.md> messages.json
```

1. 先跑 `--probe`，确认识别出的格式与消息条数。
2. 让智能体读取 `SKILL.md`、`references/profiles.md` 及对应的 `assets/template-*.md` 后撰写笔记。发言人一律写微信原始昵称，放进 `【】`。
3. 跑两个校验脚本。`check_quotes.py` 必须显示「未匹配 0 处」，`check_note.py` 必须打印「笔记校验：全部通过」。
4. 在 Obsidian 中打开生成的 `.md`。

大批量记录请用 `--view` 生成按时间排序的去噪阅读视图，不要把完整 JSON 塞进上下文。

## 配置

| 键 | 默认值 | 作用 |
|---|---|---|
| `vault` | `<your-vault>` | Obsidian 仓库根目录 |
| `out_dir` | `{vault}/微信提炼` | 笔记与 `_history.json` 的落盘位置 |
| `self_name` | （空） | 归一自己发言人的显示名 |
| `default_range` | `7d` | 未指定范围、且无增量锚点时的默认范围 |
| `default_profile` | `auto` | `auto` / `knowledge` / `decision` / `crm` |
| `redact` | `false` | 掩码手机号、邮箱、证件号 |
| `date_prefix` | `true` | 文件名前置 `YYYY-MM-DD` |

## 校验与回归

```
python3 scripts/parse_chat.py assets/sample-chat.txt --stats
python3 scripts/parse_chat.py assets/sample-wx-share.txt --stats
python3 scripts/check_note.py <note.md> messages.json
```

两个合成样本是回归基线（8 条与 6 条消息）。`check_note.py` 会按笔记的 profile 校验 frontmatter、章节顺序、引语归因、消息数一致性、状态值与人名格式。

## 隐私

- 仓库中不包含任何真实聊天记录、提炼笔记、`messages.json` 或本机路径。
- `assets/` 下的样本数据均为合成内容。
- `EXTEND.md`、`messages.json`、`view.md` 与生成的笔记都在 `.gitignore` 中。
- 切勿提交真实聊天导出。分享笔记前请使用 `--redact` 并人工复核。

## 贡献

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 致谢

三遍提炼法与强制归因审计改编自 `baoyu-wechat-summary`；目录结构遵循开放的 Agent Skills 格式。

## 许可

[MIT](./LICENSE)
