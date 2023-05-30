import json
from typing import Dict
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

import yaml
from toolz import groupby
import pandas as pd
from jinja2 import Environment, FileSystemLoader


def _get_html_for_contest(
        summaries,#OrderedDict[str, pd.DataFrame],
        contest: int,
        template,
        winners=None,
        meta=None
):
    # captions = [{"rank": k, **row} for k, row in summary.iterrows()]
    samplers = list(summaries.keys())
    for summary in summaries.values():
        if "score" in summary.columns and "mean" not in summary.columns:
            summary["mean"] = summary["score"]
    captions = {
        sampler: [{"rank": k, **row} for k, row in summary.iterrows()]
        for sampler, summary in summaries.items()
    }

    out = template.render(
        captions=captions,
        contest=contest,
        cartoon=f"cartoons/{contest}.jpg",
        winners=winners,
        meta=meta,
        samplers=samplers,
        summary_fnames=[f.name for f in Path("summaries").glob(f"{contest}*.csv")],
    )
    return out


def _get_winner(contest: int) -> str:
    summaries = Path("summaries")
    _files = list(summaries.glob(f"{contest}*.csv"))
    if len(_files) > 1:
        files = [f for f in _files if "UCB" in f.name]
        f = files[0]
    else:
        f = _files[0]
    df = pd.read_csv(f)
    if "mean" not in df.columns:
        df["mean"] = df["score"]
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

    with open("nyccwinners/nyc_winners2.json", "r") as f:
        mrare = json.load(f)
        chosen = {
            int(k.strip("Contest #")): _fmt_captions(v["cartoon"]["contestFinalists"])
            for k, v in mrare.items()
            if "Contest #" in k
        }

        mwell = {
            title: {
                k: r["cartoon"][k]
                for k in r["cartoon"].keys()
                if "date" in k.lower()
            }
            for title, r in mrare.items()
        }

        meta = {
            int(k.strip("Contest #")): v
            for k, v in mwell.items()
            if "Contest #" in k
        }



    def _get_contest(fname: str) -> int:
        rare = fname.replace(".csv", "")
        mrares = rare.split("_")
        return int(mrares[0])

    summaries_dir = Path("summaries")
    contests = {_get_contest(f.name) for f in summaries_dir.glob("*.csv")}

    for contest in contests:
        if contest < min(meta.keys()):
            continue
        print(contest)
        dfs = [pd.read_csv(f) for f in summaries_dir.glob(f"{contest}*.csv")]
        if contest not in meta:
            print(f"contest={contest} meta doesn't exist, creating blank entry")
            meta[contest] = {}
        try:
            n_captions = [len(df) for df in dfs]
            meta[contest]["n_captions"] = max(n_captions)
        except:
            raise ValueError(f"{contest}, {n_captions}")
        meta[contest]["n_responses"] = int(sum(df["votes"].sum() for df in dfs))

        #  "votingEndDate": "2019-07-21T22:44:00.000Z",
        #  "announceFinalistsDate": "2019-07-15T22:42:00.000Z",
        #  "contestSubmissionEndDate": "2019-06-30T22:42:00.000Z",
        #  "issueDate": "",
        #  "announceFinalistsIssueDate": "July 22, 2019",

    nycc_winners.update(chosen)

    # contest, cartoon, winner
    _summary = [
        {"contest": k, "cartoon": f"cartoons/{k}.jpg", "winner": _get_winner(k)}
        for k in contests
    ]

    summary = list(sorted(_summary, key=lambda x: -x["contest"]))

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
        if (
            (_get_end_date(v) and _get_end_date(v) <= datetime.now())
            or k <= 620 or (831 <= k <= 870)
        )
    }

    # summary = [
    #     v
    #     for v in summary
    #     if v["contest"] < 620 or (
    #         v["contest"] in meta2
    #         and _get_end_date(meta2[v["contest"]])
    #         and _get_end_date(meta2[v["contest"]]) <= datetime.now()
    #     )
    # ]
    summary = [s for s in summary if s["contest"] < max(contests) - 2]

    def _get_sampler(x: str) -> str:
        y = x.replace(".csv", "").replace("summary", "")
        if y[:3].isdigit():
            y = y[3:]
        if y == "":
            return "lil-KLUCB"
        return y.replace("_", "")

    def _get_contest(x: str) -> int:
        assert x[:3].isdigit()
        return int(x[:3])

    summaries_dir = Path("summaries")
    fnames = [f.name for f in summaries_dir.glob(f"*.csv")]
    contest_fnames = groupby(_get_contest, fnames)
    contest_samplers = {
        contest: [_get_sampler(f) for f in fnames]
        for contest, fnames in contest_fnames.items()
    }
    samplers_html = {c: ", ".join(s) for c, s in contest_samplers.items()}

    with open(Path("io") / "info-510-thru-659.yaml", "r") as f:
        old_info = yaml.safe_load(f)
    for v in old_info.values():
        y, m, d = v["votingStartDate"].split("-")
        start = datetime(int(y), int(m), int(d))
        end = start + timedelta(days=13)
        v["announceFinalistsIssueDate"] = end.isoformat()[:10] + " (estimated)"
    assert set(meta.keys()).intersection(set(old_info.keys())) == set()
    meta.update(old_info)
    meta2.update(old_info)

    for i, s in enumerate(summary):
        contest = s["contest"]
        dfs = [pd.read_csv(f) for f in Path("summaries").glob(f"{contest}*.csv")]
        n_votes = sum(df["votes"].sum() for df in dfs)
        s["n_responses"] = int(n_votes)

    out = env.get_template("index.html").render(
        summary=summary, nycc_winners=nycc_winners, dates=meta2, samplers=samplers_html, meta=meta2,
    )
    with open("index.html", "w") as fh:
        fh.write(out)

    for contest in list(contests)[::-1]:
        if contest % 10 == 0:
            print(contest)

        fnames = sorted([f for f in summaries_dir.glob(f"{contest}*.csv")])
        summaries = OrderedDict([(_get_sampler(f.name), pd.read_csv(f)) for f in fnames])
        print(summaries.keys())
        out = _get_html_for_contest(summaries, contest, template, nycc_winners.get(contest, []), meta=meta.get(contest, {}))
        with open(f"dashboards/{contest}.html", "w") as fh:
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
