"""
Lightweight, free, local heuristic parser for the "Smart Import" tab.
No API key, no cost — just pattern matching on common ways people jot down orders
in Roman Urdu / English mixed notes.

This is a best-effort parser, NOT real AI — it will miss unusual phrasing, so the
UI always shows an editable preview table before anything is saved.

Recognized pattern, roughly: "<day> <month-name> ... <name/product> ... <number> <unit>"
e.g. "5 Jan ko Ali ne 2 case liye"  ->  Date=Jan 5, Product="Ali", Quantity=2
"""

import re
from datetime import datetime

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Words that are noise once we've pulled the date + quantity phrase out —
# stripped so what's left is (hopefully) just the product/customer name.
NOISE_WORDS = r"\b(ko|ne|liye|bheji|diya|di|le|gaya|the|se|aur|bhi|ka|ki|ke)\b"

UNIT_WORDS = r"(case|cases|unit|units|piece|pieces|cover|covers|pcs|pc|box|boxes|dozen|carton|cartons)"


def simple_parse_raw_text(text):
    """
    Parse messy multi-line/comma-separated order notes into structured rows.
    Returns a list of dicts: [{"Date": date, "Product": str, "Quantity": int}, ...]
    Lines that don't match a recognizable date + quantity pattern are skipped.
    """
    results = []
    if not text or not text.strip():
        return results

    current_year = datetime.now().year
    lines = re.split(r"[\n]+", text)

    for line in lines:
        for chunk in re.split(r"(?<=\d)\s*,\s*(?=\d)|;", line):
            chunk = chunk.strip()
            if not chunk:
                continue

            date_match = re.search(r"(\d{1,2})\s*([A-Za-z]{3,9})", chunk)
            qty_match = re.search(rf"(\d+)\s*{UNIT_WORDS}", chunk, re.IGNORECASE)

            if not date_match or not qty_match:
                continue

            day = int(date_match.group(1))
            month = MONTHS.get(date_match.group(2).lower())
            if not month:
                continue

            try:
                parsed_date = datetime(current_year, month, day).date()
            except ValueError:
                continue

            quantity = int(qty_match.group(1))

            remainder = chunk.replace(date_match.group(0), "").replace(qty_match.group(0), "")
            remainder = re.sub(NOISE_WORDS, "", remainder, flags=re.IGNORECASE)
            remainder = re.sub(r"\s+", " ", remainder).strip(" .-+")
            product_guess = remainder or "Unknown"

            results.append({"Date": parsed_date, "Product": product_guess, "Quantity": quantity})

    return results