from pyeasyga import pyeasyga
import json
import random
import sqlite3
from pathlib import Path
from constants import TAGS, DB_PATH
#9-13
#gioca coi parametri, cerca di faRLO CONVERGERE E eventualmente cambia la mutazione
#####COLORS FOR THE DECK########
color1 = "Amber"
color2 = "Ruby"

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
        "location_synergy": "location",
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
    if (30 <= tags["evasive"] + tags["healing"] + tags["challenger"] <= 50):
        if (2.5 <= avgcost <= 3):
            fit +=1
        fit = fit + (tags["evasive"] + tags["healing"] + tags["challenger"])/10 - 2
    ###################
    ##elinor section##
    ###################
    if (30 <= tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"] <= 50): #tap synery non esiste, fallo
        if (2 <= avgcost <= 2.5):
            fit +=1
        fit = fit + (tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"])/10 - 2
    ###################
    ##detectives section##
    ###################
    if (30 <= tags["removal"] + tags["evasive"] + tags["bodyguard"] <= 50):
        if (2.5 <= avgcost <= 2.9):
            fit +=1
        fit = fit + (tags["removal"] + tags["evasive"] + tags["bodyguard"])/10 - 2
    ###################
    ##m&m section##
    ################### commentata perchè generica ed è solo quelle tre carte
    """
    if (30 <= tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"] <= 50):
        if (3.8 <=avgcost <= 4.3):
            fit +=1
        fit = fit + (tags["character"] + tags["lore_gain"] + tags["ramp"] + tags["lore_ramp"] + tags["duo_shift"])/10 - 2
    """
    ###################
    ##midrange section##
    ###################
    if (30 <= tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"] <= 50):
        if (3 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["removal"] + tags["debuff"] + tags["discard"] + tags["draw"])/10 - 2
    ###################
    ##retro section##
    ###################
    if (30 <= tags["ramp"] + tags["character"] <= 50):
        if (4 <= avgcost <= 5):
            fit +=1
        fit = fit + (tags["ramp"] + tags["character"])/10 - 2
    ###################
    ##songs section##
    ###################
    if (30 <= tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["hero_recursion"] + tags["nonhero_recursion"] <= 50):
        if (3.5 <= avgcost <= 4):
            fit +=1
        fit = fit + (tags["action"] + tags["lore_gain"] + tags["singer"] + tags["removal"] + tags["burn"] + tags["hero_recursion"] + tags["nonhero_recursion"])/10 - 2
    ###################
    ##actions section##
    ###################
    if (30 <= tags["action"] + tags["songs"] + tags["draw"] + tags["item"] + tags["lore_gain"] - tags["character"] <= 50):
        if (2.6 <= avgcost <= 3.4):
            fit +=1
        fit = fit + (tags["action"] + tags["songs"] + tags["draw"] + tags["item"] + tags["lore_gain"] - tags["character"])/10 - 2
    ###################
    ##boost section##
    ###################
    if (30 <= tags["boost"] + tags["removal"] + tags["draw"] + tags["lore_gain"] <= 50):
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
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type")))
    else: #double colored deck
        card_colors = set(item[1].split("-"))
        if card_colors <= {color1, color2}:
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type")))

ga = pyeasyga.GeneticAlgorithm(
    data,
    population_size=100,
    generations=900,
    crossover_probability=0.2,
    mutation_probability=0.8,
)
ga.create_individual = create_individual
ga.mutate_function = mutate
ga.fitness_function = fitness

ga.run()
print_card_names(ga.best_individual()[1], rows)
