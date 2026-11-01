import json
from pathlib import Path
import pandas as pd
import sqlite3

run_dir = Path(r"data\runs")
rows = []
for f in run_dir.glob("*.run"):
    with open(f, encoding="utf-8") as fp:
        r = json.load(fp)
    p = r["players"][0]
    rows.append({
        "run_id": r["start_time"],
        "character": p["character"],
        "ascension": r["ascension"],
        "win": r["win"],
        "abandoned": r["was_abandoned"],
        "killed_by": r["killed_by_encounter"],
        "run_time_min": r["run_time"] / 60,
        "final_floor": sum(len(act) for act in r["map_point_history"]),
        "n_players": len(r["players"]),
        "build_id": r["build_id"],
        "schema_version": r["schema_version"],
    })
rows_rest = []
rows_floor = []
rows_card_offers = []
rows_relic_offers = []
rows_final_deck = []
rows_final_relics = []
rows_shop = []

for f in run_dir.glob("*.run"):
    with open(f, encoding="utf-8") as fp:
        r = json.load(fp)
    if len(r["players"]) > 1 or r["was_abandoned"]:
        continue
    
    p = r["players"][0]
    for card in p["deck"]:
        rows_final_deck.append({
            "run_id": r["start_time"],
            "card_id": card["id"],
            "floor_added": card["floor_added_to_deck"],
            "upgraded": card.get("current_upgrade_level", 0) > 0,
            "enchantment": card.get("enchantment", {}).get("id"),
        })

    for relic in p["relics"]:
        rows_final_relics.append({
            "run_id": r["start_time"],
            "relic_id": relic["id"],
            "floor_added": relic["floor_added_to_deck"],
        })

    floor_num = 0                          # does NOT reset between acts
    for act_idx, act in enumerate(r["map_point_history"], start=1):
        for point in act:
            floor_num += 1
            stats = point["player_stats"][0]   # solo only, so index 0 is safe
            room = point["rooms"][-1]   # what the floor ended as
            first = point["rooms"][0]
            event_id = first.get("model_id") if first["room_type"] == "event" and len(point["rooms"]) > 1 else None
            rows_floor.append({
                "run_id": r["start_time"],
                "act": act_idx,
                "floor": floor_num,
                "map_point_type": point["map_point_type"],
                "room_type": room["room_type"],
                "encounter": room.get("model_id"),
                "turns_taken": sum(rm.get("turns_taken", 0) for rm in point["rooms"]),
                "hp": stats["current_hp"],
                "max_hp": stats["max_hp"],
                "damage_taken": stats["damage_taken"],
                "max_hp_lost": stats["max_hp_lost"],
                "gold": stats["current_gold"],
                "event_id": event_id
            })
            rt = room["room_type"]
            if rt in ("monster", "elite", "boss"):
                source = "combat"
            elif rt == "shop":
                source = "shop"
            else:
                source = "event"

            for i, choice in enumerate(stats.get("card_choices", [])):
                card = choice["card"]
                rows_card_offers.append({
                    "run_id": r["start_time"],
                    "floor": floor_num,
                    "card_id": card["id"],
                    "upgraded": card.get("current_upgrade_level", 0) > 0,
                    "was_picked": choice["was_picked"],
                    "source": source,
                    "screen_id": i // 3,
                })

            if rt == "shop":
                for card in stats.get("cards_gained", []):
                    rows_card_offers.append({
                        "run_id": r["start_time"],
                        "floor": floor_num,
                        "card_id": card["id"],
                        "upgraded": card.get("current_upgrade_level", 0) > 0,
                        "was_picked": True,
                        "source": "shop",
                        "screen_id": None,   # shop isn't a reward screen
                    })
                    
                rows_shop.append({
                "run_id": r["start_time"],
                "floor": floor_num,
                "gold_before": stats["current_gold"] + stats.get("gold_spent", 0) - stats.get("gold_gained", 0),
                "gold_spent": stats.get("gold_spent", 0),
                "cards_bought": len(stats.get("cards_gained", [])),
                "relics_bought": len(stats.get("bought_relics", [])),
                "potions_bought": len(stats.get("bought_potions", [])),
                "cards_removed": len(stats.get("cards_removed", [])),
                })
                

            
            if point["map_point_type"] == "ancient":
                for choice in stats.get("ancient_choice", []):
                    rows_relic_offers.append({
                        "run_id": r["start_time"],
                        "floor": floor_num,
                        "relic_id": "RELIC." + choice["TextKey"],
                        "was_picked": choice["was_chosen"],
                        "source": "ancient",
                    })
            else:
                for choice in stats.get("relic_choices", []):
                    rows_relic_offers.append({
                        "run_id": r["start_time"],
                        "floor": floor_num,
                        "relic_id": choice["choice"],
                        "was_picked": choice["was_picked"],
                        "source": "event" if event_id else rt,
                    })
            for campfire in stats.get("rest_site_choices", []):
                rows_rest.append({
                    "run_id": r["start_time"],
                    "floor": floor_num,
                    "choice":campfire
                })
            
            
            

runs = pd.DataFrame(rows)
print(f"Total runs: {len(runs)}")
coop = runs["n_players"] > 1
print(f"Co-op: {coop.sum()}, solo abandoned: {(~coop & runs['abandoned']).sum()}")
runs = runs[(runs["n_players"] == 1) & (~runs["abandoned"])]
print(f"Kept: {len(runs)}")

floors = pd.DataFrame(rows_floor)
card_offers = pd.DataFrame(rows_card_offers)
relic_offers = pd.DataFrame(rows_relic_offers)
rest_choices = pd.DataFrame(rows_rest)
final_deck = pd.DataFrame(rows_final_deck)
final_relics = pd.DataFrame(rows_final_relics)
shop_visits = pd.DataFrame(rows_shop)

con = sqlite3.connect("sts2.db")
runs.to_sql("runs", con, if_exists="replace", index=False)
floors.to_sql("floors", con, if_exists="replace", index=False)
card_offers.to_sql("card_offers", con, if_exists="replace", index=False)
relic_offers.to_sql("relic_offers", con, if_exists="replace", index=False)
rest_choices.to_sql("rest_choices", con, if_exists="replace", index=False)
final_deck.to_sql("final_deck", con, if_exists="replace", index=False)
final_relics.to_sql("final_relics", con, if_exists="replace", index=False)
shop_visits.to_sql("shop_visits", con, if_exists="replace", index=False)
con.close()
print("Saved sts2.db")


