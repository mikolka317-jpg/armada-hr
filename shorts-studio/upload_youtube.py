#!/usr/bin/env python3
"""
Завантаження відео на YouTube через офіційний YouTube Data API v3.

Одноразова підготовка (≈10 хвилин):
1. https://console.cloud.google.com → створити проєкт → увімкнути
   "YouTube Data API v3".
2. "Credentials" → "Create credentials" → "OAuth client ID" →
   тип "Desktop app" → завантажити JSON як client_secret.json
   у цю папку.
3. pip install google-api-python-client google-auth-oauthlib

Використання:
    python3 upload_youtube.py video.mp4 "Назва відео" "Опис" "тег1,тег2"

Перший запуск відкриє браузер для входу у ваш Google-акаунт —
токен збережеться у token.json, далі все працює без участі людини.
"""
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = os.path.dirname(os.path.abspath(__file__))


def get_service():
    creds = None
    token_path = os.path.join(HERE, "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(HERE, "client_secret.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(path, title, description, tags):
    yt = get_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        # Shorts визначається автоматично: вертикальне відео ≤ 3 хв
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    request = yt.videos().insert(part="snippet,status", body=body,
                                 media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%")
    print(f"Опубліковано: https://youtube.com/shorts/{response['id']}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    video = sys.argv[1]
    title = sys.argv[2]
    desc = sys.argv[3] if len(sys.argv) > 3 else ""
    tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
    upload(video, title, desc, tags)
