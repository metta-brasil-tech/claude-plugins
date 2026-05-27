"""
render_pdf.py — Chrome headless wrapper pra converter HTML em PDF.

Detecta Chrome/Edge/Chromium no PATH, cria user-data-dir isolado, roda
--headless --print-to-pdf com --no-pdf-header-footer.

Uso:
    from render_pdf import render
    render("out.html", "out.pdf")
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_chrome() -> str:
    """Detecta o binário do Chrome/Edge/Chromium."""
    candidates = []

    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            os.path.expanduser(r"~\AppData\Local\Chromium\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:  # linux
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/microsoft-edge",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    # Also try PATH lookup
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return found

    raise RuntimeError(
        "Chrome/Edge/Chromium não encontrado. Instale o Chrome ou ajuste o PATH."
    )


def _file_uri(path: Path) -> str:
    """Converte path local em file:// URI compatível com Chrome."""
    abs_path = path.resolve()
    if sys.platform == "win32":
        # Windows: file:///C:/path/to/file.html
        return "file:///" + str(abs_path).replace("\\", "/").replace(" ", "%20")
    return "file://" + str(abs_path).replace(" ", "%20")


def render(
    html_path: str | Path,
    pdf_path: str | Path,
    *,
    chrome_path: str | None = None,
    timeout: int = 120,
) -> Path:
    """Renderiza HTML em PDF via Chrome headless.

    Returns:
        Path do PDF gerado.
    """
    html_path = Path(html_path)
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    chrome = chrome_path or _find_chrome()
    html_uri = _file_uri(html_path)

    # User-data-dir isolado pra evitar conflito com Chrome do user
    user_data_dir = tempfile.mkdtemp(prefix="chrome-pdf-")

    try:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_uri,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        if not pdf_path.exists():
            raise RuntimeError(
                f"Chrome não gerou PDF.\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return pdf_path
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_pdf.py <input.html> <output.pdf>")
        sys.exit(1)
    out = render(sys.argv[1], sys.argv[2])
    print(f"PDF: {out} ({out.stat().st_size} bytes)")
