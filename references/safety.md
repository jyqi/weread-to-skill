# Safety, privacy, and copyright

## Private by default

Treat book lists, reading progress, highlights, personal reviews, and reading statistics as private user data. Do not publish, upload, or commit them without explicit authorization.

Use working files under a task-specific private directory. Do not place API responses in a public repository. Never embed `WEREAD_API_KEY` or an authorization header in generated files.

## Coverage honesty

WeRead traces do not equal the complete book. A highlight may omit surrounding context, translation nuance, examples, and later qualifications. Always disclose `has_full_text: false` and refuse to attribute unseen material to the author.

If the user supplies a lawful local copy separately, process it with an appropriate document skill and record that source independently. Do not silently upgrade a trace-based skill into a full-book claim.

## Copyright minimization

- Keep raw exported text local.
- Use short excerpts only when necessary for traceability.
- Prefer paraphrased concepts, methods, and distinctions.
- Do not create a shareable artifact containing long passages or a reconstruction of the book.

## Shareable mode

Compile with `--privacy shareable`. This mode removes personal note bodies and raw highlight excerpts from rendered references. It retains source IDs, chapter anchors, paraphrased concepts, and coverage disclosure.

Before sharing, run `scan_secrets.py` and manually inspect the output for private examples, names, paths, and context that the pattern scanner cannot detect.
