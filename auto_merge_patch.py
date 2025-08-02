#!/usr/bin/env python3
"""auto_merge_patch.py
-------------------------------------------------
Add automatic merging of all qual_numeric_*.csv files
into engineer_features() inside soccer_agent_pipeline.py.

Usage:
    python auto_merge_patch.py
Requires: run in same directory as soccer_agent_pipeline.py
"""

import pathlib, re, textwrap

ROOT = pathlib.Path(__file__).resolve().parent
pipeline_path = ROOT / "soccer_agent_pipeline.py"
txt = pipeline_path.read_text(encoding="utf-8")

# Look for engineer_features function definition
pat = re.compile(r'def\s+engineer_features\([^)]*\):([\s\S]+?)^def', re.MULTILINE)
m = pat.search(txt)
if not m:
    print("engineer_features() not found; skipped")
else:
    body = m.group(1)
    if 'qual_files =' in body:
        print("auto merge already present; skipping")
    else:
        insert_code = textwrap.dedent("""            # --- AUTO MERGE QUALITATIVE CSVs ---
            import glob, pandas as pd
            qual_files = glob.glob(str(ROOT / 'qual_numeric_*.csv'))
            if qual_files:
                qual_df = pd.concat([pd.read_csv(f) for f in qual_files], ignore_index=True)
                # Merge on today_game_id & team_code
                df = df.merge(qual_df, on=['today_game_id', 'team_code'], how='left')
            # -----------------------------------
        """)
        # Insert after first line of function
        ind = m.start(1)
        # Find indentation of body line 1
        body_start_line = body.split('\n',1)[0]
        indent = re.match(r'(\s*)', body_start_line).group(1)
        insert_code_indented = textwrap.indent(insert_code, indent)
        txt_new = txt[:ind] + insert_code_indented + txt[ind:]
        pipeline_path.write_text(txt_new, encoding='utf-8')
        print("✓ engineer_features() patched with auto merge")
