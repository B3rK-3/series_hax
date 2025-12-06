import time
import requests
import json
from memory_engine import engine  # Your AI Brain

# config
BASE_URL = "https://series-hackathon-service-202642739529.us-east1.run.app"
API_KEY = "6113d6ed-b505-4b92-ae29-21fbe76eb2fc"
SENDER_NUM = "+16463458837"
MY_TEST_NUMBER = "+14072724176"

# Friends to check (for demo))
FRIENDS_TO_CHECK = ["Eren", "Sarah", "Mike"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ==========================================
# 2. API FUNCTIONS (Written directly here)
# ==========================================

def set_typing(chat_id, is_typing):
    """
    Makes the bot look like it's typing (The 'Human' touch).
    """
    action = "start_typing" if is_typing else "stop_typing"
    url = f"{BASE_URL}/api/chats/{chat_id}/{action}"
    try:
        if is_typing:
            requests.post(url, headers=HEADERS)
        else:
            requests.delete(url, headers=HEADERS)
    except Exception as e:
        print(f"[WARNING] Typing indicator failed: {e}")

def create_chat(recipient_phone):
    """
    Creates a new thread with your phone number.
    """
    url = f"{BASE_URL}/api/chats"
    payload = {
        "chat": {
            "phone_numbers": [recipient_phone]
        },
        "message": {
            "text": "recall AI connected - i'll help you stay in touch with friends"
        },
        "send_from": SENDER_NUM
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status() # Errors if API fails
        data = response.json().get('data')
        return data['id']
    except Exception as e:
        print(f"[ERROR] Create Chat Failed: {e}")
        # Print actual API error response for debugging
        if 'response' in locals():
            print(f"API Response: {response.text}")
        return None

def send_human_message(chat_id, text):
    """
    Sends the message with a fake 'thinking' delay and typing indicator.
    """
    print(f"[BOT] Bot is typing...")
    set_typing(chat_id, True)

    # Fake delay based on message length (0.05s per character)
    time.sleep(min(3, len(text) * 0.05))

    url = f"{BASE_URL}/api/chats/{chat_id}/chat_messages"
    payload = {
        "message": {
            "text": text
        }
    }

    try:
        requests.post(url, headers=HEADERS, json=payload)
        print(f"[SUCCESS] SENT: {text}")
    except Exception as e:
        print(f"[ERROR] Send Failed: {e}")
    finally:
        set_typing(chat_id, False)

# ==========================================
# 3. THE TEST RUNNER
# ==========================================

if __name__ == "__main__":
    from datetime import datetime

    print("="*60)
    print(" RECALL AI - FRIEND NUDGE DEMO")
    print("="*60)
    print(f"[INFO] Today is {datetime.now().strftime('%B %d, %Y')}")
    print(f"[INFO] Checking {len(FRIENDS_TO_CHECK)} friends from chat history")
    print(f"[INFO] Will send nudges to: {MY_TEST_NUMBER}\n")

    # Generate nudges for all friends
    nudges = []
    for friend in FRIENDS_TO_CHECK:
        print(f"\n{'='*60}")
        print(f" Analyzing: {friend}")
        print('='*60)

        try:
            nudge_text = engine.generate_recall_nudge(friend)
            nudges.append({
                "friend": friend,
                "nudge": nudge_text
            })
            print(f"[NUDGE] {nudge_text}")
        except Exception as e:
            print(f"[ERROR] Failed to generate nudge for {friend}: {e}")

    # Display summary
    print(f"\n\n{'='*60}")
    print(" SUMMARY - ALL NUDGES")
    print('='*60)
    for item in nudges:
        print(f"\n[{item['friend']}]")
        print(f"  > {item['nudge']}")

    # Ask if user wants to send
    print(f"\n\n{'='*60}")
    send_choice = input(f"Send the first nudge ({nudges[0]['friend']}) to your phone? (y/n): ")

    if send_choice.lower() == 'y' and nudges:
        print(f"\n[SEND] Creating chat and sending nudge about {nudges[0]['friend']}...")
        chat_id = create_chat(MY_TEST_NUMBER)

        if chat_id:
            print(f"[SUCCESS] Chat created: {chat_id}")
            send_human_message(chat_id, nudges[0]['nudge'])
            print(f"[COMPLETE] Nudge sent! Check your phone at {MY_TEST_NUMBER}")
        else:
            print("[ERROR] Failed to create chat. Check your API credentials.")
    else:
        print("[INFO] Skipped sending. Demo complete!")