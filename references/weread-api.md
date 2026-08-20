# WeRead API subset

Use the companion `weread-skills` documentation as the authority. This file records only the subset needed by this compiler.

## Gateway

- Endpoint: `POST https://i.weread.qq.com/api/agent/gateway`
- Header: `Authorization: Bearer $WEREAD_API_KEY`
- JSON body: keep all business parameters at the top level.
- Add `"skill_version": "1.0.4"` to every request.
- If a response contains `upgrade_info`, stop and follow its upgrade message before retrying.
- If `errcode` is nonzero, treat the call as failed. Never invent missing data.

## Required calls

| Purpose | API | Key rules |
|---|---|---|
| Resolve title | `/store/search` | Pass `scope=10`; response group scope may differ. |
| Book metadata | `/book/info` | Pass `bookId`. |
| Chapters | `/book/chapterinfo` | Use `chapterUid` as the stable chapter anchor. |
| Progress | `/book/getprogress` | `progress` is 0-100; only 100 means finished. Time is seconds. |
| Highlights | `/book/bookmarklist` | Returns personal highlights, not bookmark contents. |
| Personal reviews | `/review/list/mine` | Parameter is lowercase `bookid`; paginate with returned `synckey`. |
| Notebook list | `/user/notebooks` | Paginate with the final row's `sort` as top-level `lastSort`. |
| Popular highlights | `/book/bestbookmarks` | Optional; fixed top 20 and not personal evidence. |

## Evidence semantics

- `noteCount` means personal highlight count, not total note count.
- Total note count is `reviewCount + noteCount + bookmarkCount`.
- Exportable personal content is highlights plus reviews; bookmark contents are not available.
- `review.abstract` is conditional. When present, it is the original excerpt associated with the reader's thought.
- Popular highlights and public comments must remain separate from the reader's own evidence.
- Convert timestamps only for display. Preserve the numeric timestamp in the private JSON bundle.

## Privacy

Never print or persist `WEREAD_API_KEY`. Do not accept the key as a CLI argument. Keep exported bundles in a private working directory and delete them when the user no longer needs them.
