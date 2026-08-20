# Data contracts

## Evidence bundle

`weread_export.py` creates a JSON object with these stable fields:

```json
{
  "schema_version": 1,
  "fetched_at": "ISO-8601",
  "skill_version": "1.0.4",
  "book": {"bookId": "...", "title": "...", "author": "..."},
  "chapters": [],
  "progress": {},
  "sources": [
    {
      "id": "h:bookmark-id",
      "type": "highlight",
      "chapter_uid": 1,
      "chapter_title": "...",
      "text": "...",
      "created_at": 0
    }
  ],
  "coverage": {
    "basis": "weread-personal-traces",
    "has_full_text": false,
    "chapter_count": 0,
    "covered_chapter_count": 0,
    "highlight_count": 0,
    "review_count": 0
  },
  "source_fingerprint": "sha256"
}
```

Source ID prefixes:

- `h:` — personal highlight from `/book/bookmarklist`
- `r:` — personal thought or review from `/review/list/mine`
- `p:` — optional popular highlight; never treat as personal evidence

## Concepts input

Write a JSON array. Each concept must follow this shape:

```json
[
  {
    "id": "test-for-compounding",
    "name": "用复利检验选择",
    "claim": "A concise paraphrase of the supported idea.",
    "when_to_use": ["选择工作", "评估长期项目"],
    "steps": ["列出一年后仍会保留的能力", "检查成果所有权"],
    "boundaries": ["现金流紧张时先满足生存约束"],
    "source_ids": ["h:123", "r:456"],
    "reader_view": "Optional reader-specific interpretation.",
    "agent_inference": "Optional inference that must be labeled as inference.",
    "confidence": "medium"
  }
]
```

Required fields: `id`, `name`, `claim`, `when_to_use`, `steps`, `boundaries`, `source_ids`, and `confidence`.

Constraints:

- Use kebab-case unique IDs.
- Use non-empty arrays for `when_to_use`, `steps`, `boundaries`, and `source_ids`.
- Use only source IDs present in the bundle.
- Set confidence to `high`, `medium`, or `low`.
- Paraphrase claims. Do not copy long source passages.
- Put the reader's interpretation in `reader_view`, not in `claim` as if it came from the author.
- Put new reasoning in `agent_inference` and keep the inference label visible.

## Generated state

`state/sync.json` contains the book ID, source fingerprint, included source IDs, concept IDs, generation time, privacy mode, and coverage. Use it for comparison during updates. It is not a substitute for the private evidence bundle.
