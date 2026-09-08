from __future__ import annotations

import re
import sys
from pathlib import Path


def patch_main(repo: Path) -> Path:
    main_path = repo / "backend" / "main.py"
    if not main_path.is_file():
        raise SystemExit(f"backend/main.py not found: {main_path}")

    text = main_path.read_text(encoding="utf-8-sig")

    if "from fastapi.staticfiles import StaticFiles" not in text:
        anchor = "from fastapi.responses import FileResponse, JSONResponse\n"
        if anchor not in text:
            raise SystemExit("Could not find FastAPI response import in backend/main.py")
        text = text.replace(anchor, anchor + "from fastapi.staticfiles import StaticFiles\n", 1)

    if "AETHERVOICE_FRONTEND_DIR" not in text:
        logger_anchor = 'logger = get_logger("main")\n'
        insert = (
            'logger = get_logger("main")\n\n'
            'AETHERVOICE_FRONTEND_DIR = os.path.join(\n'
            '    os.path.dirname(__file__), "app", "static", "aethervoice"\n'
            ')\n'
            'AETHERVOICE_ASSETS_DIR = os.path.join(AETHERVOICE_FRONTEND_DIR, "assets")\n'
        )
        if logger_anchor not in text:
            raise SystemExit("Could not find logger initialization in backend/main.py")
        text = text.replace(logger_anchor, insert, 1)

    if 'name="aethervoice-assets"' not in text:
        cors_marker = "app.add_middleware(\n"
        start = text.find(cors_marker)
        if start == -1:
            raise SystemExit("Could not find CORS middleware block")
        end = text.find("\n)\n", start)
        if end == -1:
            raise SystemExit("Could not locate end of CORS middleware block")
        end += len("\n)\n")
        mount_block = (
            "\n# AetherVoice React build assets. The directory is created by build_frontend.ps1.\n"
            "if os.path.isdir(AETHERVOICE_ASSETS_DIR):\n"
            "    app.mount(\n"
            "        \"/assets\",\n"
            "        StaticFiles(directory=AETHERVOICE_ASSETS_DIR),\n"
            "        name=\"aethervoice-assets\",\n"
            "    )\n"
        )
        text = text[:end] + mount_block + text[end:]

    root_start = text.find('@app.get("/", tags=["Frontend"], include_in_schema=False)')
    legacy_start = text.find('@app.get("/legacy-dashboard"', root_start) if root_start != -1 else -1

    replacement = '''@app.get("/", tags=["Frontend"], include_in_schema=False)
async def serve_integrated_frontend():
    aethervoice_index = os.path.join(AETHERVOICE_FRONTEND_DIR, "index.html")
    if os.path.exists(aethervoice_index):
        return FileResponse(aethervoice_index)

    legacy_integrated = os.path.join(
        os.path.dirname(__file__), "app", "static", "integrated.html"
    )
    if os.path.exists(legacy_integrated):
        return FileResponse(legacy_integrated)

    return {"message": "AetherVoice frontend missing. Visit /docs for API documentation."}


'''

    if root_start != -1 and legacy_start != -1:
        text = text[:root_start] + replacement + text[legacy_start:]
    elif "AetherVoice frontend missing" not in text:
        raise SystemExit("Could not safely replace the current root frontend route")

    if '@app.get("/favicon.svg"' not in text:
        legacy_marker = '@app.get("/legacy-dashboard", tags=["Frontend"], include_in_schema=False)\n'
        pos = text.find(legacy_marker)
        if pos == -1:
            raise SystemExit("Could not find legacy dashboard route")
        routes = '''@app.get("/favicon.svg", tags=["Frontend"], include_in_schema=False)
async def serve_aethervoice_favicon():
    path = os.path.join(AETHERVOICE_FRONTEND_DIR, "favicon.svg")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"detail": "favicon not found"})


@app.get("/live-analysis", tags=["Frontend"], include_in_schema=False)
@app.get("/voice-lab", tags=["Frontend"], include_in_schema=False)
@app.get("/threat-intelligence", tags=["Frontend"], include_in_schema=False)
@app.get("/reports", tags=["Frontend"], include_in_schema=False)
@app.get("/settings", tags=["Frontend"], include_in_schema=False)
async def serve_aethervoice_spa_route():
    path = os.path.join(AETHERVOICE_FRONTEND_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"detail": "AetherVoice frontend not built"})


'''
        text = text[:pos] + routes + text[pos:]

    main_path.write_text(text, encoding="utf-8", newline="\n")
    return main_path


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    path = patch_main(repo)
    print(f"Patched: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
