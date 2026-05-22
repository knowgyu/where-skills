#!/usr/bin/env python3
"""Repo-level wrapper for the self-contained where-skills OfficeWhere helper."""

from __future__ import annotations

import runpy
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / "skills" / "where-skills" / "scripts" / "officewhere_provider.py"

if __name__ == "__main__":
    runpy.run_path(str(HELPER), run_name="__main__")
