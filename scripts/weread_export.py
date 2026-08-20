#!/usr/bin/env python3
"""Export one WeRead book's personal reading traces as a normalized JSON bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GATEWAY = "https://i.weread.qq.com/api/agent/gateway"
SKILL_VERSION = "1.0.4"


class WeReadError(RuntimeError):
    pass


def gateway(api_name: str, **params: Any) -> dict[str, Any]:
    api_key = os.environ.get("WEREAD_API_KEY", "").strip()
    if not api_key:
        raise WeReadError(
            "WEREAD_API_KEY is not set. Run: export WEREAD_API_KEY=<your-api-key>"
        )

    body = {"api_name": api_name, **params, "skill_version": SKILL_VERSION}
    request = urllib.request.Request(
        GATEWAY,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise WeReadError(f"WeRead HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise WeReadError(f"Unable to reach WeRead: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise WeReadError("WeRead returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise WeReadError("WeRead returned an unexpected response shape")
    if payload.get("upgrade_info"):
        info = payload["upgrade_info"]
        message = info.get("message") if isinstance(info, dict) else str(info)
        raise WeReadError(f"WeRead skill upgrade required: {message}")
    if payload.get("errcode") not in (None, 0):
        raise WeReadError(
            f"WeRead API error {payload.get('errcode')}: "
            f"{payload.get('errmsg') or payload.get('message') or 'unknown error'}"
        )
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def search_books(title: str) -> list[dict[str, Any]]:
    result = gateway("/store/search", keyword=title, scope=10)
    books_by_id: dict[str, dict[str, Any]] = {}
    for group in result.get("results", []) or []:
        for item in group.get("books", []) or []:
            info = item.get("bookInfo") or {}
            if info.get("bookId"):
                books_by_id[str(info["bookId"])] = info
    return list(books_by_id.values())


def resolve_book_id(title: str) -> str:
    books = search_books(title)
    exact = [book for book in books if str(book.get("title", "")).strip() == title.strip()]
    candidates = exact or books
    if len(candidates) == 1:
        return str(candidates[0]["bookId"])
    if not candidates:
        raise WeReadError(f'No WeRead book found for "{title}"')
    preview = "; ".join(
        f'{book.get("title", "?")} — {book.get("author", "?")} '
        f'[{book.get("bookId", "?")}]'
        for book in candidates[:8]
    )
    raise WeReadError(
        "The title is ambiguous. Re-run with --book-id after selecting one: " + preview
    )


def fetch_all_reviews(book_id: str) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    synckey = 0
    seen_cursors: set[int] = set()
    while True:
        page = gateway("/review/list/mine", bookid=book_id, synckey=synckey, count=100)
        for wrapper in page.get("reviews", []) or []:
            review = wrapper.get("review") if isinstance(wrapper, dict) else None
            if isinstance(review, dict):
                reviews.append(review)
        if not page.get("hasMore"):
            break
        next_cursor = int(page.get("synckey") or 0)
        if next_cursor == synckey or next_cursor in seen_cursors:
            raise WeReadError("Review pagination cursor repeated; stopped to avoid a loop")
        seen_cursors.add(next_cursor)
        synckey = next_cursor
    return reviews


def chapter_maps(*chapter_lists: Any) -> tuple[dict[str, str], dict[str, int]]:
    titles: dict[str, str] = {}
    indexes: dict[str, int] = {}
    for chapters in chapter_lists:
        for chapter in chapters or []:
            uid = chapter.get("chapterUid")
            if uid is None:
                continue
            key = str(uid)
            titles[key] = str(chapter.get("title") or "未标注章节")
            if chapter.get("chapterIdx") is not None:
                indexes[key] = int(chapter["chapterIdx"])
    return titles, indexes


def normalize_sources(
    highlights_payload: dict[str, Any],
    reviews: list[dict[str, Any]],
    chapter_payload: dict[str, Any],
    popular_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    chapter_titles, chapter_indexes = chapter_maps(
        chapter_payload.get("chapters"), highlights_payload.get("chapters"),
        (popular_payload or {}).get("chapters"),
    )
    sources: list[dict[str, Any]] = []

    for index, item in enumerate(highlights_payload.get("updated", []) or []):
        raw_id = item.get("bookmarkId") or f"index-{index}"
        uid = item.get("chapterUid")
        uid_key = str(uid) if uid is not None else ""
        sources.append(
            {
                "id": f"h:{raw_id}",
                "type": "highlight",
                "chapter_uid": uid,
                "chapter_index": chapter_indexes.get(uid_key),
                "chapter_title": chapter_titles.get(uid_key, "未标注章节"),
                "text": str(item.get("markText") or "").strip(),
                "range": item.get("range"),
                "created_at": item.get("createTime"),
            }
        )

    for index, review in enumerate(reviews):
        raw_id = review.get("reviewId") or f"index-{index}"
        uid = review.get("chapterUid")
        uid_key = str(uid) if uid is not None else ""
        sources.append(
            {
                "id": f"r:{raw_id}",
                "type": "reader_review",
                "chapter_uid": uid,
                "chapter_index": review.get("chapterIdx") or chapter_indexes.get(uid_key),
                "chapter_title": review.get("chapterName")
                or chapter_titles.get(uid_key, "全书或未标注章节"),
                "text": str(review.get("content") or "").strip(),
                "abstract": str(review.get("abstract") or "").strip(),
                "range": review.get("range"),
                "created_at": review.get("createTime"),
            }
        )

    if popular_payload:
        for index, item in enumerate(popular_payload.get("items", []) or []):
            raw_id = item.get("bookmarkId") or f"index-{index}"
            uid = item.get("chapterUid")
            uid_key = str(uid) if uid is not None else ""
            sources.append(
                {
                    "id": f"p:{raw_id}",
                    "type": "popular_highlight",
                    "chapter_uid": uid,
                    "chapter_index": chapter_indexes.get(uid_key),
                    "chapter_title": chapter_titles.get(uid_key, "未标注章节"),
                    "text": str(item.get("markText") or "").strip(),
                    "range": item.get("range"),
                    "popularity": item.get("totalCount"),
                }
            )

    deduplicated = {source["id"]: source for source in sources}
    return [deduplicated[key] for key in sorted(deduplicated)]


def fingerprint_sources(sources: list[dict[str, Any]]) -> str:
    canonical = json.dumps(sources, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def export_book(book_id: str, include_popular: bool = False) -> dict[str, Any]:
    book = gateway("/book/info", bookId=book_id)
    chapters_payload = gateway("/book/chapterinfo", bookId=book_id)
    progress = gateway("/book/getprogress", bookId=book_id)
    highlights = gateway("/book/bookmarklist", bookId=book_id)
    reviews = fetch_all_reviews(book_id)
    popular = (
        gateway("/book/bestbookmarks", bookId=book_id, chapterUid=0, synckey=0)
        if include_popular
        else None
    )
    sources = normalize_sources(highlights, reviews, chapters_payload, popular)
    personal_sources = [source for source in sources if source["type"] != "popular_highlight"]
    covered = {
        str(source.get("chapter_uid"))
        for source in personal_sources
        if source.get("chapter_uid") is not None
    }
    chapter_count = len(chapters_payload.get("chapters", []) or [])
    return {
        "schema_version": 1,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "skill_version": SKILL_VERSION,
        "book": book,
        "chapters": chapters_payload.get("chapters", []) or [],
        "progress": progress,
        "sources": sources,
        "coverage": {
            "basis": "weread-personal-traces",
            "has_full_text": False,
            "chapter_count": chapter_count,
            "covered_chapter_count": len(covered),
            "highlight_count": sum(s["type"] == "highlight" for s in sources),
            "review_count": sum(s["type"] == "reader_review" for s in sources),
            "popular_highlight_count": sum(
                s["type"] == "popular_highlight" for s in sources
            ),
        },
        "source_fingerprint": fingerprint_sources(sources),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search WeRead electronic books")
    search.add_argument("title")

    export = subparsers.add_parser("export-book", help="Export one book's reading traces")
    group = export.add_mutually_exclusive_group(required=True)
    group.add_argument("--book-id")
    group.add_argument("--title")
    export.add_argument("--include-popular", action="store_true")
    export.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "search":
            print(json.dumps(search_books(args.title), ensure_ascii=False, indent=2))
            return 0
        book_id = args.book_id or resolve_book_id(args.title)
        bundle = export_book(book_id, include_popular=args.include_popular)
        write_json(args.output, bundle)
        print(
            f"Exported {bundle['book'].get('title', book_id)}: "
            f"{bundle['coverage']['highlight_count']} highlights, "
            f"{bundle['coverage']['review_count']} reviews -> {args.output}"
        )
        return 0
    except WeReadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
