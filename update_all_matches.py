
#!/usr/bin/env python3
"""
update_all_matches.py
---------------------
Convenience wrapper that updates recent matches for J2, K1, K2 in one shot.

Internally imports `update_matches.py` (must be co‑located) and calls its `main`
via `subprocess` with appropriate league IDs.

Adjust `LEAGUE_CONFIG` below with real FootyStats `league_id` values if needed.
"""

import subprocess, sys, datetime as dt, pathlib, importlib.util, argparse

THIS_DIR = pathlib.Path(__file__).resolve().parent
SCRIPT   = THIS_DIR / "update_matches.py"

# FootyStats league_id mapping (example values ─ change as needed)
LEAGUE_CONFIG = {
    "J2": 12,   # J2 League
    "K1": 1,    # K League 1
    "K2": 2,    # K League 2
}

def run_update(lg: str, league_id: int, qual_file: str, merge_existing: str):
    cmd = [
        sys.executable, str(SCRIPT),
        "--league", lg,
        "--league-id", str(league_id),
        "--merge-qual", qual_file,
        "--merge-existing", merge_existing,
        "--output-dir", "/mnt/data"
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qual-file", default="", help="qual_numeric CSV path")
    args = ap.parse_args()

    today = dt.date.today().strftime("%Y%m%d")
    for lg, lid in LEAGUE_CONFIG.items():
        merge_file = f"/mnt/data/{lg.lower()}_matches_{today}.xlsx"
        run_update(lg, lid, args.qual_file, merge_file)

if __name__ == "__main__":
    main()
