"""Geometry helpers for per-display lockdown windows."""

from __future__ import annotations


def signed_offset(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def build_geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{width}x{height}{signed_offset(x)}{signed_offset(y)}"
