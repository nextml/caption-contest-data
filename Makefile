all:
	cd nyccwinners; python get_nycc_winners.py; cd ..
	python download-dashboard.py
	python write-html.py
	git add # [files]
	git push
