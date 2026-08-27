import json
import sqlite3
from pathlib import Path
import re

TAGS = {
	"draw": r"(draw [A-Za-z1-9]+(?: [A-Za-z1-9]+)* card(s?))|(and put it into (your|their) hand)",
	#type and keyword to be done separately
	"discard": r"(discard [A-Za-z1-9]+(?: [A-Za-z1-9]+)* card(s?))",
	"ramp":r"(play [A-Za-z1-9]+(?: [A-Za-z1-9]+)* for free)|(pay \d ⬡ less)|(cost \d ⬡ less)", #includes cost reduction
	"hero_recursion": r"return a character card from (your|their) discard to (your|their) hand",
	"nonhero_recursion": r"return a(n?) (item|song|action|location) card from (your|their) discard to (your|their) hand",
	"heal_synergy": r"(whenever you remove damage)|(whenever damage is removed)|(if you removed \d damage)",
	"adventure_synergy": r"whenever [A-Za-z1-9]+(?: [A-Za-z1-9]+)* quests",
	"color_synergy": r"Amber|Amethyst|Emerald|Ruby|Sapphire|Steel",
	"powerup_synergy": r"(with a card under them)|(put [A-Za-z1-9]+(?: [A-Za-z1-9]+)* face down under one of your characters)",
	"discard_synergy": r"(when you discard this card)|((when|whenever) you discard a card)|(if you discarded a card this turn)",
	"mill_synergy": r"if [A-Za-z1-9]+(?: [A-Za-z1-9]+)* were put in your discard this turn",
	"vanilla": r"useless", #ricorda di riempire il campo, da DB non esiste nel json, non volevo metterlo void o null
	"lore_gain": r"(gain \d ◊)|(gain \d lore)", #vediamo se conviene tenerli separati
	"lore_buff": r"(give [A-Za-z1-9]+(?: [A-Za-z1-9]+)* \+\d ◊)|(get(s?) \+\d ◊)",
	"protection": r"(opponent can't ready more than one)|(opposing character(s?) can't challenge and must quest)",
	"untap": r"(ready this character)|(ready chosen ((character(s?))|(item(s?))) of yours)",
	"removal": r"(exert [A-Za-z1-9]+(?: [A-Za-z1-9]+)* opposing (character(s?)|item))|(banish [A-Za-z1-9]+(?: [A-Za-z1-9]+)* opposing (character(s?)|location|item(s?)))|(return [A-Za-z1-9]+(?: [A-Za-z1-9]+)* to their player's hand)|(deal \d? damage to)|(deal damage to [A-Za-z1-9]+(?: [A-Za-z1-9]+)* equal to)|(move up to \d damage from chosen (character|location) to chosen opposing (character|location))|(can't ready at the start of their next turn)",
	"deuff": r"(opposing character(s?) get(s?) -\d ¤)",
	"group_hug": r"each player",
	"banish_trigger": r"when [A-Za-z1-9]+(?: [A-Za-z1-9]+)* (is|and) banished",
	"buff_toughness": r"characters get \+\d ⛉",
	"buff_attack": r"characters get \+\d ¤",
	"tap_enemy": r"exert chosen opposing (character|item)",
	"burn": r"(move up to \d damage from chosen (character|location) to chosen opposing (character|location))|(deal \d damage to each)",
	"self_burn": r"(deal \d damage to each of your (other)? characters)|(enters play with \d damage)",
	"movement": r"move [A-Za-z1-9]+(?: [A-Za-z1-9]+)* character(s?) [A-Za-z1-9]+(?: [A-Za-z1-9]+)* for free",
	"mill": r"put the top \d cards of your deck into your discard",
	"healing": r"(remove (up?) to \d damage from)|(move up to \d damage from)",
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