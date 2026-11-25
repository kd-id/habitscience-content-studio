from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    config_dir: Path
    config_file: Path
    output_dir: Path
    history_file: Path
    env_file: Path


def get_project_paths(project_root: Path | str | None = None) -> ProjectPaths:
    root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parent.parent
    config_dir = root / "config"
    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return ProjectPaths(
        root=root,
        config_dir=config_dir,
        config_file=config_dir / "channel_config.yaml",
        output_dir=output_dir,
        history_file=output_dir / "history.json",
        env_file=root / ".env",
    )


def load_config(config_path: Path | str | None = None, project_root: Path | str | None = None) -> dict[str, Any]:
    paths = get_project_paths(project_root)
    if paths.env_file.exists():
        load_dotenv(paths.env_file, override=False)

    target_cfg = Path(config_path).resolve() if config_path else paths.config_file
    if not target_cfg.exists():
        raise FileNotFoundError(f"Channel config not found: {target_cfg}")

    with target_cfg.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def slugify(text: str, max_length: int = 48) -> str:
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
    cleaned = re.sub(r"[\s_-]+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "konten"
    return cleaned[:max_length].rstrip("-")


def resolve_font_path(preferred: str | None = None, bold: bool = False) -> str | None:
    """Resolve a reliable TrueType font path on Windows/Linux/macOS."""
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)

    if bold:
        candidates.extend([
            "bahnschrift.ttf",
            "arialbd.ttf",
            "calibrib.ttf",
            "segoeuib.ttf",
            "segoeui.ttf",
            "LiberationSans-Bold.ttf",
            "DejaVuSans-Bold.ttf",
            "NotoSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "segoeui.ttf",
            "arial.ttf",
            "calibri.ttf",
            "bahnschrift.ttf",
            "LiberationSans-Regular.ttf",
            "DejaVuSans.ttf",
            "NotoSans-Regular.ttf",
        ])

    search_dirs = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/share/fonts"),
        Path("/System/Library/Fonts"),
    ]

    for candidate in candidates:
        p = Path(candidate)
        if p.is_file():
            return str(p)
        for directory in search_dirs:
            full = directory / candidate
            if full.is_file():
                return str(full)
    return None
