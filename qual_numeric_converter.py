
"""
qual_numeric_converter.py

Script to convert qualitative match analysis documents into quantitative scores
based on predefined scoring criteria.

Usage:
    python qual_numeric_converter.py --input_folder ./qual_docs --output_csv qual_numeric.csv
"""

import argparse
import glob
import os
import re
import pandas as pd
from docx import Document

# Scoring dictionaries -------------------------------------------------------
SCORING = {
    "injury": {
        "no key injuries": 2,
        "minor injuries": 1,
        "some key injuries": 0,
        "multiple key injuries": -1,
        "severe injury crisis": -2,
    },
    "lineup": {
        "stable optimal": 2,
        "mostly stable": 1,
        "uncertain": 0,
        "disjointed": -1,
        "major disruption": -2,
    },
    "tactics": {
        "highly effective": 2,
        "moderately effective": 1,
        "neutral": 0,
        "questionable": -1,
        "collapsing": -2,
    },
    "motivation": {
        "very high": 2,
        "high": 1,
        "normal": 0,
        "low": -1,
        "crisis": -2,
    },
    "weather": {
        "advantage": 2,
        "minor advantage": 1,
        "neutral": 0,
        "disadvantage": -1,
        "severe disadvantage": -2,
    },
}

# Regular expressions to detect sections in docx -----------------------------
SECTION_PATTERNS = {
    "injury": re.compile(r"qual_injury[:\-]\s*(.*)", re.IGNORECASE),
    "lineup": re.compile(r"qual_lineup[:\-]\s*(.*)", re.IGNORECASE),
    "tactics": re.compile(r"qual_tactics[:\-]\s*(.*)", re.IGNORECASE),
    "motivation": re.compile(r"qual_motivation[:\-]\s*(.*)", re.IGNORECASE),
    "weather": re.compile(r"qual_weather[:\-]\s*(.*)", re.IGNORECASE),
}

def classify_text(text, category):
    """Return score for text based on keyword heuristics."""
    text = text.lower()
    if category == "injury":
        if "없" in text or "no" in text:
            return 2
        if "minor" in text or "경미" in text:
            return 1
        if "부상" in text and ("다수" in text or "multiple" in text or "심각" in text):
            return -1
        if "전력" in text and "공백" in text:
            return 0
        return 0
    if category == "lineup":
        if "안정" in text or "stable" in text:
            return 2
        if "로테이션" in text or "rotat" in text:
            return 1
        if "실험" in text or "uncertain" in text:
            return -1
        return 0
    if category == "tactics":
        if "공격" in text and ("폭발" in text or "효과" in text):
            return 2
        if "안정" in text or "balanced" in text:
            return 1
        if "문제" in text or "불안" in text:
            return -1
        return 0
    if category == "motivation":
        if "반드시" in text or "필승" in text or "very high" in text:
            return 2
        if "높" in text or "high" in text:
            return 1
        if "부진" in text or "slump" in text:
            return -1
        return 0
    if category == "weather":
        if "폭염" in text or "heat" in text:
            return -1
        if "home advantage" in text or "familiar" in text:
            return 1
        return 0
    return 0

def parse_docx(filepath):
    doc = Document(filepath)
    full_text = "\n".join([p.text for p in doc.paragraphs])
    scores = {}
    for cat, pattern in SECTION_PATTERNS.items():
        match = pattern.search(full_text)
        if match:
            extracted = match.group(1)
            scores[cat] = classify_text(extracted, cat)
        else:
            scores[cat] = 0
    return scores

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_folder", required=True)
    parser.add_argument("--output_csv", required=True)
    args = parser.parse_args()

    records = []
    for filepath in glob.glob(os.path.join(args.input_folder, "*.docx")):
        filename = os.path.basename(filepath)
        match_id, team = filename.replace(".docx", "").rsplit("-", 1)
        scores = parse_docx(filepath)
        record = {
            "match_id": match_id,
            "team": team.upper(),
            **{f"{k}_score": v for k, v in scores.items()},
        }
        record["qual_total_score"] = sum(scores.values())
        records.append(record)

    pd.DataFrame(records).to_csv(args.output_csv, index=False)
    print(f"Saved {len(records)} records to {args.output_csv}")

if __name__ == "__main__":
    main()
