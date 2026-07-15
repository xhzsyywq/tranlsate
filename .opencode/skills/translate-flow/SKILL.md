---
name: translate-flow
description: Use ONLY when the user asks to test translation flow, verify translation pipeline, or run translation tests. Runs the complete AutoTranslate test suite: compile checks, CLI translation, GUI smoke test, and log verification.
---

# Translation Flow Test

Run the complete AutoTranslate verification suite.

## Steps

1. **Compile check**: `python -m py_compile app/cli.py app/main.py app/core/engine.py`
2. **CLI translation test**: Run `python -m app.cli --text "Hello, world" --to zh` (reads API key from env if set)
3. **GUI headless test**: Run with `$env:QT_QPA_PLATFORM="offscreen"` to verify window constructs
4. **Log check**: Read `$env:APPDATA\AutoTranslate\logs\app.log` for errors

Report results in a table:

| Test | Status | Details |
|------|--------|---------|
| Compile | pass/fail | import errors |
| CLI translate | pass/fail | translation output |
| GUI construct | pass/fail | widget errors |
| Logs | pass/fail | ERROR/WARNING count |

Output any failures with fix suggestions.
