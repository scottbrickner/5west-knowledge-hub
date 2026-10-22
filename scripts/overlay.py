"""
Hand-authored additions layered on top of the Dataverse-built cards.json.

build_data.py rebuilds cards.json from the Dataverse exports, which would wipe
anything edited directly in the JSON. Content that lives only in this repo
(cards and links for standalone pages like /u-drape-sternotomy/) goes here
instead, and build_data.py applies it as its last step.

Codes use an "X" prefix (SX…, RCX…, RX…) so they never collide with
Dataverse-issued codes. apply_overlay() is idempotent.

Run on the existing cards.json without a full rebuild:
    python3 scripts/overlay.py
"""
import json
import os

RED = 'style="color:#6B0000"'
GUIDE = "u-drape-sternotomy/"  # relative to the hub root (index.html)


def guide_button(text="Open the illustrated U-drape guide"):
    return (f'<p><a href="{GUIDE}" target="_blank" rel="noopener"><strong>{text} &rarr;</strong></a></p>')


U_DRAPE_CARD = {
    "slug": "u_drape_bedside_sternotomy_protocol",
    "title": "U-Drape Placement for Bedside Sternotomy",
    "type": "protocol",
    "acuity": "emergent",
    "system": ["Cardiac", "Cross-System"],
    "phase": ["POD 0", "POD 1–3", "POD 4+"],
    "condition": ["emergent sternotomy tamponade", "emergent sternotomy bleeding", "post op cardiac arrest"],
    "procedure": ["all cardiac surgery"],
    "quickAnswer": (
        "Medline orthopedic split drape (REF DYNJP8301). SPLIT END arrow points to the head. "
        "Lay the folded pack with its left edge on the sternal incision, top edge at the notch, so the first unfold "
        "lands centered. Unfold side to side (UNFOLD ⇦ ⇨), then toward the feet (UNFOLD ⇩). "
        "Peel the liners, open the split tails toward the head, and seal the U from notch to xiphoid. "
        "Prep with povidone-iodine only (SCU 10-214): no CHG/alcohol sticks, whose vapor is fuel under the drape."
    ),
    "quickAnswerHtml": (
        "<blockquote><p>Medline orthopedic split drape (REF DYNJP8301). "
        f"<strong {RED}>SPLIT END arrow points to the head.</strong> "
        f"Lay the folded pack with its <strong {RED}>left edge on the sternal incision</strong>, top edge at the notch, "
        "so the first unfold lands centered. Unfold side to side (UNFOLD ⇦ ⇨), then toward the feet (UNFOLD ⇩). "
        "Peel the liners, open the split tails toward the head, and seal the U from notch to xiphoid. "
        f"<strong {RED}>Prep with povidone-iodine only</strong> (SCU 10-214): no CHG/alcohol sticks, whose vapor is fuel under the drape.</p></blockquote>"
        + guide_button()
    ),
    "keywords": [
        "U drape", "U-drape", "split drape", "orthopedic split drape", "DYNJP8301", "Medline drape",
        "sterile drape", "draping", "resternotomy drape", "open chest drape", "sterile field",
        "emergent resternotomy", "open-chest code", "CALS", "chest prep",
    ],
    "version": "1.0",
    "lastReviewed": "2026-10-22",
    "reviewer": "Scott Brickner, MSN, RN, CCRN",
    "sourcePrecedence": "SCU 10-214 Emergent Sternotomy and Resuscitation of the Post-Op Cardiac Surgery Patient → surgeon direction → Medline DYNJP8301 package labeling",
    "sections": [
        {
            "secCode": "SX0001", "heading": "1. Snapshot / What It Is", "level": 2, "sortOrder": 1, "collapsible": False,
            "bodyHtml": (
                "<p>The U (split) drape builds the sterile field for an emergent bedside resternotomy. Its 6″ × 40″ split "
                "frames the sternum from notch to xiphoid and covers the rest of the patient, arm to arm and down to the feet.</p>"
                "<ul><li><strong>Product:</strong> Medline orthopedic split drape, REF DYNJP8301 — 77″ × 108″, "
                "AAMI PB70 Level 4, EO sterile, single use, not made with natural rubber latex.</li>"
                "<li><strong>Who:</strong> a gowned, gloved team member places it; the circulating RN opens the pack and preps the skin per policy.</li>"
                "<li><strong>Follow the print:</strong> the drape is labeled SPLIT END, UNFOLD ⇦ ⇨ and UNFOLD ⇩ in the order you use them.</li></ul>"
                + guide_button()
            ),
        },
        {
            "secCode": "SX0002", "heading": "2. Before the Drape", "level": 2, "sortOrder": 2, "collapsible": False,
            "bodyHtml": (
                "<ul><li>Gown and dressings off; expose neck to umbilicus and side to side.</li>"
                "<li>Move ECG electrodes off the sternum; keep defib pads and pacing wires connected.</li>"
                f"<li>Skin prep with <strong {RED}>povidone-iodine only</strong>, scrubbed over the incision and wide across the chest (SCU 10-214).</li>"
                "<li>No CHG/alcohol prep sticks: their vapor is fuel under the drape. Blot any pooling at the sides or under the shoulders.</li>"
                "<li>Coordinate with the compressor and surgeon; prep and drape around CPR unless told to pause.</li></ul>"
            ),
        },
        {
            "secCode": "SX0003", "heading": "3. Steps", "level": 2, "sortOrder": 3, "collapsible": False,
            "bodyHtml": (
                "<ol>"
                "<li><strong>Check the pack.</strong> REF DYNJP8301; intact, dry, in date.</li>"
                "<li><strong>Find the split end.</strong> The SPLIT END arrow points to the patient's head.</li>"
                f"<li><strong>Line the edge up with the incision.</strong> Folded pack's <strong {RED}>left edge on the sternal incision</strong>, top edge at the notch. The pack is folded off-center on purpose.</li>"
                "<li><strong>Unfold side to side.</strong> First unfold crosses the incision and lands centered as three panels; open the UNFOLD ⇦ ⇨ panels toward the arms.</li>"
                "<li><strong>Unfold toward the feet.</strong> Follow UNFOLD ⇩ over the abdomen and legs. Anything below the bed edge is no longer sterile.</li>"
                "<li><strong>Find the U and its tape.</strong> White printed liners cover the adhesive on both tails and the base of the U. White tabs lower down are cord holders.</li>"
                "<li><strong>Peel and open the split.</strong> Peel the liners, open the tails toward the head on each side of the sternum, press adhesive to dry skin from the base upward.</li>"
                "<li><strong>Check the window.</strong> U frames notch to xiphoid, edges sealed, ETT and lines outside the field. Call out “draped.”</li>"
                "</ol>" + guide_button("See every step illustrated")
            ),
        },
        {
            "secCode": "SX0004", "heading": "4. Pitfalls & Pearls", "level": 2, "sortOrder": 4, "collapsible": False,
            "bodyHtml": (
                "<ul><li><strong>Upside down:</strong> the U ends up over the abdomen. Check the SPLIT END arrow before the drape touches skin.</li>"
                "<li><strong>Off center:</strong> one edge of the window sits on the sternum. Set the pack's left edge on the incision, not the middle of the pack; don't slide it after.</li>"
                "<li><strong>Peeled too early:</strong> tape grabs the wrong spot. Peel only once the U is lined up.</li>"
                "<li><strong>Reaching across:</strong> hands and sleeves stay above the field. Walk around instead.</li>"
                f"<li><strong {RED}>Fire risk:</strong> cautery, defibrillation and 100% oxygen meet under the drape. Keck preps with povidone-iodine only so there is no alcohol vapor for them to ignite. The package carries a flammability caution.</li></ul>"
            ),
        },
    ],
    "references": [
        {"refCode": "RX0001", "type": "policy",
         "citation": "Keck Hospital of USC / USC Norris Cancer Hospital. (2023). *Emergent sternotomy and resuscitation of the post-op cardiac surgery patient* (Policy SCU 10-214; reviewed 10/10/2023) [Operating policy].", "sortOrder": 0},
        {"refCode": "RX0002", "type": "guideline",
         "citation": "Medline Industries, LP. (2025). *Orthopedic split drape with 6\" × 40\" split (REF DYNJP8301)* [Package labeling].", "sortOrder": 1},
    ],
    "related": [
        {"relCode": "RCX0001", "targetSlug": "bedside_sternotomy_scenario", "category": "Scenario"},
        {"relCode": "RCX0002", "targetSlug": "postop_bleeding_scenario", "category": "Scenario"},
        {"relCode": "RCX0003", "targetSlug": "tamponade_late_scenario", "category": "Scenario"},
    ],
}

# Sections spliced into existing Dataverse cards: (target slug, insert after secCode, section)
INJECT_SECTIONS = [
    ("bedside_sternotomy_scenario", "S00420", {
        "secCode": "SX0101", "heading": "7.1a Draping with the U-drape", "level": 3, "sortOrder": 17.5, "collapsible": True,
        "bodyHtml": (
            "<p>The cart's sterile drape is the Medline orthopedic split drape (REF DYNJP8301). "
            f"<strong {RED}>SPLIT END arrow to the head; folded pack's left edge on the sternal incision</strong> so the first unfold lands centered. "
            "Unfold ⇦ ⇨, then ⇩, peel the liners and seal the U from notch to xiphoid. Prep with povidone-iodine only.</p>"
            + guide_button()
        ),
    }),
    ("postop_bleeding_scenario", "S02206", {
        "secCode": "SX0102", "heading": "6A. If it becomes a bedside resternotomy", "level": 3, "sortOrder": 9.5, "collapsible": False,
        "bodyHtml": (
            "<p>Meeting re-exploration criteria with instability can turn this into an open-chest code at the bedside. "
            "See the <a href=\"#/card/bedside_sternotomy_scenario\">Emergent Bedside Sternotomy</a> card for the full response, and the "
            "<a href=\"#/card/u_drape_bedside_sternotomy_protocol\">U-Drape Placement</a> card for setting up the sterile field.</p>"
            + guide_button()
        ),
    }),
]

INJECT_RELATED = [
    ("bedside_sternotomy_scenario", {"relCode": "RCX0101", "targetSlug": "u_drape_bedside_sternotomy_protocol", "category": "Protocol"}),
    ("postop_bleeding_scenario", {"relCode": "RCX0102", "targetSlug": "u_drape_bedside_sternotomy_protocol", "category": "Protocol"}),
]


def apply_overlay(out):
    cards = out["cards"]
    by_slug = {c["slug"]: c for c in cards}

    if U_DRAPE_CARD["slug"] in by_slug:
        cards[cards.index(by_slug[U_DRAPE_CARD["slug"]])] = U_DRAPE_CARD
    else:
        cards.append(U_DRAPE_CARD)
    by_slug[U_DRAPE_CARD["slug"]] = U_DRAPE_CARD

    for slug, after, sec in INJECT_SECTIONS:
        card = by_slug.get(slug)
        if not card:
            print(f"overlay: card {slug} not found, skipped section {sec['secCode']}")
            continue
        card["sections"] = [s for s in card["sections"] if s["secCode"] != sec["secCode"]]
        idx = next((i for i, s in enumerate(card["sections"]) if s["secCode"] == after), len(card["sections"]) - 1)
        card["sections"].insert(idx + 1, sec)

    for slug, rel in INJECT_RELATED:
        card = by_slug.get(slug)
        if not card:
            print(f"overlay: card {slug} not found, skipped related {rel['relCode']}")
            continue
        card["related"] = [r for r in card["related"] if r["relCode"] != rel["relCode"]] + [rel]

    print(f"overlay: applied ({len(INJECT_SECTIONS)} sections, {len(INJECT_RELATED)} related links, 1 card)")
    return out


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    apply_overlay(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=None, separators=(",", ":"))
