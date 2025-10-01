"Payment data ingestion"
import csv
import time
import json
# import random
import paho.mqtt.client as paho


def map_type(type_csv):
    """Convert original category name to a more readable one"""
    return {
        "es_transportation": "Transportation",
        "es_health": "Health",
        "es_otherservices": "Other Services",
        "es_food": "Food",
        "es_hotelservices": "Hotel Services",
        "es_barsandrestaurants": "Bars and Restraurants",
        "es_tech": "Technology",
        "es_sportsandtoys": "Sports and Toys",
        "es_wellnessandbeauty": "Wellness",
        "es_hyper": "Hyper",
        "es_fashion": "Fashion",
        "es_home": "Home",
        "es_contents": "Contents",
        "es_travel": "Travel",
        "es_leisure": "Leisure",
    }[type_csv]


# CREATE TABLE payments (ts TIMESTAMP DEFAULT NOW(), customer TEXT, category TEXT, age_category TEXT, amount FLOAT)
def transform(row_raw):
    """Re-map original keys"""
    return {
        "customer": row_raw["customer"],
        "category": map_type(row["category"]),
        "age_category": row_raw["age"],
        "amount": row_raw["amount"],
    }


client = paho.Client(client_id="python", userdata=None, protocol=paho.MQTTv5)
client.connect("localhost", 1883)

while True:
    with open("input.csv", encoding="UTF-8") as csv_file:
        reader = csv.DictReader(csv_file, quotechar="'")

        for row in reader:
            if row["category"] not in (
                "es_transportation",
                "es_health",
                "es_sportsandtoys",
                "es_barsandrestaurants",
                "es_wellnessandbeauty",
            ):
                continue

            # if not random.choice([True, False]):n
            #    continue

            client.publish("payments", json.dumps(transform(row)))

            time.sleep(0.1)
