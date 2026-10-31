#!/usr/bin/env python3
"""Render monospace demo text (including ANSI SGR colours) to PNG screenshots."""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Basic 16 ANSI colours (normal + bright), used for both fg and bg.
_ANSI16 = [  # One Dark-like palette: readable on a dark background.
    (40, 44, 52), (224, 108, 117), (152, 195, 121), (229, 192, 123),
    (97, 175, 239), (198, 120, 221), (86, 182, 194), (171, 178, 191),
    (92, 99, 112), (240, 128, 136), (170, 220, 140), (240, 210, 140),
    (125, 195, 255), (215, 145, 235), (110, 205, 215), (240, 242, 245),
]

_SGR = re.compile(r"\x1b\[([0-9;]*)m")
_DEFAULT_FG = (214, 218, 226)
_DEFAULT_BG = (30, 33, 40)


def _ansi256(index: int) -> tuple[int, int, int]:
    if index < 16:
        return _ANSI16[index]
    if index < 232:
        index -= 16
        r = index // 36
        g = (index % 36) // 6
        b = index % 6
        ramp = [0, 95, 135, 175, 215, 255]
        return (ramp[r], ramp[g], ramp[b])
    gray = 8 + (index - 232) * 10
    return (gray, gray, gray)


def _parse_sgr(params: list[int], state: dict) -> None:
    if not params:
        params = [0]
    i = 0
    while i < len(params):
        code = params[i]
        if code == 0:
            state["fg"] = None
            state["bg"] = None
            state["bold"] = False
        elif code == 1:
            state["bold"] = True
        elif code == 22:
            state["bold"] = False
        elif code == 39:
            state["fg"] = None
        elif code == 49:
            state["bg"] = None
        elif 30 <= code <= 37:
            state["fg"] = _ANSI16[code - 30]
        elif 90 <= code <= 97:
            state["fg"] = _ANSI16[code - 90 + 8]
        elif 40 <= code <= 47:
            state["bg"] = _ANSI16[code - 40]
        elif 100 <= code <= 107:
            state["bg"] = _ANSI16[code - 100 + 8]
        elif code in (38, 48):
            is_bg = code == 48
            if i + 1 < len(params) and params[i + 1] == 5 and i + 2 < len(params):
                color = _ansi256(params[i + 2])
                i += 2
                if is_bg:
                    state["bg"] = color
                else:
                    state["fg"] = color
            elif i + 1 < len(params) and params[i + 1] == 2 and i + 4 < len(params):
                color = (params[i + 2], params[i + 3], params[i + 4])
                i += 4
                if is_bg:
                    state["bg"] = color
                else:
                    state["fg"] = color
        i += 1


def _segments(line: str) -> list[tuple[str, dict]]:
    """Split a line into (text, style_state) runs."""
    state = {"fg": None, "bg": None, "bold": False}
    out: list[tuple[str, dict]] = []
    pos = 0
    for match in _SGR.finditer(line):
        if match.start() > pos:
            out.append((line[pos:match.start()], dict(state)))
        raw = match.group(1)
        params = [int(p) for p in raw.split(";") if p != ""] if raw else [0]
        _parse_sgr(params, state)
        pos = match.end()
    if pos < len(line) or not out:
        out.append((line[pos:], dict(state)))
    return out


def _load_font(size: int = 14):
    from PIL import ImageFont

    for candidate in (
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/LiberationMono-Regular.ttf",
    ):
        p = Path(candidate)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()


def render(text: str, out_path: Path, title: str = "", size: int = 26) -> None:
    """
    Draw ``text`` on a fixed character grid.

    Every glyph sits in its own cell of ``advance`` x ``line_h`` pixels, with
    ``line_h`` equal to the font's ascent + descent, so box-drawing characters
    join into continuous rules instead of leaving gaps between lines.
    """
    from PIL import Image, ImageDraw

    font = _load_font(size)
    raw_lines = text.replace("\t", "    ").splitlines() or [""]
    lines: list[str] = []
    if title:
        lines.extend([title, "=" * len(title), ""])
    lines.extend(raw_lines)

    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    advance = round(font.getlength("M"))
    pad = size

    columns = max((len(_SGR.sub("", ln)) for ln in lines), default=0)
    width = columns * advance + pad * 2
    height = len(lines) * line_h + pad * 2
    img = Image.new("RGB", (width, height), _DEFAULT_BG)
    draw = ImageDraw.Draw(img)

    y = pad
    for ln in lines:
        x = pad
        for chunk, style in _segments(ln):
            fg = style["fg"] or _DEFAULT_FG
            if style["bold"] and style["fg"] is None:
                fg = (250, 250, 250)
            bg = style["bg"]
            for ch in chunk:
                if bg is not None:
                    draw.rectangle([x, y, x + advance - 1, y + line_h - 1], fill=bg)
                if not ch.isspace():
                    draw.text((x, y), ch, font=font, fill=fg)
                x += advance
        y += line_h

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, optimize=True)
    print(f"wrote {out_path} {img.size}")


def main(src_dir: str, dst_dir: str):
    src = Path(src_dir)
    dst = Path(dst_dir)
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob("*.txt")):
        render(
            f.read_text(encoding="utf-8", errors="replace"),
            dst / (f.stem + ".png"),
            title=f.stem,
        )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
