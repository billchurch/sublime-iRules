# Changelog

## 1.0.0 — unreleased

Requires Sublime Text 4 (build 4107+). Sublime Text 3 stays on 0.9.10.

### Added
- 81 commands and 22 events from F5's reference that were missing, including
  the BIG-IP 21.0 `JSON::*` and `SSE::*` commands and `JSON_*` / `SSE_RESPONSE`
  events.
- Completion details: description, introducing BIG-IP version, docs link.
- Event completions offered only after `when`, and opened automatically once
  `when` is completed or followed by a space; at the end of a line they
  expand to `EVENT priority 500 { }`, with Tab stops on `500` and the body.
  This replaces the old `when` snippet.
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

### Changed
- Syntax definition moved to sublime-syntax version 2.
- Command and event lists are generated from F5 clouddocs
  (`tools/irules_data`).

## 0.9.10 and earlier

See the git history.
