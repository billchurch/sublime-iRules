# Changelog

## 1.0.0 — 2026-09-25

Requires Sublime Text 4 (build 4107+). Sublime Text 3 stays on 0.9.10.

### Added
- 81 commands and 22 events from F5's reference that were missing, including
  the BIG-IP 21.0 `JSON::*` and `SSE::*` commands and `JSON_*` / `SSE_RESPONSE`
  events.
- Completion details: description, introducing BIG-IP version, docs link.
- Event completions offered only after `when`, and opened automatically once
  `when` is completed or followed by a space; at the end of a line they
  expand to `EVENT priority 500 { }`, with Tab stops on `500` and the body.
  The `when` snippet now inserts `when ` and opens the event list, and words
  that have a snippet no longer also appear as plain completions.
- Format selection; format on save (`format_on_save`); indentation follows the
  view's tab settings.
- `.irules` file extension; indentation rules; `ife` and `ifei` snippets.

### Fixed
- An unknown event after `when` no longer breaks highlighting for the rest of
  the file.
- `{abc}` brace strings were highlighted as code blocks.
- `LSN::inbound-entry` and similar names were only partly highlighted.
- `ROUTE::age` and `QOE_PARSE_DONE` were wrongly marked deprecated.
- Formatter: one-line blocks such as `if {$a} { set x 1 }` no longer dedent
  the following lines; multi-line strings and same-line braced payloads are
  left untouched; brackets inside braced regexes no longer shift indentation.
- Formatter crashed on line continuations (NameError).
- `regexp` / `regsub` with `--` and a variable pattern highlighted the whole
  following block as a regex.
- A bare `when` at the end of a line no longer marks the next line's first
  word as an unknown event.
- The plugin no longer unloads itself after a package upgrade (stale
  `irules_lib` modules made its import fail until Sublime was restarted).

### Changed
- Syntax definition moved to sublime-syntax version 2.
- Command and event lists are generated from F5 clouddocs
  (`tools/irules_data`).

## 0.9.10 and earlier

See the git history.
