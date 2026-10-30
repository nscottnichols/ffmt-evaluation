#!/usr/bin/env python3
"""Launch the portable ffmt conformance runner from an external checkout."""
from evaluation import launch

if __name__ == "__main__":
    raise SystemExit(launch("conformance"))
