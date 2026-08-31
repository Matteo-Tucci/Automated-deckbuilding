import json
from shutil import copy
import sqlite3
from pathlib import Path
import re
from tokenize import group

WORDS = r"[\w' !?.-]+"
TAGS = {
	"draw": rf"(draw {WORDS} cards?)|(and put it into (your|their) hand)|(draw cards equal to)",
	#type and keyword to be done separately
	"discard": rf"(discard {WORDS} cards?)",
	"ramp":rf"(play {WORDS} for free)|(pay \d ⬡ less)|(cost \d ⬡ less)|(into your inkwell)", #includes cost reduction
	"hero_recursion": rf"return a character card {WORDS}? from (your|their) discard to (your|their) hand",
	"nonhero_recursion": rf"return a(n?) (item|song|action|location) card {WORDS}? from (your|their) discard to (your|their) hand",
	"heal_synergy": r"(whenever you remove damage)|(whenever damage is removed)|(if you removed \d damage)",
	"adventure_synergy": rf"whenever {WORDS} quests",
	"color_synergy": r"\b(?:Amber|Amethyst|Emerald|Ruby|Sapphire|Steel)\b",
	"powerup_synergy": rf"(with a card under them)|(put {WORDS} face down under one of your characters)",
	"discard_synergy": r"(when you discard this card)|((when|whenever) you discard a card)|(if you discarded a card this turn)",
	"mill_synergy": rf"if {WORDS} were put in your discard this turn",
	"vanilla": r"useless", #ricorda di riempire il campo, da DB non esiste nel json, non volevo metterlo void o null
	"lore_gain": r"(gain \d+ ◊)|(gain \d+ lore)", #vediamo se conviene tenerli separati
	"lore_buff": rf"(give {WORDS} \+\d+ ◊)|(get(s?) \+\d+ ◊)",
	"protection": r"(opponent can't ready more than one)|(opposing characters? can't challenge and must quest)",
	"untap": rf"(ready this character)|(ready chosen ((characters?)|(items?)))|(ready your {WORDS} characters?)",
	"removal": rf"(exert (target|each|every|all)? opposing (characters?|item))|(banish (target|each|every|all)? (opposing|chosen) (characters?|location|items?))|(return (chosen (characters?|items?|locations?))? to their player's hand)|(deal \d+ damage to)|(deal damage to {WORDS} equal to)|(move up to \d+ damage from chosen (character|location) to chosen opposing (character|location))|(can't ready at the start of their next turn)",
	"debuff": r"(opposing characters? gets? -\d+ ¤)",
	"group_hug": r"each player",
	"banish_trigger": rf"when {WORDS} (is|and) banished",
	"buff_toughness": r"(this)? characters? get \+\d+ ⛉",
	"buff_attack": r"(this)? characters? get \+\d+ ¤",
	"tap_enemy": r"exert chosen opposing (character|item)",
	"burn": r"(move up to \d+ damage from chosen (character|location) to chosen opposing (character|location))|(deal \d+ damage to each)",
	"self_burn": r"(deal \d+ damage to each of your (?:other )?characters)|(enters play with \d+ damage)",
	"movement": rf"move {WORDS} character(s?) {WORDS} for free",
	"mill": r"put the top \d+ cards of your deck into your discard",
	"healing": r"(remove (?:up to )?\d+ damage from)|(move (:?up to )?\d+ damage from)",
	"wipe": r"banish (all|each|every)",
    "stax": rf"(opponents? (:? {WORDS})* discards?)|(opponents? loses? \d (lore|◊))",
}
DB_PATH = Path("db") / "cards.db"
JSON_PATH = Path("db") / "allCards.json"


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
    combined_tags = list(dict.fromkeys([*matched.keys(), *keyword_tags]))
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