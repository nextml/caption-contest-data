import json
from typing import Dict
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

import pandas as pd
from jinja2 import Environment, FileSystemLoader


def _get_html_for_contest(contest: int, template, winners=None, dates=None):
    summary = pd.read_csv(Path("summaries") / f"{contest}.csv")
    captions = [{"rank": k, **row} for k, row in summary.iterrows()]

    out = template.render(
        captions=captions,
        contest=contest,
        cartoon=f"cartoons/{contest}.jpg",
        winners=winners,
        dates=dates,
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
        # fmt: on


    with open("nyccwinners/nyc_winners.json", "r") as f:
        raw = json.load(f)
        rare = [r["data"]["cartoon"] for r in raw]
        mrare = {r["title"]: r["contestFinalists"] for r in rare}
        chosen = {
            int(k.strip("Contest #")): _fmt_captions(v)
            for k, v in mrare.items()
            if "Contest #" in k
        }

        mwell = {
            r["title"]: {k: r[k] for k in r.keys() if "date" in k.lower()} for r in rare
        }

        meta = {
            int(k.strip("Contest #")): v
            for k, v in mwell.items()
            if "Contest #" in k
        }
        #  "votingEndDate": "2019-07-21T22:44:00.000Z",
        #  "announceFinalistsDate": "2019-07-15T22:42:00.000Z",
        #  "contestSubmissionEndDate": "2019-06-30T22:42:00.000Z",
        #  "issueDate": "",
        #  "announceFinalistsIssueDate": "July 22, 2019",

    nycc_winners.update(chosen)

    contests = {int(f.name.replace(".csv", "")) for f in summaries.glob("*.csv")}

    # contest, cartoon, winner
    summary = [
        {"contest": k, "cartoon": f"cartoons/{k}.jpg", "winner": _get_winner(k)}
        for k in contests
    ]

    summary = list(sorted(summary, key=lambda x: -x["contest"]))

    def _get_end_date(v: Dict[str, str]) -> Optional[datetime]:
        if "votingEndDate" not in v or v["votingEndDate"] is None:
            return None
        d_str = v["votingEndDate"]
        if len(d_str) and d_str[-1] == "Z":
            d_str = d_str[:-1]  # Zulu time zone
        eps = timedelta(hours=6)
        return datetime.fromisoformat(d_str) + eps

    meta2 = {
        k: v
        for k, v in meta.items()
        if _get_end_date(v) and _get_end_date(v) <= datetime.now()
    }
    summary = [
            v 
            for v in summary 

            if v["contest"] in meta2 and _get_end_date(meta2[v["contest"]])
                and _get_end_date(meta2[v["contest"]]) <= datetime.now()]

    out = env.get_template("index.html").render(
        summary=summary, nycc_winners=nycc_winners, dates=meta2
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

    for contest in list(contests)[::-1]:
        if contest % 10 == 0:
            print(contest)
        out = _get_html_for_contest(contest, template, nycc_winners.get(contest, []), dates=meta.get(contest, {}))
        with open(f"dashboards/{contest}.html", "w") as fh:
            fh.write(out)
