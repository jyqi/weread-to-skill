#!/usr/bin/env python3
"""Compile a normalized WeRead evidence bundle and agent-authored concepts into a skill."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CONFIDENCE = {"high", "medium", "low"}


class ContractError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return ascii_slug or "weread-book-skill"


def validate_bundle(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if bundle.get("schema_version") != 1:
        raise ContractError("Unsupported or missing bundle schema_version")
    if not isinstance(bundle.get("book"), dict) or not bundle["book"].get("bookId"):
        raise ContractError("Bundle book.bookId is required")
    if not isinstance(bundle.get("sources"), list):
        raise ContractError("Bundle sources must be an array")
    source_map: dict[str, dict[str, Any]] = {}
    for source in bundle["sources"]:
        source_id = source.get("id") if isinstance(source, dict) else None
        if not source_id or source_id in source_map:
            raise ContractError(f"Invalid or duplicate source ID: {source_id!r}")
        source_map[source_id] = source
    return source_map


def require_string_list(concept: dict[str, Any], field: str) -> list[str]:
    value = concept.get(field)
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ContractError(f"Concept {concept.get('id')!r}: {field} must be a non-empty string array")
    return [item.strip() for item in value]


def validate_concepts(
    concepts: Any, source_map: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(concepts, list) or not concepts:
        raise ContractError("Concepts must be a non-empty JSON array")
    if len(concepts) > 20:
        raise ContractError("Refuse more than 20 concepts; distill or merge them")
    seen_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for concept in concepts:
        if not isinstance(concept, dict):
            raise ContractError("Every concept must be an object")
        concept_id = str(concept.get("id") or "")
        if not SLUG_RE.fullmatch(concept_id) or concept_id in seen_ids:
            raise ContractError(f"Invalid or duplicate concept id: {concept_id!r}")
        seen_ids.add(concept_id)
        name = str(concept.get("name") or "").strip()
        claim = str(concept.get("claim") or "").strip()
        confidence = str(concept.get("confidence") or "")
        if not name or not claim:
            raise ContractError(f"Concept {concept_id!r}: name and claim are required")
        if confidence not in CONFIDENCE:
            raise ContractError(f"Concept {concept_id!r}: invalid confidence")
        source_ids = require_string_list(concept, "source_ids")
        missing = [source_id for source_id in source_ids if source_id not in source_map]
        if missing:
            raise ContractError(f"Concept {concept_id!r}: missing source IDs {missing}")
        normalized.append(
            {
                "id": concept_id,
                "name": name,
                "claim": claim,
                "when_to_use": require_string_list(concept, "when_to_use"),
                "steps": require_string_list(concept, "steps"),
                "boundaries": require_string_list(concept, "boundaries"),
                "source_ids": source_ids,
                "reader_view": str(concept.get("reader_view") or "").strip(),
                "agent_inference": str(concept.get("agent_inference") or "").strip(),
                "confidence": confidence,
            }
        )
    return normalized


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_skill(book: dict[str, Any], slug: str, coverage: dict[str, Any]) -> str:
    title = str(book.get("title") or slug)
    author = str(book.get("author") or "未知作者")
    description = (
        f"Apply traceable personal reading frameworks derived from the user's WeRead traces "
        f"for {title} by {author}. Use for decisions, writing, learning, review, source tracing, "
        "and boundary checks related to this book. This skill covers personal highlights and "
        "reviews, not the complete book text."
    )
    return f"""---
name: {slug}
description: {yaml_quote(description)}
---

# {title}：个人阅读 Skill

Use this skill as an operational interpretation of the user's WeRead traces for **{title}** by {author}.

## Evidence boundary

- Treat this as personal reading-trace coverage, not full-book coverage.
- Never claim access to unseen chapters or the complete text.
- Distinguish author-oriented paraphrase, reader view, and agent inference.
- Return source IDs and chapter anchors when the user asks for evidence.

Coverage at generation time: {coverage.get('highlight_count', 0)} personal highlights, {coverage.get('review_count', 0)} personal reviews, and {coverage.get('covered_chapter_count', 0)} chapters with traces out of {coverage.get('chapter_count', 0)} listed chapters.

## Route the request

1. Read [concepts.md](references/concepts.md) for the relevant method units.
2. Read [source-map.md](references/source-map.md) when evidence, chapter context, or confidence matters.
3. Read [reader-notes.md](references/reader-notes.md) only when personal interpretation is relevant.
4. If the request requires full-book coverage, state the limitation and ask for a lawful local copy or a narrower question.

## Response method

1. Name the relevant concept and why it applies.
2. Apply its steps to the user's real situation.
3. State the boundary or countercondition.
4. Label reader-specific interpretation and new inference.
5. Cite source IDs on request; do not invent quotations or chapter locations.
"""


def render_concepts(concepts: list[dict[str, Any]], source_map: dict[str, dict[str, Any]]) -> str:
    lines = ["# Concepts", ""]
    for concept in concepts:
        chapters = sorted(
            {
                str(source_map[source_id].get("chapter_title") or "未标注章节")
                for source_id in concept["source_ids"]
            }
        )
        lines.extend(
            [
                f"## {concept['name']}",
                "",
                f"- ID: `{concept['id']}`",
                f"- Confidence: `{concept['confidence']}`",
                f"- Claim: {concept['claim']}",
                f"- Use when: {'；'.join(concept['when_to_use'])}",
                f"- Chapters: {'；'.join(chapters)}",
                f"- Sources: {', '.join(f'`{sid}`' for sid in concept['source_ids'])}",
                "",
                "### Steps",
                "",
            ]
        )
        lines.extend(f"{index}. {step}" for index, step in enumerate(concept["steps"], 1))
        lines.extend(["", "### Boundaries", ""])
        lines.extend(f"- {item}" for item in concept["boundaries"])
        if concept["reader_view"]:
            lines.extend(["", f"**Reader view:** {concept['reader_view']}"])
        if concept["agent_inference"]:
            lines.extend(["", f"**Agent inference:** {concept['agent_inference']}"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def short_text(value: Any, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_source_map(bundle: dict[str, Any], privacy: str) -> str:
    coverage = bundle.get("coverage") or {}
    lines = [
        "# Source map",
        "",
        "> Coverage is based on WeRead reading traces, not the complete book text.",
        "",
        f"- Basis: `{coverage.get('basis', 'weread-personal-traces')}`",
        f"- Full text available: `{str(bool(coverage.get('has_full_text'))).lower()}`",
        f"- Personal highlights: {coverage.get('highlight_count', 0)}",
        f"- Personal reviews: {coverage.get('review_count', 0)}",
        f"- Covered chapters: {coverage.get('covered_chapter_count', 0)} / {coverage.get('chapter_count', 0)}",
        "",
        "## Anchors",
        "",
    ]
    for source in bundle.get("sources", []):
        lines.append(
            f"### `{source['id']}` · {source.get('chapter_title') or '未标注章节'} · {source.get('type')}"
        )
        lines.append("")
        if privacy == "private":
            excerpt = source.get("text") or source.get("abstract")
            lines.append(f"> {short_text(excerpt) if excerpt else '[no text]'}")
        else:
            lines.append("> [excerpt omitted in shareable mode]")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_reader_notes(bundle: dict[str, Any], privacy: str) -> str:
    lines = ["# Reader notes", ""]
    reviews = [source for source in bundle.get("sources", []) if source.get("type") == "reader_review"]
    if privacy == "shareable":
        return "# Reader notes\n\nPersonal note bodies are omitted in shareable mode.\n"
    if not reviews:
        return "# Reader notes\n\nNo personal review text was available at generation time.\n"
    for source in reviews:
        lines.extend(
            [
                f"## `{source['id']}` · {source.get('chapter_title') or '未标注章节'}",
                "",
                short_text(source.get("text"), 500) or "[empty note]",
                "",
            ]
        )
        if source.get("abstract"):
            lines.extend([f"> Related excerpt: {short_text(source['abstract'])}", ""])
    return "\n".join(lines).rstrip() + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def compile_skill(
    bundle: dict[str, Any], concepts_data: Any, output_dir: Path, slug: str, privacy: str
) -> None:
    source_map = validate_bundle(bundle)
    concepts = validate_concepts(concepts_data, source_map)
    book = bundle["book"]
    coverage = bundle.get("coverage") or {}

    atomic_write(output_dir / "SKILL.md", render_skill(book, slug, coverage))
    atomic_write(output_dir / "references" / "concepts.md", render_concepts(concepts, source_map))
    atomic_write(output_dir / "references" / "source-map.md", render_source_map(bundle, privacy))
    atomic_write(output_dir / "references" / "reader-notes.md", render_reader_notes(bundle, privacy))
    display_name = f"{book.get('title') or slug} · 个人阅读"
    short_description = "调用个人划线与想法中的书籍框架"
    prompt = f"Use ${slug} to apply this book's traceable personal reading frameworks to my current problem."
    openai_yaml = (
        "interface:\n"
        f"  display_name: {yaml_quote(display_name)}\n"
        f"  short_description: {yaml_quote(short_description)}\n"
        f"  default_prompt: {yaml_quote(prompt)}\n"
    )
    atomic_write(output_dir / "agents" / "openai.yaml", openai_yaml)
    state = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "book_id": str(book.get("bookId")),
        "source_fingerprint": bundle.get("source_fingerprint"),
        "source_ids": sorted(source_map),
        "concept_ids": [concept["id"] for concept in concepts],
        "privacy": privacy,
        "coverage": coverage,
    }
    atomic_write(
        output_dir / "state" / "sync.json",
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--concepts", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--skill-name")
    parser.add_argument("--privacy", choices=["private", "shareable"], default="private")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    bundle = load_json(args.bundle)
    concepts = load_json(args.concepts)
    suggested = args.skill_name or slugify(str(bundle.get("book", {}).get("title") or ""))
    if not SLUG_RE.fullmatch(suggested):
        raise SystemExit("--skill-name must contain lowercase letters, digits, and hyphens only")
    resolved_output = args.output_dir.expanduser().resolve()
    if resolved_output == Path(resolved_output.anchor) or resolved_output == Path.home().resolve():
        raise SystemExit("Refusing to use a filesystem root or home directory as --output-dir")
    compile_skill(bundle, concepts, resolved_output, suggested, args.privacy)
    print(f"Generated {suggested} -> {resolved_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
