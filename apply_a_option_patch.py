#!/usr/bin/env python3
"""apply_a_option_patch.py
-------------------------------------------------
One-shot script to apply “A안” modifications so that
❶ `_score`-suffix qualitative columns are recognised
   as model features.
❷ Upset detector uses `motivation_score`.
❸ `soccer_agent_pipeline.scan_upsets()` is fully
   implemented (same logic as run_predictions_quick).

Usage:
    python apply_a_option_patch.py
"""

import pathlib, re, sys, textwrap

ROOT = pathlib.Path(__file__).resolve().parent

def patch_train_models():
    path = ROOT / "train_models.py"
    txt = path.read_text(encoding="utf-8")
    pattern = re.compile(r'feature_cols\s*=\s*\[[^\]]+\]')
    m = pattern.search(txt)
    if not m:
        print("train_models.py: feature_cols assignment not found!")
        return
    original = m.group(0)
    if "endswith" in original:
        print("train_models.py: already patched, skip.")
        return
    replacement = original.replace('c.startswith("qual_")',
                                   'c.startswith("qual_") or c.endswith("_score")')
    txt = txt.replace(original, replacement)
    path.write_text(txt, encoding="utf-8")
    print("✓ Patched train_models.py")

def patch_run_predictions():
    path = ROOT / "run_predictions_quick.py"
    txt = path.read_text(encoding="utf-8")
    if "motivation_score" in txt:
        print("run_predictions_quick.py: already patched, skip.")
    else:
        txt = txt.replace('qual_motivation', 'motivation_score')
        path.write_text(txt, encoding="utf-8")
        print("✓ Patched run_predictions_quick.py")

def patch_pipeline():
    path = ROOT / "soccer_agent_pipeline.py"
    txt = path.read_text(encoding="utf-8")
    if "def scan_upsets" not in txt:
        print("soccer_agent_pipeline.py: scan_upsets def not found!")
        return
    new_body = textwrap.dedent("""        def scan_upsets(predictions):
            """Return dict[league] -> dataframe with upset flags."""
            print("[5/6] Scanning for upsets & deciding multi-cover strategy")
            out = {}
            for lg, df in predictions.items():
                df = df.copy()
                df["is_upset"] = df.apply(
                    lambda r: (abs(float(r.get("motivation_score", 0))) >= 1.5)
                              or (r[["P_H", "P_D", "P_A"]].max() < 0.37),
                    axis=1
                )
                import numpy as np
                probs = df[["P_H", "P_D", "P_A"]].values
                ent = -np.sum(probs * np.log(probs + 1e-9), axis=1)
                df["entropy"] = ent
                df = df.sort_values("entropy", ascending=False)
                df["cover_flag"] = False
                df.loc[df.head(4).index, "cover_flag"] = True
                out[lg] = df
            return out
    """)
    txt_new = re.sub(r'def scan_upsets[\s\S]+?return \{[^\}]+\}', new_body, txt, count=1)
    if txt_new == txt:
        print("soccer_agent_pipeline.py: failed to patch (regex mismatch)")
        return
    path.write_text(txt_new, encoding="utf-8")
    print("✓ Patched soccer_agent_pipeline.py")

if __name__ == "__main__":
    patch_train_models()
    patch_run_predictions()
    patch_pipeline()
    print("✅ A-option patches applied. Re-run the pipeline 👍")
