# Workflow

## 1. Define the use lens

Choose one primary lens before distillation:

| Lens | Prefer extracting |
|---|---|
| `decision` | trade-offs, tests, thresholds, reversibility, failure modes |
| `writing` | arguments, distinctions, examples, counterarguments, reusable structures |
| `learning` | explanations, prerequisite concepts, misconceptions, retrieval questions |
| `review` | core claims, memory cues, unresolved questions, contradictions |

Use a custom lens only when the user's goal is more specific. Keep one primary lens so the generated skill does not become a generic summary.

## 2. Resolve and export

Prefer a `bookId` already established in the conversation. Otherwise search by title with `scope=10`. If multiple plausible editions remain, show title, author, and book ID and wait for a selection.

Export book info, chapter metadata, reading progress, personal highlights, and all pages of personal reviews. Popular highlights are optional context and must never be labeled as the user's view.

## 3. Audit coverage

Use the exported `coverage` object. Classify the evidence:

- `strong-traces`: at least 10 personal sources across at least 3 chapters.
- `partial-traces`: 3-9 personal sources or fewer than 3 covered chapters.
- `thin-traces`: 1-2 personal sources.
- `outline-only`: no personal sources.

These thresholds guide disclosure, not truth. A short book may still be well represented by fewer sources. Always preserve `has_full_text: false` for WeRead-only export.

## 4. Build concept candidates

Group sources by semantic relationship, not merely by chapter. For every candidate, ask:

1. What problem does this change?
2. What is the mechanism or distinction?
3. What observable action or diagnostic follows?
4. When does it fail?
5. Which exact sources support it?

Reject duplicates, generic advice, unsupported author attribution, and claims that depend on missing context.

## 5. Write concepts JSON

Create 4-12 units. Use fewer when evidence is thin. Stable IDs should be short kebab-case labels based on meaning, not chapter numbers, so updates can preserve identity.

Use `confidence: high` only when multiple independent personal sources support the unit or one source is unusually explicit. Use `medium` for a reasonable synthesis and `low` for tentative inference. A low-confidence unit must say what evidence is missing.

## 6. Compile and validate

Run `compile_skill.py`, then both validators. The compiler is deterministic: it renders the concepts the agent supplied and verifies that every source ID exists. It does not decide whether a concept is intellectually sound; quality review remains the agent's responsibility.

## 7. Forward test

Use at least these prompt types:

- Application: “用这本书帮我分析一个真实选择。”
- Boundary: “这个原则在现金流紧张时还成立吗？”
- Traceability: “这条判断来自哪一章、哪条笔记？”
- Coverage challenge: “请总结这本书所有章节。”

The generated skill should apply frameworks, name boundaries, return source IDs on request, and refuse to pretend it saw unobserved chapters.

## 8. Update

On refresh, compare `source_fingerprint` and source IDs. Added sources may extend or revise a concept. Removed sources may lower confidence or invalidate it. Never assume that a changed note merely adds support.
