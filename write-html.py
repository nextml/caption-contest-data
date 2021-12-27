import json
import sys
from pathlib import Path
from typing import List

import pandas as pd
from jinja2 import Environment, FileSystemLoader


def _get_html_for_contest(contest: int, template, winners=None):
    summary = pd.read_csv(Path("summaries") / f"{contest}.csv")
    captions = [{"rank": k, **row} for k, row in summary.iterrows()]

    out = template.render(
        captions=captions,
        contest=contest,
        cartoon=f"cartoons/{contest}.jpg",
        winners=winners,
    )
    return out


def _get_winner(contest: int) -> str:
    f = Path("summaries") / f"{contest}.csv"
    df = pd.read_csv(f)
    idx = df["mean"].idxmax()
    return str(df.loc[idx, "caption"])


def _fmt_captions(v: List[dict]) -> List[str]:
    v2 = list(sorted(v, key=lambda x: x["rating"]))
    v3 = [d["text"] for d in v2]
    return v3


if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("contest.html")
    summaries = Path("summaries")
    cartoons = Path("cartoons")
    with open("nyc_winners.json", "r") as f:
        nyc_winners = json.load(f)
    for winner in nyc_winners:
        winner["contest"] = int(winner["title"].split("#")[-1])
    nycc_winners = {
        w["contest"]: [w["rank1"], w["rank2"], w["rank3"]] for w in nyc_winners
    }

    with open("nyccwinners/nyc_winners.json", "r") as f:
        raw = json.load(f)
        rare = [r["data"]["cartoon"] for r in raw]
        mrare = {r["title"]: r["contestFinalists"] for r in rare}
        mwell = {
            int(k.strip("Contest #")): _fmt_captions(v)
            for k, v in mrare.items()
            if "Contest #" in k
        }
    nycc_winners.update(mwell)

    contests = {int(f.name.replace(".csv", "")) for f in summaries.glob("*.csv")}

    # contest, cartoon, winner
    summary = [
        {"contest": k, "cartoon": f"cartoons/{k}.jpg", "winner": _get_winner(k)}
        for k in contests
    ]

    summary = list(sorted(summary, key=lambda x: -x["contest"]))
    out = env.get_template("index.html").render(
        summary=summary, nycc_winners=nycc_winners
    )
    with open(f"index.html", "w") as fh:
        fh.write(out)

    #  nyc_winn
    ## Cartoons are about 672KB each -> 80 of them are 52.5MB.
    ## When I compress with tarfile (below), the smallest I can get is 68MB.
    ## Solution: resize the cartoons.
    #
    #  import tarfile
    #  with tarfile.open("all-data.tar.bz2", mode="w:bz2", compresslevel=9) as tf:
    #  with tarfile.open("all-data.tar.xz", mode="w:xz") as tf:
    #  with tarfile.open("all-data.tar.gz", mode="w:gz", compresslevel=9) as tf:
    #  for f in Path("cartoons").glob("*.jpg"):
    #  tf.add(f"cartoons/{f.name}")
    #  for f in Path("summaries").glob("*.csv"):
    #  tf.add(f"summaries/{f.name}")

    for contest in contests:
        if contest % 10 == 0:
            print(contest)
        out = _get_html_for_contest(contest, template, nycc_winners.get(contest, []))
        with open(f"dashboards/{contest}.html", "w") as fh:
            fh.write(out)
