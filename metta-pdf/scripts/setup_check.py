"""
setup_check.py — valida ambiente antes de rodar o pipeline metta-pdf.

Checks:
  1. Python 3.11+
  2. python-docx instalado
  3. Jinja2 instalado
  4. Chrome / Edge / Chromium acessível
  5. nano-banana CLI no PATH
  6. GEMINI_API_KEY definida

Exit code 0 = tudo OK. 1 = pelo menos 1 problema.

Uso:
  python setup_check.py
  python setup_check.py --quiet   # sai 0/1 sem prints
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
from pathlib import Path


# UTF-8 stdout no Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[90m"
RESET = "\033[0m"


def _supports_color() -> bool:
    if "--no-color" in sys.argv:
        return False
    return sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"


COLOR = _supports_color()


def _ok(msg: str) -> None:
    if COLOR:
        print(f"  {GREEN}✓{RESET} {msg}")
    else:
        print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    if COLOR:
        print(f"  {YELLOW}⚠{RESET} {msg}")
    else:
        print(f"  [WARN] {msg}")


def _fail(msg: str) -> None:
    if COLOR:
        print(f"  {RED}✘{RESET} {msg}")
    else:
        print(f"  [FAIL] {msg}")


def _dim(msg: str) -> None:
    if COLOR:
        print(f"    {DIM}{msg}{RESET}")
    else:
        print(f"    {msg}")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_python() -> bool:
    version = sys.version_info
    if version >= (3, 11):
        _ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    _fail(f"Python {version.major}.{version.minor} encontrado — precisa 3.11+")
    _dim("Instalar Python 3.11+ via https://python.org/downloads/")
    return False


def check_python_docx() -> bool:
    try:
        import docx  # type: ignore[import-not-found]  # noqa: F401
        # python-docx tem version interna
        import docx as _docx  # type: ignore[import-not-found]
        ver = getattr(_docx, "__version__", "?")
        _ok(f"python-docx {ver}")
        return True
    except ImportError:
        _fail("python-docx não instalado")
        _dim("pip install python-docx")
        return False


def check_jinja2() -> bool:
    try:
        import jinja2  # type: ignore[import-not-found]
        _ok(f"Jinja2 {jinja2.__version__}")
        return True
    except ImportError:
        _fail("Jinja2 não instalado")
        _dim("pip install Jinja2")
        return False


def check_chrome() -> bool:
    candidates = []
    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    for p in candidates:
        if os.path.isfile(p):
            name = Path(p).stem
            _ok(f"Browser: {name} ({p})")
            return True

    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            _ok(f"Browser: {name} ({found})")
            return True

    _fail("Chrome / Edge / Chromium não encontrado")
    _dim("Instalar Chrome: https://www.google.com/chrome/")
    return False


def check_nano_banana() -> tuple[bool, bool]:
    """Returns (found, needs_warning)."""
    # Aceita .exe, .cmd nativos ou shebang script (Git Bash no Windows)
    candidates = [
        os.path.expanduser("~/AppData/Roaming/npm/nano-banana.cmd"),
        os.path.expanduser("~/AppData/Roaming/npm/nano-banana.exe"),
        os.path.expanduser("~/.local/bin/nano-banana.cmd"),
        os.path.expanduser("~/.local/bin/nano-banana.exe"),
        os.path.expanduser("~/.local/bin/nano-banana"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            _ok(f"nano-banana CLI ({p})")
            return True, False

    found = shutil.which("nano-banana")
    if found:
        _ok(f"nano-banana CLI ({found})")
        return True, False

    _warn("nano-banana CLI não encontrada — geração de imagens ficará indisponível")
    _dim("Sprint 1 (sem imagens) ainda funciona. Pra Sprint 2+:")
    _dim("  Opção A — instalar via wrapper local (Git Bash):")
    _dim("    git clone <repo nano-banana-2> ~/tools/nano-banana-2 && ln -sf ~/tools/nano-banana-2/cli ~/.local/bin/nano-banana")
    _dim("  Opção B — npm global (se vier do npm): npm i -g nano-banana")
    return False, True


def check_gemini_key() -> bool:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        masked = f"{key[:4]}...{key[-4:]}" if len(key) >= 12 else "***"
        _ok(f"GEMINI_API_KEY definida ({masked})")
        return True
    _warn("GEMINI_API_KEY não definida — geração de imagens ficará indisponível")
    _dim("Obter key: https://aistudio.google.com/apikey")
    _dim("Definir (PowerShell):  $env:GEMINI_API_KEY = 'sua-key-aqui'")
    _dim("Definir (Bash):        export GEMINI_API_KEY='sua-key-aqui'")
    return False


def check_bash() -> bool:
    """Bash é necessário no Windows pra wrap shebang scripts (nano-banana)."""
    if sys.platform != "win32":
        return True  # Linux/Mac já têm bash nativo
    for p in [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ]:
        if os.path.isfile(p):
            _ok(f"Git Bash ({p})")
            return True
    found = shutil.which("bash")
    if found:
        _ok(f"bash ({found})")
        return True
    _warn("bash não encontrado — necessário se nano-banana for shebang script")
    _dim("Instalar Git for Windows: https://git-scm.com/download/win")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    quiet = "--quiet" in sys.argv

    if not quiet:
        print()
        print("metta-pdf · setup check")
        print()
        print("Core (Sprint 1 — pipeline básico sem imagens):")

    core = [
        check_python(),
        check_python_docx(),
        check_jinja2(),
        check_chrome(),
    ]
    core_ok = all(core)

    if not quiet:
        print()
        print("Imagens AI (Sprint 2+ — opcional pra começar):")

    has_nb, _ = check_nano_banana()
    has_key = check_gemini_key()
    check_bash()  # informativo

    if not quiet:
        print()
        print("Status:")
        if core_ok and has_nb and has_key:
            if COLOR:
                print(f"  {GREEN}✓ Tudo pronto.{RESET} Pode rodar `metta-pdf build <brief>`.")
            else:
                print("  ✓ Tudo pronto. Pode rodar `metta-pdf build <brief>`.")
        elif core_ok:
            if COLOR:
                print(f"  {YELLOW}⚠ Core OK, mas imagens AI indisponíveis.{RESET}")
            else:
                print("  ⚠ Core OK, mas imagens AI indisponíveis.")
            print("    Use `--skip-images` por enquanto. PDFs ficam com placeholders.")
        else:
            if COLOR:
                print(f"  {RED}✘ Pipeline não vai rodar.{RESET} Resolver os itens acima primeiro.")
            else:
                print("  ✘ Pipeline não vai rodar. Resolver os itens acima primeiro.")
        print()

    return 0 if core_ok else 1


if __name__ == "__main__":
    sys.exit(main())
