from pathlib import Path
import json

IN = Path("nyc_winners.json")
OUT = Path("nyc_winners2.json")

rare = json.loads(IN.read_text())
for r in rare:
    assert set(r.keys()) == {"data"}
mrare = [r["data"] for r in rare]

well_done = {r["cartoon"]["title"]: r for r in mrare}
with OUT.open("w") as f:
    json.dump(well_done, f)
