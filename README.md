# weread-to-skill

把微信读书里的章节、进度、个人划线和个人想法，编译成可追溯、可更新、能被 Codex 调用的个人书籍 Skill。

> 不是让 AI 替你读书，而是让你读过的书，在需要时重新参与判断。

## 它解决什么问题

普通读书笔记通常停留在“记录过”，很难在写作、学习或做决定时被重新调用。

`weread-to-skill` 是一个元 Skill：它不代表某一本书，而是负责把不同书籍的个人阅读痕迹，加工成新的书籍 Skill。生成结果关注的不是通用摘要，而是：

- 这条观点解决什么问题；
- 应该在什么场景调用；
- 可以执行哪些步骤；
- 什么情况下不适用；
- 它来自哪一章、哪条划线或个人想法；
- 哪些内容属于作者观点、读者理解或 AI 推导。

## 重要边界

微信读书数据只代表用户的阅读痕迹，不等于整本书全文。

因此，默认生成的是“基于个人划线与想法的书籍 Skill”，不会假装覆盖整本书。若需要完整书籍分析，应由用户另外提供自己合法拥有的本地文件，并单独记录来源。

## 工作流程

```mermaid
flowchart LR
    A["微信读书：目录、进度、划线、想法"] --> B["建立来源地图"]
    B --> C["提炼方法、步骤与边界"]
    C --> D["区分作者、读者与 AI 推导"]
    D --> E["生成个人书籍 Skill"]
    E --> F["真实问题调用与增量更新"]
```

系统分为三层：

1. **数据层**：读取书籍信息、章节目录、阅读进度、个人划线和个人想法。
2. **理解层**：由 Codex 提炼概念、适用场景、行动步骤、边界和来源。
3. **编译层**：脚本确定性地生成书籍 Skill、来源地图和同步状态，并执行校验。

## 功能

- 按书名或 `bookId` 导出单本书的个人阅读痕迹；
- 自动处理个人想法的游标分页；
- 生成稳定的来源 ID 和内容指纹；
- 把语义提炼与机械编译分开，避免脚本假装理解书籍；
- 为每本书生成独立的 `SKILL.md` 和按需读取的参考文件；
- 支持基于来源指纹和来源 ID 的增量更新；
- 支持私有版与可分享版；
- 检查来源引用、目录结构、API Key、授权头和个人绝对路径。

## 安装

### 1. 克隆到 Codex Skills 目录

仓库为私有仓库时，推荐使用已登录的 GitHub CLI：

```bash
codex_skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$codex_skills_dir"
gh repo clone jyqi/weread-to-skill "$codex_skills_dir/weread-to-skill"
```

重新打开 Codex 任务，让 Skill 列表刷新。

### 2. 配置微信读书

前往下面的页面获取微信读书 API Key：

<https://weread.qq.com/r/weread-skills>

然后在 Codex 可读取的环境中设置：

```bash
export WEREAD_API_KEY="wrk-xxxxxxxx"
```

不要把真实 API Key 写进仓库、提示词、截图或生成的书籍 Skill。

### 3. 安装官方微信读书 Skill（推荐）

```bash
npx skills add Tencent/WeChatReading -g
```

`weread-to-skill` 自带必要的导出脚本，但官方 Skill 能提供完整的微信读书查询能力和最新字段说明。

## 使用

安装完成后，直接用自然语言调用：

```text
把我微信读书里的《纳瓦尔宝典》，做成一个辅助职业决策的个人 Skill。
```

也可以指定其他目标：

```text
把《原则》的划线和想法炼成一个写作 Skill。

把我在这本书里的阅读笔记做成复习助手。

我又增加了几条划线，更新之前生成的书籍 Skill。

生成一个不包含个人笔记原文、可以分享给别人的版本。
```

Skill 会先确认具体书籍和主要用途，再进行导出、提炼、编译与校验。遇到同名书或不同版本时，不应静默选择。

## 手动运行

通常应让 Codex 完成整个流程。需要排查问题时，也可以手动执行脚本。

### 导出单本书

```bash
python3 scripts/weread_export.py export-book \
  --title "书名" \
  --output work/book-bundle.json
```

或者直接传入已经确认的 `bookId`：

```bash
python3 scripts/weread_export.py export-book \
  --book-id "book-id" \
  --output work/book-bundle.json
```

导出文件包含私人阅读数据，默认只应保存在本地私有工作目录。

### 提炼概念

让 Codex 根据 [`references/data-contracts.md`](references/data-contracts.md) 把证据提炼为 `concepts.json`。每个概念必须包含：

- 名称与核心判断；
- 使用场景；
- 可执行步骤；
- 边界或失败条件；
- 有效的来源 ID；
- 置信度；
- 可选的读者观点和 AI 推导。

### 编译书籍 Skill

```bash
python3 scripts/compile_skill.py \
  --bundle work/book-bundle.json \
  --concepts work/concepts.json \
  --skill-name book-skill-name \
  --output-dir /path/to/codex-skills/book-skill-name
```

生成可分享版本：

```bash
python3 scripts/compile_skill.py \
  --bundle work/book-bundle.json \
  --concepts work/concepts.json \
  --skill-name book-skill-name \
  --output-dir /path/to/output/book-skill-name \
  --privacy shareable
```

### 验证

```bash
python3 scripts/validate_generated_skill.py /path/to/generated-skill
python3 scripts/scan_secrets.py /path/to/generated-skill
```

## 生成结果

每本书会生成一个独立目录：

```text
<book-slug>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── concepts.md
│   ├── source-map.md
│   └── reader-notes.md
└── state/
    └── sync.json
```

- `SKILL.md`：核心行为、证据边界和请求路由；
- `concepts.md`：可以被调用的方法单元；
- `source-map.md`：章节、来源类型和短证据锚点；
- `reader-notes.md`：个人想法，仅私有模式保留正文；
- `sync.json`：来源指纹、来源 ID、概念 ID 和生成状态。

## 私有版与可分享版

| 模式 | 适合场景 | 保留内容 |
|---|---|---|
| `private` | 个人使用 | 短划线锚点、个人想法、来源 ID、概念 |
| `shareable` | 公开或团队分享 | 概念、章节锚点、来源 ID；隐藏个人想法正文和划线原文 |

即使使用可分享模式，也应在发布前人工检查个人案例、姓名、路径和上下文信息。模式转换不能替代人工隐私审查。

## 项目结构

```text
weread-to-skill/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── scripts/
│   ├── weread_export.py
│   ├── compile_skill.py
│   ├── validate_generated_skill.py
│   └── scan_secrets.py
├── references/
│   ├── workflow.md
│   ├── weread-api.md
│   ├── data-contracts.md
│   ├── quality-gates.md
│   └── safety.md
└── evals/
    ├── evals.json
    └── fixtures/
```

## 质量标准

一个合格的书籍 Skill 应满足：

- 每个概念都能追溯到有效来源；
- 每个概念都有使用场景、行动步骤和适用边界；
- 作者观点、读者理解和 AI 推导没有混写；
- 不把划线数量当作理解深度；
- 不声称覆盖没有读取的章节；
- 更新时不重复追加旧内容；
- 结构校验和凭证扫描均通过。

## 本地验证

仓库包含不涉及真实账户的测试夹具：

```bash
python3 scripts/compile_skill.py \
  --bundle evals/fixtures/sample_bundle.json \
  --concepts evals/fixtures/sample_concepts.json \
  --skill-name test-book \
  --output-dir work/test-book

python3 scripts/validate_generated_skill.py work/test-book
python3 scripts/scan_secrets.py work/test-book
```

## 当前限制

- 不获取或重构微信读书整本正文；
- 语义提炼依赖 Codex，Python 脚本只负责导出、校验和确定性编译；
- 阅读痕迹较少时，只适合生成窄范围 Skill；
- 分享模式会减少来源细节，不适合需要逐条核对原始笔记的场景；
- 微信读书接口字段或版本变化时，需要同步官方 Skill 的最新说明。
