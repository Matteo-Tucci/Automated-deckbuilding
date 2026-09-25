from pyeasyga import pyeasyga
import json
import random
import sqlite3
from pathlib import Path
from constants import TAGS, DB_PATH



def create_individual(data):
    leng = random.randint(60, 65)
    if not data:
        raise ValueError("Cannot create an individual from empty data")

    core_size = min(8, len(data))
    core_cards = random.sample(data, core_size)
    individual = [card for card in core_cards for _ in range(4)]
    individual.extend(data[random.randrange(len(data))] for _ in range(leng - len(individual)))
    return individual

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
        "potato shift": 0
    })
    fit = 0;
    avgcost = 0;
    inkpercentage = 0;
    for card in individual:
        avgcost = avgcost + card[4]
        if card[3] is True:
            inkpercentage += 1

        for tag in json.loads(card[2]):
            if tag in tags:
                tags[tag] += 1
        
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


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
color1 = "Amber"
color2 = "Amethist"

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
    if (color1 in color2): #monocolored deck
        if (item[1] in color1):
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type")))
    else: #double colored deck
        if (color1 in item[1] and color2 in item[1]):
            data.append((item[0], item[1], item[2], card.get("inkwell"), card.get("cost"), card.get("type")))

ga = pyeasyga.GeneticAlgorithm(
    data,
    populatuion_size=50,
    generations=100,
    crossover_probability=0.2,
    mutation_probability=0.8,
)
ga.create_individual = create_individual
