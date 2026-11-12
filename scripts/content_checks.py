"""Report Czech article checks without changing or rejecting articles."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata


MARKER = "Proč je to zajímavé:"
WORDS = re.compile(r"\b[\w]+(?:[-‑][\w]+)*\b")
SENTENCES = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])")
NUMBER = re.compile(r"(?<!\w)[−+-]?\d+(?:[.,]\d+)?(?:\s*[%σ])?(?!\w)")
TAKEAWAY = re.compile(r"(?<!\w)proč\s+je\s+to\s+zajímavé\s*:", re.I)
LATEX = re.compile(r"\\[a-zA-Z]+|\$[^$\n]+\$|\\[\[\]()]")
HYBRIDS = re.compile(r"\b(?:observationaln\w*|simulationaln\w*|theoreticaln\w*)\b", re.I)
STRONG = re.compile(r"\b(?:prokaz\w*|prokáz\w*|potvr[dz]\w*|definitivně|revolučn\w*|průlom\w*|poprvé|vůbec první|odhal\w*)\b", re.I)
SUPERSCRIPT = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+")


def numbers(text):
    text = SUPERSCRIPT.sub(lambda match: "^" + unicodedata.normalize("NFKC", match[0]), text)
    text = unicodedata.normalize("NFKC", text).replace("−", "-")
    return {
        value.replace(",", ".").replace(" ", "").lstrip("+")
        for value in NUMBER.findall(text)
    }


def checks(title, summary, glossary, source=None):
    """Return findings. A fail is a finding, never an instruction to block publication."""
    combined = f"{title}\n{summary}"
    findings = []

    def add(level, code, detail):
        findings.append(dict(level=level, code=code, detail=detail))

    marks = list(TAKEAWAY.finditer(summary))
    if len(marks) != 1 or marks[0][0] != MARKER or not summary[:marks[0].start()].strip() or not summary[marks[0].end():].strip():
        add("fail", "takeaway_format", "Očekává se právě jedna přesná značka a text před ní i za ní.")
    main = summary[:marks[0].start()].strip() if marks else summary.strip()
    sentences = SENTENCES.split(re.sub(r"\s+", " ", main))
    word_count = len(WORDS.findall(summary))
    if not 90 <= word_count <= 180:
        add("warn", "summary_length", f"{word_count} slov, cílový rozsah je 90 až 180.")
    if len(sentences[0]) > 160 or not sentences[0].endswith("."):
        add("warn", "first_sentence", f"{len(sentences[0])} znaků. Cíl je nejvýše 160 znaků a tečka.")
    if len(" ".join(sentences[:2])) > 280:
        add("warn", "opening_length", "První dvě věty překračují 280 znaků.")
    if LATEX.search(sentences[0]) or re.search(r"\b[A-Z]{2,}\b|[≈≲≳≤≥]", sentences[0]):
        add("warn", "technical_opening", "První věta může obsahovat vzorec nebo zkratku.")
    for pattern, level, code in ((LATEX, "fail", "latex"), (HYBRIDS, "fail", "language_hybrid"), (STRONG, "warn", "strong_claim")):
        matches = sorted({m[0] for m in pattern.finditer(combined)}, key=str.casefold)
        if matches:
            add(level, code, ", ".join(matches))
    for entry in glossary:
        variants = [v for v in entry["variants"] if re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", combined, re.I)]
        if variants:
            add("fail" if entry["status"] == "approved" else "warn", "terminology", f"{', '.join(variants)} → {entry['preferred']}")
    if source is not None:
        unmatched = numbers(combined) - numbers(source)
        if unmatched:
            add("warn", "numbers_to_review", "Čísla bez přímé shody v podkladu: " + ", ".join(sorted(unmatched)))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/news.json"))
    parser.add_argument("--glossary", type=Path, default=Path("data/glossary_cs.json"))
    parser.add_argument("--sources", type=Path, help="Optional JSON object keyed by article ID with original title and abstract as a single string.")
    parser.add_argument("--output", type=Path, default=Path("tmp/content-checks.json"))
    args = parser.parse_args()

    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    glossary = read(args.glossary)
    sources = read(args.sources) if args.sources else {}
    results = []
    totals = Counter()
    for item in read(args.input):
        if item.get("lang") != "cs" or item.get("needs_translation"):
            continue
        article_id = item["id"]
        source = sources.get(article_id)
        findings = checks(item["title"], item["summary"], glossary, source)
        levels = {f["level"] for f in findings}
        status = "fail" if "fail" in levels else "warn" if levels else "pass"
        totals[status] += 1
        results.append(dict(id=article_id, title=item["title"], status=status,
                            source_checked=source is not None, findings=findings))
    report = dict(totals=dict(totals), source_checked=sum(r["source_checked"] for r in results), articles=results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "articles"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
