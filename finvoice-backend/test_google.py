import os
from google.cloud import speech_v1
from google.oauth2 import service_account

# Load credentials
credentials_path = "google-credentials.json"
credentials = service_account.Credentials.from_service_account_file(
    credentials_path
)

# Test Speech-to-Text
client = speech_v1.SpeechClient(credentials=credentials)
print("✅ Successfully connected to Google Cloud!")
print(f"✅ Project: {credentials.project_id}")