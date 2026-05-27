"""
generate_images.py — wrapper do nano-banana CLI pra gerar N imagens em paralelo.

Recebe lista de pontos editoriais (do suggest_images.py) e roda nano-banana CLI
em background pra cada um. Retry com prompt encurtado quando dá timeout.

Uso:
    from generate_images import generate_all
    results = generate_all(points, output_dir="output/img", verbose=True)
"""
from __future__ import annotations

import io
import os
import re
import shlex
import shutil
import subprocess
import sys
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _find_nano_banana() -> tuple[str, bool]:
    """Localiza o binário do nano-banana CLI.

    Returns:
        (path, needs_bash_wrapper) — needs_bash_wrapper=True quando o "binário"
        é um shebang script bash (Git Bash no Windows). Nesse caso a chamada vai
        via `bash -c "<cli> <args>"`.
    """
    # No Windows, preferir .cmd / .exe nativos antes de scripts shebang
    win_native_candidates = [
        os.path.expanduser("~/AppData/Roaming/npm/nano-banana.cmd"),
        os.path.expanduser("~/AppData/Roaming/npm/nano-banana.exe"),
        os.path.expanduser("~/.local/bin/nano-banana.cmd"),
        os.path.expanduser("~/.local/bin/nano-banana.exe"),
    ]
    if sys.platform == "win32":
        for p in win_native_candidates:
            if os.path.isfile(p):
                return p, False

    # Shebang script bash (Git Bash, WSL, Linux, macOS)
    script_candidates = [
        os.path.expanduser("~/.local/bin/nano-banana"),
        os.path.expanduser("~/AppData/Roaming/npm/nano-banana"),
    ]
    for p in script_candidates:
        if os.path.isfile(p):
            needs_bash = sys.platform == "win32" and _is_shebang_script(p)
            return p, needs_bash

    # PATH lookup
    found = shutil.which("nano-banana")
    if found:
        needs_bash = sys.platform == "win32" and _is_shebang_script(found)
        return found, needs_bash

    raise RuntimeError(
        "nano-banana CLI não encontrada. Instale ou ajuste o PATH."
    )


def _is_shebang_script(path: str) -> bool:
    """Verifica se o arquivo começa com #! (shebang)."""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"#!"
    except OSError:
        return False


def _find_bash() -> str:
    """Localiza bash no Windows pra rodar shebang scripts."""
    candidates = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\bash.exe"),
        "/usr/bin/bash",
        "/bin/bash",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    found = shutil.which("bash")
    if found:
        return found
    raise RuntimeError("bash não encontrado pra wrapping de scripts shebang.")


def _shorten_prompt(prompt: str, max_chars: int = 800) -> str:
    """Reduz prompt mantendo as primeiras instruções e o negative no fim."""
    # Quebra na primeira frase + remove modifiers extras
    if len(prompt) <= max_chars:
        return prompt
    # Mantém setup das ~6 primeiras sentenças + última (negative)
    sentences = re.split(r"(?<=[.!?])\s+", prompt)
    keep_start = sentences[:6]
    keep_end = sentences[-2:] if "Avoid" in sentences[-1] else []
    return " ".join(keep_start + keep_end)


def _run_nano_banana(
    cli: str,
    needs_bash: bool,
    prompt: str,
    output_dir: Path,
    filename: str,
    aspect: str,
    size: str,
    timeout: int = 180,
    model: str = "flash",
) -> tuple[bool, str]:
    """Chama nano-banana CLI uma vez. Returns (success, message)."""
    # Strip .jpeg extension — CLI adds it
    output_stem = filename.rsplit(".", 1)[0]

    if needs_bash:
        # Wrap como bash -c "cli '<prompt>' -o ... -s ..."
        bash = _find_bash()
        # Escape o prompt (já é texto livre — escapar aspas internas)
        bash_cmd = (
            f'"{cli}" {shlex.quote(prompt)} '
            f'-o {shlex.quote(output_stem)} '
            f'-s {shlex.quote(size)} '
            f'-a {shlex.quote(aspect)} '
            f'-m {shlex.quote(model)} '
            f'-d {shlex.quote(str(output_dir))}'
        )
        cmd = [bash, "-c", bash_cmd]
    else:
        cmd = [
            cli,
            prompt,
            "-o", output_stem,
            "-s", size,
            "-a", aspect,
            "-m", model,
            "-d", str(output_dir),
        ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        # Check if file was created
        expected = output_dir / filename
        # nano-banana saves .jpeg by default; check common extensions
        for ext in (".jpeg", ".jpg", ".png"):
            candidate = output_dir / f"{output_stem}{ext}"
            if candidate.exists():
                # Normalize to .jpeg
                final = output_dir / filename
                if candidate != final:
                    candidate.rename(final)
                return True, str(final)
        return False, f"file not created. stderr: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        return False, f"exception: {exc}"


def _generate_one(point: dict[str, Any], output_dir: Path, cli: str, needs_bash: bool, verbose: bool = True, stagger: float = 0) -> dict[str, Any]:
    """Gera 1 imagem com retry. Trata timeout (retry com prompt curto) e 503 (backoff exponencial)."""
    name = point["section_title"][:40]
    layout = point["layout"]

    # Stagger inicial pra evitar burst no Gemini
    if stagger > 0:
        time.sleep(stagger + random.uniform(0, 2))

    if verbose:
        print(f"  [⟳] {name} ({layout})... ", flush=True)

    def try_once(prompt: str, timeout: int) -> tuple[bool, str]:
        return _run_nano_banana(
            cli=cli, needs_bash=needs_bash, prompt=prompt,
            output_dir=output_dir, filename=point["filename"],
            aspect=point["aspect"], size=point["size"], timeout=timeout,
        )

    # 1ª tentativa: prompt completo
    ok, msg = try_once(point["prompt"], 180)
    if ok:
        if verbose:
            print(f"  [✓] {name} → {point['filename']}", flush=True)
        return {**point, "status": "ok", "path": msg}

    # 503 (servidor sobrecarregado) → backoff e retry com prompt completo
    if "503" in msg or "overload" in msg.lower():
        for attempt, wait in enumerate([5, 15, 30], 1):
            if verbose:
                print(f"  [⚠] {name} 503 overload. Backoff {wait}s (tentativa {attempt}/3)...", flush=True)
            time.sleep(wait + random.uniform(0, 3))
            ok, msg = try_once(point["prompt"], 180)
            if ok:
                if verbose:
                    print(f"  [✓] {name} → {point['filename']} (após backoff)", flush=True)
                return {**point, "status": f"ok-after-backoff-{attempt}", "path": msg}
            if "503" not in msg and "overload" not in msg.lower():
                break  # outro erro — não insistir

    # Timeout → retry com prompt encurtado
    if "timeout" in msg.lower():
        if verbose:
            print(f"  [⚠] {name} timeout. Retry com prompt curto...", flush=True)
        short_prompt = _shorten_prompt(point["prompt"], max_chars=600)
        ok, msg = try_once(short_prompt, 180)
        if ok:
            if verbose:
                print(f"  [✓] {name} → {point['filename']} (retry curto)", flush=True)
            return {**point, "status": "ok-retry", "path": msg}

    # Falha final — retorna placeholder
    if verbose:
        print(f"  [✘] {name} FAILED ({msg[:80]})", flush=True)
    return {**point, "status": "failed", "error": msg, "path": None}


def generate_all(
    points: list[dict[str, Any]],
    output_dir: str | Path,
    max_workers: int = 2,
    verbose: bool = True,
    cli_path: str | None = None,
) -> list[dict[str, Any]]:
    """Gera N imagens em paralelo.

    Returns:
        Lista parallela ao input com {**point, status, path|error}.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if cli_path:
        cli, needs_bash = cli_path, sys.platform == "win32" and _is_shebang_script(cli_path)
    else:
        cli, needs_bash = _find_nano_banana()

    if verbose:
        wrap = " (via bash wrapper)" if needs_bash else ""
        print(f"\nGerando {len(points)} imagens em paralelo (max {max_workers} workers) via {cli}{wrap}\n", flush=True)

    results: list[dict[str, Any]] = [None] * len(points)  # type: ignore[list-item]

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # Stagger inicial pra primeiras N (max_workers) launches dentro de uma janela
        futures = {
            pool.submit(_generate_one, point, output_dir, cli, needs_bash, verbose, i * 1.5): i
            for i, point in enumerate(points)
        }
        for fut in as_completed(futures):
            i = futures[fut]
            results[i] = fut.result()

    if verbose:
        ok_count = sum(1 for r in results if r["status"].startswith("ok"))
        fail_count = sum(1 for r in results if r["status"] == "failed")
        print(f"\n  {ok_count}/{len(points)} imagens geradas. {fail_count} falhas.", flush=True)

    return results


def image_map_from_results(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Converte resultados em image_map pro render_html.py.

    Chaves por layout:
      - cover           → {src}
      - opener-spread   → {src, alt, badge}
      - hero-strip      → {src, alt, label, caption}
      - profile-spread  → {src, alt, badge, caption}
      - quote-photo     → {src}
    """
    m: dict[str, dict[str, Any]] = {}
    for r in results:
        if not r["status"].startswith("ok"):
            continue

        title = r.get("section_title", "")
        layout = r["layout"]
        src = f"img/{Path(r['path']).name}"

        if layout == "cover":
            m["__cover__"] = {"src": src}
        elif layout == "opener-spread":
            m[title] = {
                "src": src,
                "alt": title,
                "badge": r.get("badge", "Em ação"),
            }
        elif layout == "hero-strip":
            m[title] = {
                "src": src,
                "alt": title,
                "label": r.get("badge", "Leia a cena"),
                "caption": _hero_caption_for(title),
            }
        elif layout == "profile-spread":
            m[title] = {
                "src": src,
                "alt": title,
                "badge": r.get("badge", "Perfil"),
                "caption": _profile_caption_for(title),
            }
        elif layout == "quote-photo":
            m[title] = {"src": src}
        else:
            m[title] = {"src": src, "alt": title}

    return m


def _hero_caption_for(title: str) -> str:
    t = title.lower()
    if "visualiz" in t or "ler" in t or "cen" in t:
        return "Cada cliente entra com um contexto diferente — o profissional 4.0 capta antes de abordar."
    if "perfil" in t:
        return "Adapte a abordagem ao perfil de quem chega."
    return ""


def _profile_caption_for(title: str) -> str:
    t = title.lower()
    if "caminhone" in t and "autonom" in t:
        return "Dono do caminhão — patrimônio dele"
    if "carro particular" in t or "executivo" in t:
        return "Executivo em trânsito — pouco tempo"
    if "frota" in t:
        return "Procedimento e política da empresa"
    return ""


if __name__ == "__main__":
    import json
    from parse_brief import parse
    from select_layout import classify_sections
    from suggest_images import suggest

    if len(sys.argv) < 3:
        print("Usage: generate_images.py <brief.docx|brief.md> <output_dir> [--setor='descrição']")
        sys.exit(1)

    brief = sys.argv[1]
    out_dir = sys.argv[2]
    setor = "a Brazilian workplace"
    for arg in sys.argv[3:]:
        if arg.startswith("--setor="):
            setor = arg.split("=", 1)[1]

    secs = parse(brief)
    enriched = classify_sections(secs)
    points = suggest(enriched, brief_context={"setor": setor})

    results = generate_all(points, output_dir=out_dir, verbose=True)

    print("\nResults:")
    for r in results:
        status_icon = "✓" if r["status"].startswith("ok") else "✘"
        print(f"  {status_icon} {r['section_title'][:50]:<50}  {r['filename']}  ({r['status']})")
