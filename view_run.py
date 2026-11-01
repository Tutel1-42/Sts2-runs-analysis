import json
from pathlib import Path

run_dir = Path(r"C:\Program Files (x86)\Steam\userdata\147271943\2868840\remote\profile1\saves\history")  # change this
runs = []
for f in run_dir.glob("*.run"):
    with open(f, encoding="utf-8") as fp:
        runs.append(json.load(fp))

print(len(runs))          # current 376
print(runs[0].keys())     # top-level fields in one run