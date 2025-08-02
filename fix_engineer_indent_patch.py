#!/usr/bin/env python3
"""fix_engineer_indent_patch.py
Quick patch to re‑indent the AUTO MERGE block inside engineer_features()
which caused an IndentationError.
Run once from the project root:
    python fix_engineer_indent_patch.py
"""

import pathlib, re, textwrap
ROOT = pathlib.Path(__file__).resolve().parent
fp = ROOT / "soccer_agent_pipeline.py"
code = fp.read_text(encoding="utf-8").splitlines()
fixed = []
in_eng = False
for line in code:
    if line.startswith("def engineer_features"):
        in_eng = True
        fixed.append(line)
        continue
    if in_eng and line.startswith("def "):
        in_eng = False
    if in_eng:
        # ensure at least 4‑space indent
        if line.strip() and not line.startswith("    "):
            line = "    " + line
    fixed.append(line)
fp.write_text("\n".join(fixed), encoding="utf-8")
print("✓ Indentation of engineer_features() corrected.")
