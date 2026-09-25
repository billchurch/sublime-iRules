# Maintaining the iRules data

Commands and events come from F5's reference at
https://clouddocs.f5.com/api/irules/. Three generated files are built from it:

| File | What is generated |
| --- | --- |
| `iRule.sublime-syntax` | the five `most_likely_irule_*` / `deprecated_irule_*` variables only |
| `Completions/iRules-commands.sublime-completions` | the whole file |
| `irules_lib/events.py` | the whole file |

Never edit those by hand. Edit `data/overrides.json` and re-render.

## Refresh from F5

```bash
python3 -m tools.irules_data fetch    # rewrites data/clouddocs.json
python3 -m tools.irules_data render   # rewrites the generated files
tools/syntax-tests.sh
python3 -m unittest discover -s tests/python -t .
```

The weekly **F5 docs drift** workflow fails when clouddocs changes. Its log
lists the added and removed names.

## data/overrides.json

| Key | Use it when |
| --- | --- |
| `commands.add` / `events.add` | a real command or event is missing from clouddocs |
| `commands.deprecate` / `events.deprecate` | clouddocs does not mark something deprecated |
| `commands.exclude` / `events.exclude` | clouddocs lists something that is not a command or event |
| `commands.rename` / `events.rename` | clouddocs misspells a name |
| `syntax_skip` | the grammar handles a command with its own rule |
| `tcl_completions` | Tcl built-ins to offer as completions |
| `completions_extra` | hand-written completion snippets, copied verbatim |

`render` stops with an error, naming the override to fix, when:

- an override has gone stale: an `add` entry F5 has since documented, or an
  `exclude`, `rename` or `deprecate` entry for a name that no longer exists;
- a `rename` would overwrite a name F5 already documents;
- a generated list would be empty;
- a name matched earlier by the grammar would hide part of a later one (for
  example a deprecated `LSN::inbound` in front of a valid `LSN::inbound-entry`).

`fetch` refuses a snapshot that lost more than 10% of its entries, which
usually means F5 changed the page markup. It exits with status 3, not 1,
when clouddocs cannot be reached, so the weekly drift job's log shows a
network problem rather than a docs change.
