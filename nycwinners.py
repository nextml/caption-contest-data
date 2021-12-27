import json
from typing import Dict, List

import pandas as pd


def _get_nyc_winners(fname="io/raw.json"):
    """
    This file obtained by running this query at [1]:

        query {   cartoons(first: 400000) {
        id,
        title,
        announceFinalistsDate
        contestFinalists {
         id,
         text,
         rating
        }
        } }

    [1]:https://graphql.newyorker.com/graphiql
    """
    with open(fname, "r") as f:
        return json.load(f)

def _expand(contest):
    winners = contest.pop("contestFinalists")
    out = {}
    for winner in winners:
        out[f"rank{winner['rating']}"] = winner["text"]
    out.update(contest)
    return out


if __name__ == "__main__":
    raw = _get_nyc_winners()
    mrare = filter(lambda c: "contest" in c["title"].lower(), raw["data"]["cartoons"])
    medium = [_expand(d) for d in mrare]
    cooked = [m for m in medium if any("rank" in k for k in m.keys())]
    keys = [set(d.keys()) for d in cooked]
    assert all(keys[0] == k for k in keys), "All contests should have a top-rated caption"

    with open("nyc_winners.json", "w") as f:
        json.dump(cooked, f, indent=2, sort_keys=True)
