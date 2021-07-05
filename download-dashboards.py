import json
import requests
import csv
import datetime
import pandas as pd
import logging
import os,sys
import shutil
from warnings import warn

CCD_IP = os.environ["CCD_IP"]
CCD_MACHINE = os.environ["CCD_MACHINE"]
today = datetime.datetime.now().isoformat()[:10]

def main(exp_uid, name):
    print('exp_uid',exp_uid, name)
    ranks_url = f'{CCD_IP}/{exp_uid}/ranks.json'
    targets_url = f'{CCD_IP}/{exp_uid}/targets.json'
    votes_url = f'{CCD_IP}/{exp_uid}/votes.json'

    ranks = requests.get(ranks_url).json()
    targets = requests.get(targets_url).json()
    votes = requests.get(votes_url).json()
    csv_dump = [['caption', 'mean', 'precision','votes','not_funny','somewhat_funny','funny']]
    for r in ranks:
        idx = r[0]
        line = [targets[idx]['primary_description']]+r[1:]
        for key in ['not', 'somewhat', 'funny']:
            try:
                line.append(votes[str(idx)][key])
            except:
                print(exp_uid, name, idx, key)
                raise
        csv_dump.append(line)

    df = pd.DataFrame(csv_dump)
    return df

def image_download():
    all_contests = requests.get(f'{CCD_MACHINE}/contest_log.json').json()
    with open(f"all-contests-{today}.json", "w") as f:
        json.dump(all_contests, f)
    for c in all_contests['contests']:
        print("getting image for contest ", c['contest_number'])
        name = c['contest_number']
        exp_uid = c['exp_uid']
        try:
            url = f'{CCD_IP}/{exp_uid}/cartoon.jpg'
            r = requests.get(url, stream=True)
            path = f'cartoons/{name}.jpg'
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print('failed on', exp_uid, name, r.status_code)
            if isinstance(e, KeyboardInterrupt):
                break


def get_and_write(contest):
    name = contest['contest_number']
    exp_uid = contest['exp_uid']
    try:
        print("Getting contest ", contest['contest_number'])
        df = main(exp_uid, str(name))
    except Exception as e:
        warn(f"Failed on {name}")
        logging.exception(e)
        return False
    fname = f"summaries/{name}.csv"
    print("Writing contest ", contest['contest_number'], "to summaries/")
    df.to_csv(fname, index=False, header=False)
    return True


if __name__=='__main__':
    image_download()
    all_contests = requests.get(f'{CCD_MACHINE}/contest_log.json').json()
    try:
        futures = map(get_and_write, all_contests["contests"])
        results = list(futures)
    except KeyboardInterrupt:
        pass
