#!/usr/bin/env python3
"""apply_a_option_patch.py  (fixed quoting)
One-shot script to patch:
  1) train_models.py  -> include *_score columns
  2) run_predictions_quick.py -> use motivation_score
  3) soccer_agent_pipeline.py -> implement scan_upsets()
Run this once in the project root:
    python apply_a_option_patch.py
"""

import pathlib, re, textwrap

ROOT = pathlib.Path(__file__).resolve().parent

def patch_train_models():
    path = ROOT / "train_models.py"
    if not path.exists():
        print("train_models.py not found.")
        return
    txt = path.read_text(encoding="utf-8")
    m = re.search(r'feature_cols\s*=\s*\[[^\]]+\]', txt)
    if not m:
        print("feature_cols assignment not found in train_models.py")
        return
    original = m.group(0)
    if "_score" in original:
        print("train_models.py already patched.")
        return
    patched = original.replace('c.startswith("qual_")',
                               'c.startswith("qual_") or c.endswith("_score")')
    txt = txt.replace(original, patched)
    path.write_text(txt, encoding="utf-8")
    print("✓ Patched train_models.py")

def patch_run_predictions():
    path = ROOT / "run_predictions_quick.py"
    if not path.exists():
        print("run_predictions_quick.py not found.")
        return
    txt = path.read_text(encoding="utf-8")
    if "motivation_score" in txt:
        print("run_predictions_quick.py already patched.")
        return
    txt = txt.replace('qual_motivation', 'motivation_score')
    path.write_text(txt, encoding="utf-8")
    print("✓ Patched run_predictions_quick.py")

def patch_pipeline():
    path = ROOT / "soccer_agent_pipeline.py"
    if not path.exists():
        print("soccer_agent_pipeline.py not found.")
        return
    txt = path.read_text(encoding="utf-8")
    if "motivation_score" in txt and "def scan_upsets(" in txt and "cover_flag" in txt:
        print("soccer_agent_pipeline.py already looks patched.")
        return
    # Build new scan_upsets implementation
    new_body = textwrap.dedent("""        def scan_upsets(predictions):
            '''Return dict[league] -> dataframe with upset & cover flags.'''
            print('[5/6] Scanning for upsets & deciding multi-cover strategy')
            out = {}
            import numpy as np
            for lg, df in predictions.items():
                df = df.copy()
                # upset flag
                df['is_upset'] = df.apply(
                    lambda r: (abs(float(r.get('motivation_score', 0))) >= 1.5)
                              or (r[['P_H', 'P_D', 'P_A']].max() < 0.37),
                    axis=1
                )
                # entropy & cover selection (top‑4 highest entropy)
                probs = df[['P_H', 'P_D', 'P_A']].values
                entropy = -np.sum(probs * np.log(probs + 1e-12), axis=1)
                df['entropy'] = entropy
                df = df.sort_values('entropy', ascending=False)
                df['cover_flag'] = False
                df.loc[df.head(4).index, 'cover_flag'] = True
                out[lg] = df
            return out
    """)
    # Replace existing placeholder scan_upsets definition
    txt_new, subs = re.subn(
        r'def\s+scan_upsets[\s\S]+?return[^\n]*',
        new_body,
        txt,
        count=1
    )
    if subs == 0:
        print('scan_upsets placeholder not found, inserting new function.')
        # Append at end
        txt_new = txt + "\n\n" + new_body
    path.write_text(txt_new, encoding="utf-8")
    print("✓ Patched soccer_agent_pipeline.py")

if __name__ == "__main__":
    patch_train_models()
    patch_run_predictions()
    patch_pipeline()
    print("✅ A-option patches applied successfully.")
