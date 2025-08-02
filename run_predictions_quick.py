
#!/usr/bin/env python3
"""
run_predictions_quick.py
------------------------
* Loads calibrated prediction XLSX for J2, K1, K2
* Merges qualitative CSV
* Calculates ΔP vs market odds (if odds CSV provided)
* Flags upsets & multi‑cover picks (simplified rule)
* Outputs Excel report ready for betting sheet.
"""

import argparse, pandas as pd, pathlib, numpy as np

def load_pred(lg: str, date: str):
    path = pathlib.Path(f"/mnt/data/{lg.lower()}_predictions_calibrated.xlsx")
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_excel(path)
    df['league'] = lg
    # 필터 날짜
    df = df[df['today_game_id'].str.startswith(date.replace('-', ''))]
    return df

def load_odds(odds_file: str):
    if odds_file and pathlib.Path(odds_file).exists():
        odds = pd.read_csv(odds_file)
        return odds
    return pd.DataFrame()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--qual-file", required=True, help="qual_numeric CSV")
    p.add_argument("--odds-file", default="", help="market odds CSV (optional)")
    p.add_argument("--output", required=True, help="Excel report path")
    args = p.parse_args()

    leagues = ["J2", "K1", "K2"]
    df = pd.concat([load_pred(lg, args.date) for lg in leagues], ignore_index=True)

    # Merge qualitative
    qual = pd.read_csv(args.qual_file)
    df = df.merge(qual, on=["today_game_id", "team_code"], how="left")

    # ΔP if odds provided
    if args.odds_file:
        odds = load_odds(args.odds_file)
        if not odds.empty:
            df = df.merge(odds, on="today_game_id", how="left")
            for col_model, col_market in [("P_H", "P_H_market"), ("P_D", "P_D_market"), ("P_A", "P_A_market")]:
                if col_market in df.columns:
                    df[f"Δ{col_model}"] = df[col_model] - df[col_market]

    # Upset flag (motivation_score >=1.5 or max P <0.37)
    df["is_upset"] = df.apply(
        lambda r: (abs(float(r.get("motivation_score", 0))) >= 1.5) or
                  (r[["P_H", "P_D", "P_A"]].max() < 0.37),
        axis=1
    )

    # Multi‑cover pick: top 4 highest entropy games
    probs = df[["P_H", "P_D", "P_A"]].values
    ent = -np.sum(probs * np.log(probs + 1e-9), axis=1)
    df["entropy"] = ent
    df = df.sort_values("entropy", ascending=False)
    df["cover_flag"] = False
    df.loc[df.head(4).index, "cover_flag"] = True

    # Save
    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)
    print(f"✅ Report saved → {out_path}")

if __name__ == "__main__":
    main()
