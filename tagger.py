import json
import sqlite3
from pathlib import Path

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
	INSERT OR REPLACE INTO cards
	(id, fullName, code, color, card_json, tags)
	VALUES (?, ?, ?, ?, ?, ?)
	""",
	rows,
)

conn.commit()
conn.close()

print(f"Inserted {len(rows)} cards into 'cards' where Core.allowed is true.")

