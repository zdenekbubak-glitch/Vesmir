"""Measure the saved news corpus without contacting external services."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean

MARKER = "Proč je to zajímavé:"
WORDS = re.compile(r"\b[\w]+(?:[-‑][\w]+)*\b")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])")
FLAGS = {
    "LaTeX nebo značky vzorců": r"\\(?:frac|mathrm|begin|alpha|lambda)\b|\$[^$\n]+\$",
    "Matematický zápis": r"[≲≳≈≤≥]|f_?NL",
    "Objev nebo odhalení": r"\b(?:odhal\w*|objevili|objevila)\b",
    "Záhada": r"\bzáhad\w*\b",
    "Zásadní": r"\bzásadn\w*\b",
    "Poprvé": r"\b(?:poprvé|vůbec první)\b",
    "Potvrzení": r"\bpotvr[dz]\w*\b",
    "Průlom nebo revoluce": r"\b(?:průlom\w*|revolučn\w*)\b",
    "Definitivně": r"\bdefinitivně\b",
    "Prokazuje": r"\bprokaz\w*\b",
    "Rudý posuv": r"\brud\w+\s+posuv\w*\b",
    "Červený posun": r"\bčerven\w+\s+posun\w*\b",
    "Temná hmota": r"\btemn\w+\s+hmot\w*\b",
    "Tmavá hmota": r"\btmav\w+\s+hmot\w*\b",
    "Časoprostor": r"\bčasoprostor\w*\b",
    "Prostoročas": r"\bprostoročas\w*\b",
}


def report(items):
    czech = [item for item in items if item.get("lang") == "cs"]
    summaries = [str(item.get("summary") or "") for item in czech]
    lengths = [len(WORDS.findall(s)) for s in summaries]
    paragraphs = [re.split(r"\n\s*\n", s.strip()) for s in summaries]
    first_lengths = [len(WORDS.findall(p[0])) for p in paragraphs]
    sentences = [SENTENCE.split(s.split(MARKER, 1)[0].strip()) for s in summaries]
    sentence_lengths = [len(WORDS.findall(line)) for group in sentences for line in group if line]
    sources = Counter(item.get("source") or "neuvedeno" for item in czech)
    lines = [
        "# Výchozí stav kvality článků",
        "",
        f"- Položek celkem: {len(items)}. Českých: {len(czech)}.",
        "- České položky podle zdroje: " + ", ".join(f"{k} {v}" for k, v in sources.most_common()),
        f"- Délka souhrnu: průměr {mean(lengths or [0]):.1f} slov, rozsah {min(lengths or [0])}–{max(lengths or [0])}.",
        f"- První odstavec: průměr {mean(first_lengths or [0]):.1f} slov.",
        f"- Průměrná věta hlavního textu: {mean(sentence_lengths or [0]):.1f} slov.",
        f"- První věta nad 160 znaků: {sum(len(s[0]) > 160 for s in sentences)}.",
        f"- Tři nebo více odstavců: {sum(len(p) >= 3 for p in paragraphs)}.",
        f"- Závěrečná značka jinak než právě jednou: {sum(s.count(MARKER) != 1 for s in summaries)}.",
        "",
        "Následují počty českých článků s alespoň jednou shodou v titulku nebo souhrnu. Jde o signály ke kontrole. Dělení vět je přibližné a může započítat zkratky.",
        "",
    ]
    corpus = [f"{item.get('title', '')} {summary}" for item, summary in zip(czech, summaries)]
    lines.extend(f"- {label}: {sum(bool(re.search(pattern, s, re.I)) for s in corpus)}" for label, pattern in FLAGS.items())
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/news.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/baseline.md"))
    args = parser.parse_args()
    items = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report(items), encoding="utf-8")


if __name__ == "__main__":
    main()
