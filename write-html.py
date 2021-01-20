import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import pandas as pd


def _get_html_for_contest(contest, template, winners=None):
    summary = pd.read_csv(Path("summaries") / f"{contest}.csv")
    captions = [{"rank": k, **row} for k, row in summary.iterrows()]

    out = template.render(
        captions=captions,
        contest=contest,
        cartoon=f"cartoons/{contest}.jpg",
        winners=winners,
    )
    return out


def _get_winner(contest) -> str:
    f = Path("summaries") / f"{contest}.csv"
    df = pd.read_csv(f)
    idx = df["mean"].idxmax()
    return str(df.loc[idx, "caption"])


if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("contest.html")
    summaries = Path("summaries")
    cartoons = Path("cartoons")
    with open("nyc_winners.json", "r") as f:
        nyc_winners = json.load(f)
    for winner in nyc_winners:
        winner["contest"] = int(winner["title"].split("#")[-1])
    all_winners = {
        w["contest"]: [w["rank1"], w["rank2"], w["rank3"]] for w in nyc_winners
    }

    contests = {int(f.name.replace(".csv", "")) for f in summaries.glob("*.csv")}

    # contest, cartoon, winner
    summary = [
        {"contest": k, "cartoon": f"cartoons/{k}.jpg", "winner": _get_winner(k)}
        for k in contests
    ]
    summary = list(sorted(summary, key=lambda x: -x["contest"]))
    out = env.get_template("index.html").render(summary=summary)
    with open(f"index.html", "w") as fh:
        fh.write(out)

    for contest in contests:
        if contest % 10 == 0:
            print(contest)
        out = _get_html_for_contest(contest, template, all_winners.get(contest, []))
        with open(f"dashboards/{contest}.html", "w") as fh:
            fh.write(out)
