Obstacles
1. There’s no floor number field. You have to derive it by counting across acts. 
2. map_point_type can be misleading. Floor 6 says "unknown", but rooms shows it was actually a slime fight. Use rooms[0].room_type for what really happened.
3. Shop purchases aren’t in card_choices. At the shop on floor 22 you bought Accuracy, but it only appears in cards_gained; the shop’s card_choices list only cards you didn’t buy. If you compute pickrate from card_choices alone, every shop card will look  like it’s never taken.
4. Some reward screens have 6 cards with 2 picks. On floors 19 and 20, you picked two cards from one screen. A “skip” is a screen where everything is was_picked: false, so you need to group offers by screen, not count them one by one.
5. The naming is inconsistent: was_chosen for ancients and was_picked for everything else. That’s minor, but it’s exactly the sort of thing you should normalize and note.
6. damage_taken mixes in max-HP loss. At the Tablet of Truth you lost 69 max HP, and it logged 52 damage taken. (Also, you played 30+ floors on 1–11 max HP and earned a PERFECT badge, which is amazing.)
7. The data has versions. Keep schema_version and build_id on every run row, so if older runs parse differently you can tell why.
8. There’s a multiplayer structure. players is a list and player_stats has player_id. If you play co-op, decide early whether to include those runs or filter to solo.
9. solo only, no abandoned runs.


CHECK: In runs without The Hunt (or Prayer Wheel), there should be zero 6-card combat screens.
In runs with it, double screens should only appear after its floor_added_to_deck.