This repo contains data from the later runs of The New Yorker's Caption
Contest. For complete details and the original data, see
https://github.com/nextml/caption-contest-data and
https://nextml.github.io/caption-contest-data

## Updating

``` python
$ cd nyccwinners; python get_nycc_winners.py; cd ..
$ python download-dashboard.py
$ python write-html.py
$ git add [files]
$ git push
```
