---
name: weread-to-skill
description: Turn one WeRead book's chapter metadata, reading progress, personal highlights, and personal reviews into a traceable, incrementally updatable Codex skill. Use when the user asks to 把微信读书某本书做成 Skill、炼书、把划线变成方法库、生成个人书籍助手、更新已有书籍 Skill，or apply personal reading notes as decision, writing, learning, or review frameworks. This skill works from reading traces and must not claim full-book coverage unless the user separately supplies lawful full text.
---

# WeRead to Skill

Compile personal WeRead traces into an operational book skill. Preserve the boundary between the author's words, the reader's notes, and agent inference.

## Prerequisites

- Require `WEREAD_API_KEY` in the environment. If absent, ask the user to obtain it from `https://weread.qq.com/r/weread-skills` and set `export WEREAD_API_KEY=<key>`.
- Prefer the companion `weread-skills` skill when it is installed. Never copy or expose its API key.
- Treat the exported bundle and generated skill as private unless the user explicitly requests a shareable build.

## Choose the operation

- **Create**: export one book, distill concepts, and generate a new personal book skill.
- **Update**: export the same book again, compare source IDs with `state/sync.json`, revise affected concepts, and regenerate without duplicating sources.
- **Shareable copy**: regenerate with `--privacy shareable`; omit personal note text and raw highlight excerpts.
- **Inspect only**: export or analyze evidence without creating a skill when the user only asks for a report.

Read [workflow.md](references/workflow.md) before creating or updating a skill. Read [weread-api.md](references/weread-api.md) before fetching data. Read [data-contracts.md](references/data-contracts.md) before writing the concept JSON. Read [quality-gates.md](references/quality-gates.md) and [safety.md](references/safety.md) before final delivery.

Resolve every script path relative to the directory containing this `SKILL.md`. The examples below use `<skill-dir>` as that absolute directory and `<codex-skills-dir>` as the user's configured personal skills directory.

## Create a book skill

1. Resolve the book. When the title is ambiguous, show numbered candidates and let the user select; never silently choose a different edition.
2. Ask or infer one primary use lens: `decision`, `writing`, `learning`, `review`, or a short custom goal. State the inferred lens before compilation.
3. Export the private evidence bundle:

```bash
python3 <skill-dir>/scripts/weread_export.py export-book \
  --title "书名" \
  --output work/book-bundle.json
```

4. Inspect `coverage`. Explicitly say the result is based on reading traces, not the full book. If there are no personal highlights or reviews, stop before skill generation and offer an outline-only note instead.
5. Distill 4-12 concepts into `work/concepts.json` using the schema and evidence rules in [data-contracts.md](references/data-contracts.md). Do not let a script invent semantic concepts.
6. Compile the generated skill:

```bash
python3 <skill-dir>/scripts/compile_skill.py \
  --bundle work/book-bundle.json \
  --concepts work/concepts.json \
  --output-dir <codex-skills-dir>/<book-slug>
```

7. Validate structure, source lineage, and secrets:

```bash
python3 <skill-dir>/scripts/validate_generated_skill.py <codex-skills-dir>/<book-slug>
python3 <skill-dir>/scripts/scan_secrets.py <codex-skills-dir>/<book-slug>
```

8. Run at least four realistic prompts: direct application, boundary case, source-trace request, and unsupported/full-book claim. Revise concepts if the skill gives generic or ungrounded answers.

## Distillation rules

- Separate `author_claim`, `reader_view`, and `agent_inference` in meaning even when the final prose is compact.
- Keep a concept only when it changes a decision, action, explanation, or diagnostic question.
- Attach every author claim and reader view to at least one `source_id` from the bundle.
- Prefer the reader's own notes over popular highlights. Do not use public comments as if they were the reader's view.
- Preserve disagreement and uncertainty. Do not merge conflicting concepts into false consensus.
- Express boundaries and failure conditions. Reject generic units such as “保持长期主义” unless the evidence supplies a distinctive mechanism or test.
- Quote minimally. Use short anchors and paraphrases; never reproduce long passages.

## Update an existing skill

1. Export a fresh bundle for the same `bookId`.
2. Compare its `source_fingerprint` and source IDs with `state/sync.json`.
3. If unchanged, report that there is nothing to update.
4. If changed, revise only concepts affected by added, removed, or modified sources. Preserve stable concept IDs.
5. Re-run compilation and both validators. Never append duplicate sections to an existing file.

## Output contract

Generate one folder containing:

```text
<book-slug>/
├── SKILL.md
├── agents/openai.yaml
├── references/concepts.md
├── references/source-map.md
├── references/reader-notes.md
└── state/sync.json
```

In the final response, report the coverage basis, counts of highlights/reviews/concepts, privacy mode, validation result, and the created folder path. Do not claim that the generated skill represents the entire book.
