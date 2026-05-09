# Mental Load

A zero-dependency CLI for tracking cognitive load.

### Details

- **Zero Friction:** No questions asked. Just dump and move on.
- **Auto-Detect:** Fuzziness is detected from your language. Weight defaults to 5.
- **Visibility:** Larger blocks = heavier mental drain. `[?]` = fuzzy/unclear thoughts.

### Examples

```bash
./main.py add "maybe I should fix the sink" -w 3
./main.py map       # Visual dashboard of entries
./main.py summary   # Theme & fragmentation analysis of entries
./main.py list      # List of entries with IDs
```

### Commands

- `add <thought> [-w 1-10]`
- `map` | `summary` | `list`
- `ignore <words>` | `clear <id>` | `reset`

### Storage

Data is saved locally in `load.json` which is created automatically after your first entry.
