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

    return [data[random.randrange(len(data))] for _ in range(leng)]

def fitness (individual, data):
    tags = dict.fromkeys(TAGS, 0)
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
    if (50 <= tags["evasive"] + tags["ward"] + tags["healing"] >= 30):
        if (avgcost <= 3):
            fit +=1
        fit = fit + (tags["evasive"] + tags["ward"] + tags["healing"])/10 - 2
    ###################
    ##elinor section##
    ###################
    if (50 <= tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"] >= 30): #tap synery non esiste, fallo
        if (avgcost <= 2.5):
            fit +=1
        fit = fit + (tags["tap_synergy"] + tags["adventure_synergy"] + tags["bodyguard"])/10 - 2

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
