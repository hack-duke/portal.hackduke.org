"""Build src/forms/data/universities.json for the application's university dropdown.

Source: Hipo's university-domains-list (public, ~10k schools worldwide):
  curl -L -o world_universities.json \
    https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json
  python3 scripts/build_universities.py world_universities.json

The raw list has some noise (school districts, admin offices, typos, outdated
names), so the cleanup rules below are applied on top of it. Applicants can
still type any school that isn't listed.
"""

import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src/forms/data/universities.json"

# Not degree-granting institutions a hackathon applicant would attend.
REMOVE_PATTERNS = [
    r"^Académie d",  # French regional school districts
    r"High School\b",
    r"School District\b",
    r"\bSystem$",  # system offices; individual campuses are listed separately
    r"Office of the President",
    r"^CHUV - ",
    r"^HUG - ",
]

# Typos, broken casing, and outdated or truncated names.
RENAME = {
    "42 FR": "42 Paris",
    "American Public University System": "American Public University",
    "Lone Star College System": "Lone Star College",
    "Tokai University Educational System": "Tokai University",
    "42 US": "42 Silicon Valley",
    "CHEONGJU UNIVERSITY": "Cheongju University",
    "Elon College": "Elon University",
    "Global Open University , Nagaland": "Global Open University, Nagaland",
    "Higher School o Business/National Louis University(WSB/NLU) in Nowy Sacz":
        "Higher School of Business - National Louis University (WSB-NLU), Nowy Sacz",
    "karamanoglu mehmet bey University": "Karamanoğlu Mehmetbey University",
    "Morehouse": "Morehouse College",
    "Universidad Técnica \"Federico Santa María\"": "Universidad Técnica Federico Santa María",
    "Washington University, Saint Louis": "Washington University in St. Louis",
    "yale-NUS": "Yale-NUS College",
}

ADD = [
    "Duke Kunshan University",
]


def clean(name: str) -> str:
    name = " ".join(name.split())
    name = name.replace("’", "'").replace("‘", "'")
    name = RENAME.get(name, name)
    name = re.sub(r"\s+,", ",", name)
    # Drop a stray trailing period, but keep abbreviations like "A.C." or "A.S.PAI.T.E."
    if name.endswith(".") and not re.search(r"\b[A-Z]\.$", name):
        name = name[:-1]
    return name


def main(src: str) -> None:
    raw = json.load(open(src, encoding="utf-8"))
    names = {clean(u["name"]) for u in raw if isinstance(u.get("name"), str) and u["name"].strip()}
    names = {n for n in names if not any(re.search(p, n) for p in REMOVE_PATTERNS)}
    names.update(ADD)
    result = sorted(names, key=str.casefold)
    OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(result)} universities to {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
