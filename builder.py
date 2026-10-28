from pyeasyga import pyeasyga
import json
import random
import sqlite3
from pathlib import Path
from constants import TAGS, DB_PATH
#9-13
#gioca coi parametri, cerca di faRLO CONVERGERE E eventualmente cambia la mutazione
#####COLORS FOR THE DECK########
color1 = "Steel"
color2 = "Emerald"

def create_individual(data):
    leng = random.randint(60, 65)
    if not data:
        raise ValueError("Cannot create an individual from empty data")

    core_size = min(8, len(data))
    core_cards = random.sample(data, core_size)
    individual = [card for card in core_cards for _ in range(4)]
    individual.extend(data[random.randrange(len(data))] for _ in range(leng - len(individual)))
    return individual
#mutazione normale, uno alla volta
#def mutate(individual):
#    individual[random.randrange(len(individual))] = random.choice(data)
def mutate(individual):
    first_index, second_index = random.sample(range(len(individual)), 2)
    card = random.choice(data)

    individual[first_index] = card
    individual[second_index] = card

def print_card_names(individual, rows):
    card_names = {
        row[0]: json.loads(row[3]).get("fullName")
        for row in rows
    }
    card_counts = {}
    for card in individual:
        card_id = card[0]
        card_counts[card_id] = card_counts.get(card_id, 0) + 1

    for card_id, count in sorted(card_counts.items(), key=lambda item: card_names[item[0]]):
        print(f"{count} {card_names[card_id]}")

def fitness (individual, data):
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
    full_names_by_base = {}
    shifted_base_names = set()
    for card in individual:
        count = sum(other_card[0] == card[0] for other_card in individual)
        if (count > 4):
            return -100
        avgcost = avgcost + card[4]
        if card[3] is True:
            inkpercentage += 1

        ##shift check##
        card_tags = json.loads(card[2])
        if len(card) > 6 and isinstance(card[6], str):
            full_name = card[6].strip().casefold()
            base_name = full_name.split(" - ", 1)[0]
            full_names_by_base.setdefault(base_name, set()).add(full_name)
            if "shift" in card_tags:
                shifted_base_names.add(base_name)
        ######
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
        "location_synergy": "location",
    }.items():
        if card_type_counts.get(required_type, 0) < tags[synergy_tag]:
            fit -= 0.5
    for base_name in shifted_base_names:
        if len(full_names_by_base[base_name]) < 2:
            fit -= 0.5

    avgcost = avgcost / len(individual)
    inkpercentage = (inkpercentage / len(individual) )*100
    if (inkpercentage >= 75):
        fit +=1
    ###################
    ##damaged section##
    ###################
    if (40 <= tags["evasive"] + tags["give_evasive"] + tags["removal"] + tags["challenger"] + tags["tap_enemy"] + tags["lore_gain"] + tags["lore_buff"] + tags["healing"] <= 60):
        if (2.5 <= avgcost <= 3.5):
            fit +=1
        fit = fit + (tags["evasive"] + tags["give_evasive"] + tags["removal"] + tags["challenger"] + tags["tap_enemy"] + tags["lore_gain"] + tags["lore_buff"] + tags["healing"])/10 - 2
    ###################
    ##elinor section##
    ###################
    if (40 <= tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"] + tags["lore_gain"] + tags["adventure_synergy"] + tags["protection"] + tags["character"]*0.8 <= 60):
        if (2 <= avgcost <= 2.6):
            fit +=1
        fit = fit + (tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"] + tags["lore_gain"] + tags["adventure_synergy"] + tags["protection"] + tags["character"]*0.8)/10 - 2
    ###################
    ##detectives section##
    ###################
    if (40 <= tags["removal"] + tags["evasive"] + tags["give_evasive"] + tags["bodyguard"] <= 60):
        if (2.5 <= avgcost <= 2.9):
            fit +=1
        fit = fit + (tags["removal"] + tags["evasive"] + tags["give_evasive"] + tags["bodyguard"])/10 - 2
    ###################
    ##m&m section##
    ################### commentata perchè generica ed è solo quelle tre carte
    """
    if (40 <= tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"] <= 60):
        if (3.8 <=avgcost <= 4.3):
            fit +=1
        fit = fit + (tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"])/10 - 2
    """
    ###################
    ##midrange section##
    ###################
    if (40 <= tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"] + tags["challenger"] + tags["healing"] + tags["bounce"] <= 60):
        if (3 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"] + tags["challenger"] + tags["healing"] + tags["bounce"])/10 - 2
    ###################
    ##retro section##
    ###################
    if (40 <= tags["ramp"]*0.8 + tags["character"]*0.9 + tags["item"] + tags["draw"] + tags["removal"] <= 60):
            if (4 <= avgcost <= 5):
                fit +=1
            fit = fit + (tags["ramp"]*0.8 + tags["character"]*0.9 + tags["item"] + tags["draw"] + tags["removal"])/10 - 2
    ###################
    ##songs section##
    ###################
    if (40 <= tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["songs"] + tags["song_synergy"] + tags["draw"] <= 60):
        if (3.5 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["songs"] + tags["song_synergy"] + tags["draw"])/10 - 2
    ###################
    ##actions section##
    ###################
    if (50 <= tags["action"]*0.5 + tags["song_synergy"] + tags["draw"] + tags["item"]*0.5 + tags["lore_gain"] + tags["removal"] - tags["character"]*2 <= 75):
            if (2.6 <= avgcost <= 3.4):
                fit +=1
            fit = fit + (tags["action"]*0.5 + tags["song_synergy"] + tags["draw"] + tags["item"]*0.5 + tags["lore_gain"] + tags["removal"] - tags["character"]*2)/10 - 2
    ###################
    ##boost section##
    ###################
    if (40 <= tags["boost"] + tags["removal"] + tags["draw"] + tags["lore_gain"] <= 60):
        if (3 <= avgcost <= 3.5):
            fit +=1
        fit = fit + (tags["boost"] + tags["removal"] + tags["draw"] + tags["lore_gain"])/10 - 2
    return fit


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

#guarda se serve anche il resto della carta
cursor.execute(
	"""
    SELECT id, color, tags, card_json
	FROM cards
	"""
)
rows = cursor.fetchall()
conn.commit()
conn.close()

data = [] #we only get the right colors, to help mutation and crossover
for item in rows:
    card = json.loads(item[3])
    if (color1 == color2): #monocolored deck
        if (item[1] in color1):
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type"), card.get("fullName")))
    else: #double colored deck
        card_colors = set(item[1].split("-"))
        if card_colors <= {color1, color2}:
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type"), card.get("fullName")))

ga = pyeasyga.GeneticAlgorithm(
    data,
    population_size=200,
    generations=400,
    crossover_probability=0.2,
    mutation_probability=0.8,
)
ga.create_individual = create_individual
ga.mutate_function = mutate
ga.fitness_function = fitness

ga.run()
print_card_names(ga.best_individual()[1], rows)
