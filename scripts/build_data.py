"""
5 West Knowledge Hub — static site data pipeline.

Reads the raw Dataverse JSON exports (OneDrive) + the already-cleaned Card
Sections BodyHtml CSV, and produces one clean data/cards.json for the static
site to fetch and render client-side.

Run: python3 scripts/build_data.py
"""
import json
import csv
import re
import os

ONEDRIVE = "/Users/scottpro/Library/CloudStorage/OneDrive-KeckMedicineofUSC/Documents/"
SECTIONS_CSV = "/Users/scottpro/Claude/Projects/Knowledge Hub | Critical Care/5West Knowledge Hub - Build/CardSection_BodyHtml_FINAL_2026-08-02.csv"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")

# manual disambiguation for the 3 bare "Heart Failure" related-card links
# that were never resolvable from TargetCardTitle alone -- see project memory.
# RC00010: source = ACS diagnosis card -> ischemic HF is classically reduced-EF
# RC00850/RC00851: source = Heart Transplant (OHT) card, created as a pair at
# the same timestamp -> almost certainly meant to cover BOTH HF phenotypes as
# transplant-workup background reading, not a duplicate mistake
HEART_FAILURE_OVERRIDES = {
    "RC00010": "hfref_diagnosis",
    "RC00850": "hfref_diagnosis",
    "RC00851": "hfpef_diagnosis",
}

CANONICAL_SYSTEM_MAP = {
    "cardiac": "Cardiac", "cardiovascular": "Cardiac",
    "pulmonary": "Pulmonary",
    "neurologic": "Neurologic", "neurological": "Neurologic",
    "renal": "Renal/FEN", "renal-fen": "Renal/FEN", "renal fen": "Renal/FEN",
    "renal/fen": "Renal/FEN",
    "renal-fenestration": "Renal/FEN", "renal fenestration": "Renal/FEN",  # autocorrect artifact
    "renal-fluid-electrolyte": "Renal/FEN", "renal fluid electrolyte": "Renal/FEN",
    "hematology": "Hematology",
    "infectious": "Infectious", "infectious-disease": "Infectious", "infectious disease": "Infectious",
    "endocrine": "Endocrine", "metabolic": "Endocrine",
    "gi": "GI", "gastrointestinal": "GI", "hepatic": "GI",
    "integumentary": "Integumentary",
    "musculoskeletal": "Musculoskeletal",
    "vascular": "Vascular",
    "psych": "Psych", "pain": "Pain", "genetics": "Genetics",
    "electrophysiology": "Electrophysiology", "pharmacy": "Pharmacy",
    "cross-system": "Cross-System", "cross system": "Cross-System",
}


def clean_system(raw):
    """Normalize the wildly inconsistent System field (mixed delimiters --
    backtick-lists, plain commas, '+', parenthetical asides that are
    sometimes a system breakdown and sometimes an unrelated clinical note,
    a 'Fen'->'Fenestration' autocorrect artifact) into a small closed set of
    canonical tags, validated against every unique raw value in the corpus
    (17 tags, zero unmapped fallthrough) before wiring in."""
    if not raw:
        return []
    s = re.sub(r"\*?\([^)]*\)\*?", "", raw)  # strip parenthetical asides entirely
    parts = re.split(r"`\s*,\s*`|`\s*\+\s*`|,|\+", s)
    tags = []
    for p in parts:
        p = p.strip().strip("`").strip().lower()
        p = re.sub(r"\s+", " ", p)
        if not p:
            continue
        canon = CANONICAL_SYSTEM_MAP.get(p, p.title())
        if canon not in tags:
            tags.append(canon)
    return tags


PHASE_LABELS = {
    "preop": "Pre-op",
    "postop": "Post-op",
    "pod-0": "POD 0",
    "pod-1-3": "POD 1–3",
    "pod-4-plus": "POD 4+",
    "post-discharge": "Post-discharge",
    "medical-admit": "Medical admit",
    "chronic-disease": "Chronic disease",
    "n-a": None,  # not a real phase value, drop it
}


def load_json(filename):
    with open(os.path.join(ONEDRIVE, filename), encoding="utf-8") as f:
        return json.load(f)


def clean_backtick_list(raw):
    """'hematology`, `cardiac' -> ['hematology', 'cardiac']
    Source data was a markdown code-list (`item`, `item`) that had only its
    outermost backticks stripped on import, leaving internal `, ` artifacts."""
    if not raw:
        return []
    raw = raw.strip().strip("`")
    parts = [p.strip().strip("`").strip() for p in raw.split("`, `")]
    return [p for p in parts if p]


def humanize(token):
    return token.replace("-", " ").replace("_", " ").strip().title()


def clean_markdown_bold(text):
    """Strip leftover **bold** markdown from plain-text fields (QuickAnswer
    etc.) -- these were never run through the BodyHtml cleanup pipeline
    since they're separate Card-level columns, not Card Section rows."""
    if not text:
        return text
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def main():
    cards_raw = load_json("Card.json")
    types_raw = load_json("CardType.json")
    acuity_raw = load_json("Acuity.json")
    refs_raw = load_json("Reference.json")
    links_raw = load_json("RelatedCardLink.json")

    # --- facets ---
    card_types = {
        t["cr577_typecode"]: {
            "code": t["cr577_typecode"],
            "label": t["cr577_displayname"],
            "color": "#" + t["cr577_colorhex"] if t.get("cr577_colorhex") else None,
            "sortOrder": t.get("cr577_sortorder"),
        }
        for t in types_raw
    }
    acuities = {
        a["cr577_acuitycode"]: {
            "code": a["cr577_acuitycode"],
            "label": a["cr577_displayname"],
            "sortOrder": a.get("cr577_sortorder"),
        }
        for a in acuity_raw
    }

    # --- cleaned section BodyHtml (SecCode -> BodyHtml) ---
    section_html = {}
    with open(SECTIONS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            section_html[row["SecCode"]] = row["BodyHtml"]

    # --- cards, keyed by slug ---
    cards_by_slug = {}
    cards_by_title_lower = {}
    for c in cards_raw:
        slug = c.get("cr577_slug")
        if not slug:
            continue
        title = (c.get("cr577_title") or "").strip()

        system_tags = clean_system(c.get("cr577_system"))
        phase_raw = clean_backtick_list(c.get("cr577_phase"))
        phase_labels = [PHASE_LABELS.get(p, humanize(p)) for p in phase_raw]
        phase_labels = [p for p in phase_labels if p]  # drop n-a/None

        keywords = [
            k.strip() for k in (c.get("cr577_keywordsconcat") or "").split(";") if k.strip()
        ]

        card = {
            "slug": slug,
            "title": title,
            "type": c.get("cr577_type"),
            "acuity": c.get("cr577_acuity"),
            "system": system_tags,
            "phase": phase_labels,
            "condition": c.get("cr577_condition"),
            "procedure": c.get("cr577_procedure"),
            "quickAnswer": clean_markdown_bold(c.get("cr577_quickanswer")),
            "quickAnswerHtml": None,  # filled in below from the "Quick Answer" section, if present
            "keywords": keywords,
            "version": c.get("cr577_version"),
            "lastReviewed": c.get("cr577_lastreviewed"),
            "reviewer": c.get("cr577_reviewer"),
            "sourcePrecedence": c.get("cr577_sourceprecedence"),
            "sections": [],   # filled once CardSection.json is available
            "references": [],
            "related": [],
        }
        cards_by_slug[slug] = card
        if title:
            cards_by_title_lower[title.lower()] = slug

    # --- references, grouped by source card slug ---
    refs_by_card = {}
    for r in refs_raw:
        card_slug = r.get("cr577_cardlookup")
        if not card_slug:
            continue
        refs_by_card.setdefault(card_slug, []).append({
            "refCode": r.get("cr577_refcode"),
            "type": r.get("cr577_referencetype"),
            "citation": r.get("cr577_citationtext"),
            "sortOrder": r.get("cr577_sortorder"),
        })
    for slug, refs in refs_by_card.items():
        if slug in cards_by_slug:
            refs.sort(key=lambda r: (r.get("sortOrder") is None, r.get("sortOrder")))
            cards_by_slug[slug]["references"] = refs

    # --- card sections: structure from the fresh pull, body from the
    # already-cleaned local CSV (joined by SecCode -- ignore BodyHtml in the
    # fresh pull entirely, it's the dirty pre-August-cleanup version) ---
    HEADING_NOTE_RE = re.compile(r"\s*\*?\(expandable(?: in app)?\)\*?\s*", re.IGNORECASE)

    sections_raw = load_json("CardSection.json")
    sections_by_card = {}
    missing_body = 0
    for s in sections_raw:
        seccode = s.get("cr577_seccode")
        card_slug = s.get("cr577_cardlookup")
        if not seccode or not card_slug or card_slug not in cards_by_slug:
            continue
        heading = (s.get("cr577_heading") or "").strip()

        if heading == "Header Metadata":
            continue  # internal authoring note (Title/Version/Status table), not clinical content

        body = section_html.get(seccode)
        if body is None:
            missing_body += 1
            continue

        if heading == "Quick Answer":
            # richer HTML-formatted version of the same text as Card.QuickAnswer
            # (that one's the plain-text tile-preview version) -- surface this
            # one as the detail-page callout instead of duplicating both
            cards_by_slug[card_slug]["quickAnswerHtml"] = body
            continue

        heading_clean = HEADING_NOTE_RE.sub("", heading).strip()
        sections_by_card.setdefault(card_slug, []).append({
            "secCode": seccode,
            "heading": heading_clean,
            "level": s.get("cr577_level"),
            "sortOrder": s.get("cr577_sortorder"),
            "collapsible": (s.get("cr577_iscollapsible") or "").lower() == "yes",
            "bodyHtml": body,
        })
    for slug, secs in sections_by_card.items():
        secs.sort(key=lambda x: (x.get("sortOrder") is None, x.get("sortOrder")))
        cards_by_slug[slug]["sections"] = secs

    # --- related card links: resolve TargetCardTitle -> target slug ---

    # hand-verified concept-name mismatches (checked each against the real
    # Card.json title list before adding -- not a blind fuzzy match). These
    # are genuine word-order/naming differences, not missing cards.
    TITLE_ALIASES = {
        "maze procedure": "maze / cox-maze iv (surgical ablation of atrial fibrillation)",
        "mitral valve replacement": "mitral valve surgery",
        "mitral valve repair/replacement": "mitral valve surgery",
        "cardiac transplantation": "orthotopic heart transplantation (oht)",
        "heart transplant": "orthotopic heart transplantation (oht)",
        "heart transplantation": "orthotopic heart transplantation (oht)",
        "tricuspid valve repair": "tricuspid valve surgery (repair and replacement)",
        "tricuspid valve replacement": "tricuspid valve surgery (repair and replacement)",
        "late tamponade": "late post-op pericardial tamponade",
        "post-operative bleeding workup": "post-op bleeding workup",
        "aortic valve replacement / aortic root replacement": "avr / aortic root replacement — surgery card (deep)",
        "complete heart block / symptomatic bradyarrhythmia": "symptomatic bradyarrhythmia / heart block (post-cardiac surgery)",
    }

    def normalize(s):
        s = (s or "").lower()
        s = re.sub(r"[()\[\]]", " ", s)        # drop parens/brackets, keep inner words
        s = re.sub(r"[/\-–—:,]", " ", s)  # slashes/dashes/colons/commas -> space
        s = re.sub(r"\bpost\s*operative\b", "post op", s)
        s = re.sub(r"\bpostop\b", "post op", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def word_sorted(s):
        return " ".join(sorted(s.split()))

    norm_titles = [(normalize(c["title"]), slug) for slug, c in cards_by_slug.items()]
    sorted_titles = [(word_sorted(t), slug) for t, slug in norm_titles]
    # normalize BOTH sides of the alias table at build time -- comparing a
    # normalized target against a raw (un-normalized) alias key/value was a
    # silent-miss bug caught by testing this against the real title list
    aliases_normalized = {normalize(k): normalize(v) for k, v in TITLE_ALIASES.items()}

    def resolve_target(target_title, relcode):
        if relcode in HEART_FAILURE_OVERRIDES:
            return HEART_FAILURE_OVERRIDES[relcode]
        if not target_title:
            return None
        raw = target_title.strip("*").strip()
        nt = normalize(raw)
        if len(nt) <= 3:
            return None

        if nt in aliases_normalized:
            alias = aliases_normalized[nt]
            for t, slug in norm_titles:
                if t == alias:
                    return slug

        # exact normalized match
        for t, slug in norm_titles:
            if t == nt:
                return slug
        # containment either direction (handles paraphrase / reordered
        # punctuation, e.g. "GI Bleed Post-Cardiac Surgery" vs the real
        # "GI Bleed (Post-Cardiac Surgery)")
        for t, slug in norm_titles:
            if nt in t or t in nt:
                return slug
        # word-order-independent match (handles "A / B" vs "B / A" reversals)
        nts = word_sorted(nt)
        for t, slug in sorted_titles:
            if nts == t:
                return slug
        return None

    unresolved = []
    links_by_card = {}
    for link in links_raw:
        source_slug = link.get("cr577_sourcecardid")
        if not source_slug or source_slug not in cards_by_slug:
            continue
        if (link.get("cr577_isstub") or "").lower() == "yes":
            continue  # stub rows never meant to resolve to a real card
        target_title = link.get("cr577_targetcardtitle")
        relcode = link.get("cr577_relcode")
        target_slug = resolve_target(target_title, relcode)
        if not target_slug:
            # not a bug -- this is a real content gap: the target concept
            # doesn't have a card yet. Drop the dead link rather than force
            # a low-confidence fuzzy match (a wrong link is worse than no
            # link), but record it so we can report what's most-requested.
            unresolved.append((relcode, source_slug, target_title))
            continue
        if target_slug == source_slug:
            continue  # don't let a card link to itself
        links_by_card.setdefault(source_slug, []).append({
            "relCode": relcode,
            "targetSlug": target_slug,
            "category": link.get("cr577_category"),
        })

    for slug, links in links_by_card.items():
        cards_by_slug[slug]["related"] = links

    # --- assemble output ---
    out = {
        "cardTypes": sorted(card_types.values(), key=lambda t: (t["sortOrder"] is None, t["sortOrder"])),
        "acuities": sorted(acuities.values(), key=lambda a: (a["sortOrder"] is None, a["sortOrder"])),
        "cards": list(cards_by_slug.values()),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    print(f"cards: {len(cards_by_slug)}")
    print(f"references attached: {sum(len(c['references']) for c in cards_by_slug.values())}")
    print(f"related links resolved: {sum(len(c['related']) for c in cards_by_slug.values())}")
    print(f"related links UNRESOLVED (target card doesn't exist yet): {len(unresolved)}")
    if unresolved:
        from collections import Counter
        counts = Counter(normalize(t) for _, _, t in unresolved if t)
        top = counts.most_common(25)
        print("  most-requested missing cards (content backlog signal):")
        for title_norm, n in top:
            # show original casing for readability
            orig = next(t for _, _, t in unresolved if normalize(t) == title_norm)
            print(f"    {n:>3}x  {orig}")
        missing_report_path = os.path.join(os.path.dirname(__file__), "..", "data", "missing_cards_report.json")
        with open(missing_report_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"title": t, "count": n} for t, n in counts.most_common()],
                f, indent=2
            )
        print(f"  full report written: {missing_report_path}")
    print(f"sections attached: {sum(len(c['sections']) for c in cards_by_slug.values())} / {len(sections_raw)}")
    if missing_body:
        print(f"  sections with NO cleaned BodyHtml match (SecCode not found in the Aug CSV): {missing_body}")
    cards_with_no_sections = [c["title"] for c in cards_by_slug.values() if not c["sections"]]
    if cards_with_no_sections:
        print(f"  cards with ZERO sections attached: {len(cards_with_no_sections)}")
        for t in cards_with_no_sections[:10]:
            print("    ", t)
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
