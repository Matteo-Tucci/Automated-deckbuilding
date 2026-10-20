import argparse
from collections import Counter
import json
import sqlite3
from pathlib import Path

from constants import DB_PATH, TAGS


def fitness (individual):
    tags = dict.fromkeys(TAGS, 0)
    tags.update({
        "item": 0,
        "character": 0,
        "action": 0,
        "location": 0,
        "alert": 0,
        "bodyguard": 0,
        "boost": 0,
        "challenger": 0,
        "evasive": 0,
        "reckless": 0,
        "resist": 0,
        "rush": 0,
        "shift": 0,
        "singer": 0,
        "support": 0,
        "vanish": 0,
        "ward": 0,
        "sing together": 0,
        "universal shift": 0,
        "combo shift": 0,
        "duo shift": 0,
        "temporary shift": 0,
        "potato shift": 0,
        "tap_synergy": 0,
        "lore_ramp": 0,
        "songs": 0,
        "duo_shift": 0
    })
    fit = 0;
    avgcost = 0;
    inkpercentage = 0;
    draw_removal_cards = 0
    card_type_counts = {}
    for card in individual:
        count = sum(other_card[0] == card[0] for other_card in individual)
        if (count > 4):
            return -100
        avgcost = avgcost + card[4]
        if card[3] is True:
            inkpercentage += 1

        card_tags = json.loads(card[2])
        card_type = (card[5] or "").lower()
        card_type_counts[card_type] = card_type_counts.get(card_type, 0) + 1
        if "draw" in card_tags or "removal" in card_tags:
            draw_removal_cards += 1
        for tag in card_tags:
            if tag in tags:
                tags[tag] += 1

    if draw_removal_cards < 10:
        fit -= 1
    for synergy_tag, required_type in {
        "singer": "song",
        "song_synergy": "song",
        "action_synergy": "action",
        "item_synergy": "item",
    }.items():
        if card_type_counts.get(required_type, 0) < tags[synergy_tag]:
            fit -= 0.5

    avgcost = avgcost / len(individual)
    inkpercentage = (inkpercentage / len(individual) )*100
    if (inkpercentage >= 75):
        fit +=1
    ###################
    ##damaged section##
    ###################
    if (50 <= tags["evasive"] + tags["healing"] + tags["challenger"] >= 30):
        if (2.5 <= avgcost <= 3):
            fit +=1
        fit = fit + (tags["evasive"] + tags["healing"] + tags["challenger"])/10 - 2
    ###################
    ##elinor section##
    ###################
    if (50 <= tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"] >= 30): #tap synery non esiste, fallo
        if (2 <= avgcost <= 2.5):
            fit +=1
        fit = fit + (tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"])/10 - 2
    ###################
    ##detectives section##
    ###################
    if (50 <= tags["removal"] + tags["evasive"] + tags["bodyguard"] >= 30):
        if (2.5 <= avgcost <= 2.9):
            fit +=1
        fit = fit + (tags["removal"] + tags["evasive"] + tags["bodyguard"])/10 - 2
    ###################
    ##m&m section##
    ###################
    if (50 <= tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"] >= 30):
        if (3.8 <=avgcost <= 4.3):
            fit +=1
        fit = fit + (tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"])/10 - 2
    ###################
    ##midrange section##
    ###################
    if (50 <= tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"] >= 30):
        if (3 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"])/10 - 2
    ###################
    ##retro section##
    ###################
    if (50 <= tags["ramp"] + tags["character"] >= 30):
        if (4 <= avgcost <= 5):
            fit +=1
        fit = fit + (tags["ramp"] + tags["character"])/10 - 2
    ###################
    ##songs section##
    ###################
    if (50 <= tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["hero_recursion"] + tags["nonhero_recursion"] >= 30):
        if (3.5 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["hero_recursion"] + tags["nonhero_recursion"])/10 - 2
    ###################
    ##actions section##
    ###################
    if (50 <= tags["action"] + tags["songs"] + tags["draw"] + tags["item"] + tags["lore_gain"] - tags["character"] >= 30):
        if (2.6 <= avgcost <= 3.4):
            fit +=1
        fit = fit + (tags["action"] + tags["songs"] + tags["draw"] + tags["item"] + tags["lore_gain"] - tags["character"])/10 - 2
    ###################
    ##boost section##
    ###################
    if (50 <= tags["boost"] + tags["removal"] + tags["draw"] + tags["lore_gain"] >= 30):
        if (3 <= avgcost <= 3.5):
            fit +=1
        fit = fit + (tags["boost"] + tags["removal"] + tags["draw"] + tags["lore_gain"])/10 - 2
    return fit


def _parse_line(line, line_number):
	parts = line.strip().split(maxsplit=1)
	if len(parts) != 2:
		raise ValueError(f"line {line_number}: expected '<quantity> <card name>'")

	try:
		quantity = int(parts[0])
	except ValueError as error:
		raise ValueError(f"line {line_number}: quantity must be an integer") from error

	if quantity <= 0:
		raise ValueError(f"line {line_number}: quantity must be positive")

	card_name = parts[1].strip()
	if not card_name:
		raise ValueError(f"line {line_number}: card name is missing")

	return quantity, card_name


def load_individual(deck_path, db_path=DB_PATH):
	"""Load a deck-list file as an individual compatible with builder.py."""
	deck_path = Path(deck_path)
	quantities = {}

	for line_number, line in enumerate(
		deck_path.read_text(encoding="utf-8").splitlines(), start=1
	):
		if not line.strip():
			continue

		quantity, card_name = _parse_line(line, line_number)
		key = card_name.casefold()
		if key not in quantities:
			quantities[key] = [card_name, 0, line_number]
		quantities[key][1] += quantity

	if not quantities:
		raise ValueError("the deck list is empty")

	individual = []
	with sqlite3.connect(db_path) as connection:
		for card_name, quantity, line_number in quantities.values():
			row = connection.execute(
				"""
				SELECT id, color, tags, card_json
				FROM cards
				WHERE fullName = ? COLLATE NOCASE
				""",
				(card_name,),
			).fetchone()

			if row is None:
				raise ValueError(
					f"line {line_number}: card not found: {card_name}"
				)
			card = json.loads(row[3])
			card_tuple = (
				row[0],
				row[1],
				row[2],
				card.get("inkwell"),
				card.get("cost"),
				card.get("type"),
			)
			individual.extend([card_tuple] * quantity)

	return individual


def card_difference(first_individual, second_individual):
    if not second_individual:
        raise ValueError("second individual cannot be empty")

    first_counts = Counter(card[0] for card in first_individual)
    second_counts = Counter(card[0] for card in second_individual)
    total = sum(
        min(count, second_counts[card_id])
        for card_id, count in first_counts.items()
    )
    return 1 - (total / len(second_individual))


def main():
    parser = argparse.ArgumentParser(description="Create a builder-compatible individual.")
    parser.add_argument("deck_file", type=Path, help="path to the deck-list text file")
    args = parser.parse_args()

    try:
        individual = load_individual(args.deck_file)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))

    print(f"Fitness: {fitness(individual)}")
    print(f"Card difference: {card_difference(individual, individual)}")


if __name__ == "__main__":
	main()




