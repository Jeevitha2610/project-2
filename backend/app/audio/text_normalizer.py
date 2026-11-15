"""Text Normalization for Speech Synthesis.

Normalizes numbers, currencies, dates, and common abbreviations into spoken English,
and splits text into clean sentence chunks of <= 25 words.
"""
from __future__ import annotations

import re
from typing import List

ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen"
]
TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
]
THOUSANDS = ["", "thousand", "million", "billion"]

ORDINALS = {
    "1st": "first", "2nd": "second", "3rd": "third", "4th": "fourth",
    "5th": "fifth", "6th": "sixth", "7th": "seventh", "8th": "eighth",
    "9th": "ninth", "10th": "tenth", "11th": "eleventh", "12th": "twelfth",
    "13th": "thirteenth", "14th": "fourteenth", "15th": "fifteenth",
    "16th": "sixteenth", "17th": "seventeenth", "18th": "eighteenth",
    "19th": "nineteenth", "20th": "twentieth", "21st": "twenty-first",
    "22nd": "twenty-second", "23rd": "twenty-third", "30th": "thirtieth",
    "31st": "thirty-first"
}

ABBREVIATIONS = {
    r"\bdr\.": "doctor",
    r"\bmr\.": "mister",
    r"\bmrs\.": "missus",
    r"\bms\.": "miss",
    r"\bprof\.": "professor",
    r"\be\.g\.": "for example",
    r"\bi\.e\.": "that is",
    r"\betc\.": "et cetera",
    r"\bvs\.": "versus",
    r"\bapprox\.": "approximately",
    r"\bdept\.": "department",
    r"\bapt\.": "apartment",
    r"\bst\.": "street",
    r"\brd\.": "road",
    r"\bave\.": "avenue",
    r"\bblvd\.": "boulevard",
    r"\bmin\.": "minute",
    r"\bsec\.": "second",
    r"\bhr\.": "hour",
    r"\bhrs\.": "hours",
    r"\bkg\b": "kilograms",
    r"\bkm\b": "kilometers",
    r"\bcm\b": "centimeters",
    r"\bmm\b": "millimeters",
}

MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def _integer_to_words(n: int) -> str:
    """Converts an integer (0 to 999,999,999,999) to English words."""
    if n == 0:
        return "zero"
    if n < 0:
        return "negative " + _integer_to_words(abs(n))

    def _convert_hundred(val: int) -> str:
        parts = []
        if val >= 100:
            parts.append(ONES[val // 100] + " hundred")
            val %= 100
        if val >= 20:
            tens_word = TENS[val // 10]
            val %= 10
            if val > 0:
                parts.append(f"{tens_word}-{ONES[val]}")
            else:
                parts.append(tens_word)
        elif val > 0:
            parts.append(ONES[val])
        return " ".join(parts)

    parts = []
    chunk_idx = 0
    while n > 0:
        chunk = n % 1000
        if chunk != 0:
            chunk_word = _convert_hundred(chunk)
            if THOUSANDS[chunk_idx]:
                chunk_word += " " + THOUSANDS[chunk_idx]
            parts.insert(0, chunk_word)
        n //= 1000
        chunk_idx += 1

    return " ".join(parts)


def _number_to_year(n: int) -> str:
    """Reads 4-digit years naturally (e.g. 1995 -> nineteen ninety-five, 2026 -> twenty twenty-six)."""
    if 1000 <= n <= 2099:
        century = n // 100
        decade = n % 100
        c_str = _integer_to_words(century)
        if decade == 0:
            return f"{c_str} hundred"
        if decade < 10:
            return f"{c_str} oh {_integer_to_words(decade)}"
        return f"{c_str} {_integer_to_words(decade)}"
    return _integer_to_words(n)


def normalize_text_input(text: str) -> str:
    """Normalizes abbreviations, currency, dates, numbers in input text."""
    if not text:
        return ""

    out = text

    # 1. Abbreviations
    for pattern, repl in ABBREVIATIONS.items():
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    # 2. Ordinals: 1st, 2nd, etc.
    def _replace_ordinal(match: re.Match) -> str:
        token = match.group(0).lower()
        return ORDINALS.get(token, token)
    out = re.sub(r"\b\d+(?:st|nd|rd|th)\b", _replace_ordinal, out, flags=re.IGNORECASE)

    # 3. Currency: $50, $10.50, €20, £10, ₹100
    def _replace_currency(match: re.Match) -> str:
        sym = match.group(1)
        amount_str = match.group(2)
        unit = "dollars" if sym == "$" else "euros" if sym == "€" else "pounds" if sym == "£" else "rupees"
        subunit = "cents" if sym in ("$", "€") else "pence" if sym == "£" else "paise"
        if "." in amount_str:
            main_part, dec_part = amount_str.split(".", 1)
            main_val = int(main_part) if main_part else 0
            dec_val = int(dec_part[:2]) if dec_part else 0
            res = f"{_integer_to_words(main_val)} {unit}"
            if dec_val > 0:
                res += f" and {_integer_to_words(dec_val)} {subunit}"
            return res
        val = int(amount_str)
        unit_name = unit[:-1] if val == 1 and unit.endswith("s") else unit
        return f"{_integer_to_words(val)} {unit_name}"

    out = re.sub(r"([$€£₹])(\d+(?:\.\d{1,2})?)", _replace_currency, out)

    # 4. Dates: DD/MM/YYYY or YYYY-MM-DD
    def _replace_date(match: re.Match) -> str:
        d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            month_name = MONTHS[m]
            day_str = ORDINALS.get(f"{d}th", f"{d}")
            year_str = _number_to_year(y)
            return f"{month_name} {day_str}, {year_str}"
        return match.group(0)

    out = re.sub(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", _replace_date, out)

    # 5. Standalone 4-digit years: e.g. 1990-2099
    def _replace_year(match: re.Match) -> str:
        val = int(match.group(0))
        if 1900 <= val <= 2099:
            return _number_to_year(val)
        return match.group(0)

    # 6. Percentages: 25% -> twenty-five percent
    def _replace_percent(match: re.Match) -> str:
        num = match.group(1)
        if "." in num:
            parts = num.split(".")
            return f"{_integer_to_words(int(parts[0]))} point {_integer_to_words(int(parts[1]))} percent"
        return f"{_integer_to_words(int(num))} percent"

    out = re.sub(r"\b(\d+(?:\.\d+)?)\s*%", _replace_percent, out)

    # 7. Decimals: 3.14 -> three point one four
    def _replace_decimal(match: re.Match) -> str:
        whole, frac = match.group(1), match.group(2)
        whole_str = _integer_to_words(int(whole))
        frac_str = " ".join(ONES[int(digit)] for digit in frac)
        return f"{whole_str} point {frac_str}"

    out = re.sub(r"\b(\d+)\.(\d+)\b", _replace_decimal, out)

    # 8. Integers
    def _replace_number(match: re.Match) -> str:
        num = int(match.group(0))
        if 1900 <= num <= 2099:
            return _number_to_year(num)
        return _integer_to_words(num)

    out = re.sub(r"\b\d+\b", _replace_number, out)

    # Clean whitespace
    out = re.sub(r"\s+", " ", out).strip()
    return out


def split_into_chunks(text: str, max_words_per_chunk: int = 25) -> List[str]:
    """Splits normalized text into sentence chunks of about 25 words or fewer."""
    if not text or not text.strip():
        return []

    # First split on clean sentence boundaries (. ! ?)
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: List[str] = []

    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) <= max_words_per_chunk:
            chunks.append(s)
        else:
            # Sentence is longer than max_words_per_chunk: split on sub-clauses (, ; :) or word count
            sub_clauses = re.split(r"(?<=[,;:])\s+", s)
            current_chunk: List[str] = []
            current_word_count = 0
            for clause in sub_clauses:
                clause_words = clause.split()
                if current_word_count + len(clause_words) <= max_words_per_chunk:
                    current_chunk.append(clause)
                    current_word_count += len(clause_words)
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk).strip())
                        current_chunk = []
                        current_word_count = 0
                    if len(clause_words) <= max_words_per_chunk:
                        current_chunk.append(clause)
                        current_word_count = len(clause_words)
                    else:
                        # Slice clause directly by word count
                        for i in range(0, len(clause_words), max_words_per_chunk):
                            chunks.append(" ".join(clause_words[i:i + max_words_per_chunk]))
            if current_chunk:
                chunks.append(" ".join(current_chunk).strip())

    return [c.strip() for c in chunks if c.strip()]
