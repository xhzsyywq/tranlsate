---
name: package-exe
description: Use ONLY when the user asks to package or build the exe, create installer, or deploy. Packages AutoTranslate into a standalone Windows .exe using PyInstaller.
---

# Package AutoTranslate to Windows .exe

## Steps

1. **Install PyInstaller** (if needed): `pip install pyinstaller`
2. **Clean old builds**: Remove `build/` and `dist/` directories
3. **Run PyInstaller**:

```powershell
pyinstaller --onefile --windowed --name AutoTranslate `
  --add-data "app;app" `
  --hidden-import rapidocr_onnxruntime `
  --hidden-import PySide6 `
  --hidden-import keyboard `
  --hidden-import mss `
  --hidden-import python-docx `
  --hidden-import pypdf `
  --hidden-import PIL `
  --hidden-import httpx `
  --hidden-import pydantic `
  app/main.py
```

4. **Verify**: Check `dist/AutoTranslate.exe` exists and is > 10 MB
5. **Test run**: Launch the exe briefly to confirm no import errors

Report the build result: file size, any warnings, and whether the exe starts.
