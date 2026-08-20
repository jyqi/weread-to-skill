# Quality gates

Apply all gates before delivering a generated book skill.

## Evidence gate

- Every concept cites at least one valid bundle source ID.
- Author claims are paraphrases supported by the cited evidence.
- Reader views come only from personal reviews or clearly labeled interpretation of highlight selection.
- Agent inference remains explicitly labeled.

## Action gate

- Each concept states when to use it.
- Each concept contains at least one observable step.
- Each concept contains at least one boundary, counterexample, or failure condition.
- Remove concepts that merely restate a chapter topic.

## Distinctness gate

- Concept names describe different decisions or mechanisms.
- Merge overlapping concepts only when their mechanisms and boundaries match.
- Preserve genuine disagreement rather than flattening it into a generic principle.

## Coverage gate

- The generated `SKILL.md` states that WeRead-only input is not full-book coverage.
- The source map reports covered chapters and source counts.
- The skill refuses requests that require unseen full text or clearly labels the answer as outside its evidence.

## Privacy and copyright gate

- Private builds stay local.
- Shareable builds omit personal note text and raw highlight excerpts.
- No API keys, authorization headers, user IDs, or absolute personal paths appear in the skill.
- Quotes remain short and necessary; prefer paraphrase plus source anchor.

## Validation target

The structure validator, source validator, and secret scanner must all exit with code 0. Then test application, boundary, traceability, and coverage-challenge prompts manually.
