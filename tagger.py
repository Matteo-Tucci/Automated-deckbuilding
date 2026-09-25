import json
from shutil import copy
import sqlite3
from pathlib import Path
import re
from tokenize import group
from constants import TAGS, DB_PATH, JSON_PATH



def flatten_effect_text(card: dict):
    abilities = card.get("abilities") or []
    if not abilities:
        return "useless", ""

    effects = []
    keywords = []

    for ability in abilities:
        effect = ability.get("fullText")
        keyword = ability.get("keyword")

        if effect is not None:
            if isinstance(effect, list):
                effects.extend(effect)
            else:
                effects.append(effect)

        if keyword is not None:
            if isinstance(keyword, list):
                keywords.extend(keyword)
            else:
                keywords.append(keyword)

    if not (effects or keywords):
        raise ValueError(f'Card {card.get("fullName")} has no "fullText" or "keyword" ability text')

    return (
        re.sub(r"\s+", " ", " ".join(effects)).strip(),
        re.sub(r"\s+", " ", " ".join(keywords)).strip()
    )

##populating the db
with open(JSON_PATH, "r", encoding="utf-8") as f:
	data = json.load(f)

cards = data["cards"]
allowed_cards = [
	card
	for card in cards
	if card.get("allowedInFormats", {}).get("Core", {}).get("allowed") is True
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute(
	"""
	CREATE TABLE IF NOT EXISTS cards (
		id INTEGER PRIMARY KEY,
		fullName TEXT,
		code TEXT,
		color TEXT,
		card_json TEXT,
		tags TEXT
	)
	"""
)


cursor.execute(
	"""
	CREATE UNIQUE INDEX IF NOT EXISTS ux_cards_fullname
	ON cards(fullName)
	"""
)

rows = [
	(
		card["id"],
		card.get("fullName"),
		card.get("code"),
		card.get("color"),
		json.dumps(card, ensure_ascii=False),
		json.dumps({}),
	)
	for card in allowed_cards
]

cursor.executemany(
	"""
	INSERT OR IGNORE INTO cards
	(id, fullName, code, color, card_json, tags)
	VALUES (?, ?, ?, ?, ?, ?)
	""",
	rows,
)

conn.commit()


print(f"Processed {len(rows)} cards where Core.allowed is true.")

##tagging process
cursor.execute(
	"""
	SELECT id, card_json
	FROM cards
	"""
)
rows = cursor.fetchall()

compiled = {
	name: re.compile(rx, re.IGNORECASE) for name, rx in TAGS.items()
}
updated_rows = []
for row in rows:
    text = flatten_effect_text(json.loads(row[1]))
    matched = {
		name: m.group(0)
		for name, rx in compiled.items()
		if (m := rx.search(text[0]))
	}

    raw_keyword_text = text[1] or ""
    keyword_tags = [
        tag.strip()
        for tag in re.split(r"[\s,]+", raw_keyword_text.lower())
        if tag.strip()
    ]
    card_type = json.loads(row[1]).get("type")
    type_tag = card_type.lower() if isinstance(card_type, str) else None
    combined_tags = list(
        dict.fromkeys(
            [*matched.keys(), *keyword_tags, *([type_tag] if type_tag else [])]
        )
    )
    updated_rows.append((row[0], json.dumps(combined_tags, ensure_ascii=False)))

cursor.executemany(
	"""
	UPDATE cards
	SET tags = ?
	WHERE id = ?
	""",
	[(tags, cardid) for cardid, tags in updated_rows],
)

print(f"all {len(rows)} cards tagged")
conn.commit()
conn.close()