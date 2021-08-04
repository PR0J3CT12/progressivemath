# coding: utf-8
import os.path
from googleapiclient.discovery import build
from google.oauth2 import service_account


def service_function():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()
    return service
