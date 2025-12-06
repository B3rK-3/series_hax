#!/usr/bin/env python3
"""
send_sms.py

Simple script that sends an outbound message using the Series iMessage Service
Quickstart API. Reads configuration from environment variables so secrets are not
committed in source control.

Environment variables required:
  SERIES_BASE_URL   - e.g. https://api.series.example
  SERIES_API_KEY    - Bearer token to place in Authorization header
  SENDER_NUMBER     - E.164 phone string that your team owns (send_from)
  RECIPIENT_NUMBER  - E.164 recipient phone number
  MESSAGE_TEXT      - The message text to send

Usage (PowerShell):
  $env:SERIES_BASE_URL = 'https://...'
  $env:SERIES_API_KEY = 'sk_...'
  $env:SENDER_NUMBER = '+1317...'
  $env:RECIPIENT_NUMBER = '+1407...'
  $env:MESSAGE_TEXT = 'Hello from the hackathon'
  py ./send_sms.py

Note: This script does not store secrets. Set env vars or use a local .env loader
if you prefer. The script prints HTTP response body for inspection.
"""

import os
import sys
import json
import traceback
from typing import List

try:
    import requests
except Exception:
    print("Missing dependency 'requests'. Install with: pip install -r requirements.txt")
    raise


def required_env_vars() -> List[str]:
    return [
        "SERIES_BASE_URL",
        "SERIES_API_KEY",
        "SENDER_NUMBER",
        "RECIPIENT_NUMBER",
        "MESSAGE_TEXT",
    ]


def main() -> int:

    base_url ="https://series-hackathon-service-202642739529.us-east1.run.app" 
    api_key = '6113d6ed-b505-4b92-ae29-21fbe76eb2fc' 
    sender = "+16463458837"
    recipient = ["+12017244539", "+14075551212"] 
    text = "I WIN"

    url = f"{base_url}/api/chats/{1702219}/chat_messages"
    payload = {
        "message": {"text": "asda"}
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print("POST", url)
    print("Payload:", json.dumps(payload, indent=2))

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print("HTTP", r.status_code)
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)
        return 0 if r.ok else 3
    except Exception:
        print("Request failed:")
        traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())
