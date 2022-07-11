from pathlib import Path
import shutil
import yaml
from copy import deepcopy
import sys

import pandas as pd

DIR = Path(".").parent


def _reformat(df: pd.DataFrame) -> pd.DataFrame:
    rare = df.copy()
    rare["votes"] = rare["count"]
    rare["not_funny"] = rare["unfunny"].copy()
    rare["mean"] = rare["score"]

    mrare = rare.drop(
        columns=["target_id", "score", "count", "rank", "contest", "unfunny"],
        errors="ignore"
    )
    # fmt: off
    order = [
        "caption", "mean", "precision", "votes", "not_funny", "somewhat_funny", "funny"
    ]
    # fmt: on
    rare = rare[order]
    return rare


def _move_summaries(summaries, dry_run=True):
    OUT = DIR / "summaries"
    for summary in summaries:
        if any(x in summary.name for x in ["original"]):
            continue

        df = pd.read_csv(summary)
        df = _reformat(df)

        new_summary = OUT / summary.name.replace("summary_", "").replace(
            "RandomSamping", "Random"
        ).replace("_funny", "").replace("KLUCB", "lil-KLUCB")
        assert summary.exists()
        assert OUT.exists()
        assert not new_summary.exists()
        print(f"Old: {summary}\nNew: {new_summary}\n")
        if not dry_run:
            df.index.name = "rank"
            df.to_csv(new_summary)


def _move_cartoon(contest, *, source: Path, target: Path, dry_run=True):
    comic = source / f"{contest}.jpg"
    assert comic.exists()
    new_comic = DIR / "cartoons" / f"{contest}.jpg"
    assert (DIR / "cartoons").exists()
    assert not new_comic.exists()
    print(f"Old: {comic}\nNew: {new_comic}\n")
    if not dry_run:
        shutil.copy(comic, new_comic)


def copy(cartoons=False, summaries=False, meta=False, dry_run=True):
    V1 = Path("_caption-contest-data-api/")
    contests = list(range(510, 660))
    for contest in contests:
        if contest >= 660 or contest in [525]:
            continue
        if summaries:
            summaries = (V1 / "summaries").glob(f"{contest}*.csv")
            _move_summaries(summaries, dry_run=dry_run)

        info = V1 / "info" / f"{contest}"
        if cartoons:
            _move_cartoon(contest, source=info, target=DIR / "cartoons", dry_run=dry_run)
    return True


if __name__ == "__main__":
    # Make sure reformat works correctly
    new = pd.read_csv(f"summaries/660.csv")
    raw = pd.read_csv(f"_caption-contest-data-api/summaries/659_summary_KLUCB.csv")
    cooked = _reformat(raw)
    assert (cooked.columns == new.columns).all()

    # Now, use _reformat
    # copy(summaries=True)#, dry_run=False)

    ## Summaries 510-559 are written to ./summaries/

    # Now, the cartoons:
    # copy(cartoons=True)#, dry_run=False)

    _info = Path("_caption-contest-data-api") / "info.yaml"
    info = yaml.safe_load(_info.read_text())
    for contest, meta in info.items():
        dfs = [pd.read_csv(f) for f in Path("summaries").glob(f"{contest}*.csv")]
        N_captions = {len(df) for df in dfs}
        n_captions = max(N_captions)
        df = pd.concat(dfs)
        n_responses = df["votes"].sum()
        meta["n_captions"] = int(n_captions)
        meta["n_responses"] = int(n_responses)
        meta["n_participants"] = int(deepcopy(meta["np"]))
        meta["votingStartDate"] = meta["start"].isoformat()[:23]
        del meta["np"]

    with open(Path("io") / "info-510-thru-659.yaml", "w") as f:
        yaml.dump(info, f)
