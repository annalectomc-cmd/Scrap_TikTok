import firebase_admin
from firebase_admin import credentials

_initialized = False

def init_firebase():

    global _initialized

    if not _initialized:

        cred = credentials.Certificate("scraping-93adf-firebase-adminsdk-fbsvc-7e36404fe6.json")

        firebase_admin.initialize_app(cred)

        _initialized = True