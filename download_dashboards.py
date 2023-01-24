import csv
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from warnings import warn
from datetime import datetime, timedelta

import pandas as pd
import requests

CCD_IP = os.environ["CCD_IP"]
CCD_MACHINE = os.environ["CCD_MACHINE"]
today = datetime.now().isoformat()[:10]


def main(exp_uid, name):
    print("exp_uid", exp_uid, name)
    ranks_url = f"{CCD_IP}/{exp_uid}/ranks.json"
    targets_url = f"{CCD_IP}/{exp_uid}/targets.json"
    votes_url = f"{CCD_IP}/{exp_uid}/votes.json"

    ranks = requests.get(ranks_url).json()
    targets = requests.get(targets_url).json()
    votes = requests.get(votes_url).json()
    csv_dump = [
        [
            "caption",
            "mean",
            "precision",
            "votes",
            "not_funny",
            "somewhat_funny",
            "funny",
        ]
    ]
    for r in ranks:
        idx = r[0]
        line = [targets[idx]["primary_description"]] + r[1:]
        for key in ["not", "somewhat", "funny"]:
            try:
                line.append(votes[str(idx)][key])
            except:
                print(exp_uid, name, idx, key)
                raise
        csv_dump.append(line)

    df = pd.DataFrame(csv_dump)
    return df


def image_download():
    all_contests = requests.get(f"{CCD_MACHINE}/contest_log.json").json()
    with open(f"all-contests-{today}.json", "w") as f:
        json.dump(all_contests, f)
    for c in all_contests["contests"]:
        name = c["contest_number"]
        exp_uid = c["exp_uid"]
        path = f"cartoons/{name}.jpg"
        if Path(path).exists():
            continue
        print("getting image for contest ", c["contest_number"])
        try:
            url = f"{CCD_IP}/{exp_uid}/cartoon.jpg"
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print("failed on", exp_uid, name, r.status_code)
            if isinstance(e, KeyboardInterrupt):
                break


def get_and_write(contest):
    """
    Parameters
    ----------
    contest : Dict[str, Union[str, int]]
        Example dict:

            {'contest_number': 784,
            'exp_uid': 'nyi71f8b14a553152ec4da8251f57d5c494b',  # fake
            'launched': '2021-12-13 16:44:35.999066'}

    Returns
    -------
    written : bool
        If files written to disk.

    Notes
    -----
    This function writes a file to disk.

    """
    name = contest["contest_number"]
    exp_uid = contest["exp_uid"]
    fname = f"summaries/{name}.csv"

    #  if Path(fname).exists():
        #  return False

    try:
        print("Getting contest ", contest["contest_number"])
        df = main(exp_uid, str(name))
    except Exception as e:
        warn(f"Failed on {name}")
        logging.exception(e)
        return False
    print("Writing contest ", contest["contest_number"], "to summaries/")
    df.to_csv(fname, index=False, header=False)
    return True


def get_latest_contest():
    contests = [
        int(c.name.replace(".csv", "")) for c in Path("summaries").glob("*.csv")
    ]
    most_recent = max(contests)
    return most_recent

if __name__ == "__main__":
    image_download()
    all_c = requests.get(f"{CCD_MACHINE}/contest_log.json").json()

    finished = [
        c for c in all_c["contests"]
        if datetime.now() >= timedelta(days=1 * 7) + datetime.fromisoformat(c["launched"])
    ]
    breakpoint()
    try:
        futures = map(get_and_write, finished[::-1])
        results = list(futures)
        #  assert sum(results) in {0, 1}, "Only download 0 or 1 dashboards"
    except KeyboardInterrupt:
        pass
