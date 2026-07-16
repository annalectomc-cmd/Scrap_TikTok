command post installation dependencies

scrapling install


command exe generation

pyinstaller --onedir --add-data "fe/build;fe/build" --collect-all scrapling --collect-all browserforge --collect-all patchright --collect-all playwright --collect-data apify_fingerprint_datapoints --collect-data browserforge app.py 
