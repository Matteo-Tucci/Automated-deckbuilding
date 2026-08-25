import json
import sqlite3
from pathlib import Path
import re

TAGS = {
	"draw": r"(draw [A-Za-z1-9]+(?: [A-Za-z1-9]+)* card[s?])|(and put it into your hand)",
	#type and keyword to be done separately
	"discard": r"(discard [A-Za-z1-9]+(?: [A-Za-z1-9]+)* card[s?])",
	"ramp":r"(play [A-Za-z1-9]+(?: [A-Za-z1-9]+)* for free)|(pay \d ⬡ less)|(cost \d ⬡ less)" #includes cost reduction
	"hero_recursion":
	"nonhero_recursion":
	"heal_synergy":
	"adventure_synergy":
	"toughness_synergy":
	"color_synergy":
	"discard_synergy":
	"mill_synergy":
	"vanilla": r"useless", #ricorda di riempire il campo, da DB non esiste nel json
	"lore_gain":
	"protection":
	"untap":
	"removal":
	"deuff":
	"group_hug": "each player",
	"exile_trigger":
	"buff_toughness":
	"buff_attack":
	"tap_enemy":
	"burn":
	"self_burn":
	"movement":
	"mill":
	"healing":
	"wipe": r"banish (all|each|every)",
}
DB_PATH = Path("db") / "cards.db"
JSON_PATH = Path("db") / "allCards.json"


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
conn.close()

print(f"Processed {len(rows)} cards where Core.allowed is true.")