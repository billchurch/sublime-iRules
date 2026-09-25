# Contributing

## Layout

| Path | What |
| --- | --- |
| `iRule.sublime-syntax` | grammar (five variables are generated, see below) |
| `irules_plugin.py` | Sublime Text commands and listeners (thin) |
| `irules_lib/` | pure Python used by the plugin, unit-tested without Sublime |
| `tools/irules_data/` | generator for commands and events |
| `data/` | clouddocs snapshot and hand-maintained overrides |
| `tests/python/`, `tests/syntax/` | unit tests and syntax tests |

## Tests

```bash
python3 -m unittest discover -s tests/python -t .   # no dependencies
tools/syntax-tests.sh                               # needs Docker
python3 -m tools.irules_data render --check         # generated files current
```

`tools/syntax-tests.sh` downloads Sublime Text's `syntax_tests` binary
(Linux x64) once into `~/.cache` and runs it in a container.

## Developing in Sublime Text

Symlink the repository into your Packages folder as `iRules`
(macOS: `~/Library/Application Support/Sublime Text/Packages/iRules`) and
add any installed copy (`iRules` or `sublime-iRules`) to `ignored_packages`.

## Commands and events

See [docs/maintaining-data.md](docs/maintaining-data.md). Do not edit the
generated files by hand.
