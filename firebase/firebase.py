from functools import lru_cache
from google.cloud import firestore_v1
from google.oauth2 import service_account
import os

@lru_cache()
def get_firestore_client():
    cred_path = os.path.join(os.path.dirname(__file__), "firebase_creds.json")

    credentials = service_account.Credentials.from_service_account_file(cred_path)
    return firestore_v1.AsyncClient(credentials=credentials)
