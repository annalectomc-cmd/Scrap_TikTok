import firebase_admin
from firebase_admin import credentials, firestore

_initialized = False

def init_firebase():

    if not firebase_admin._apps:

        cred = credentials.Certificate(
            "scraping-93adf-firebase-adminsdk-fbsvc-7e36404fe6.json"
        )

        firebase_admin.initialize_app(cred)


def get_firestore():
    if not firebase_admin._apps:
        init_firebase()
    return firestore.client()