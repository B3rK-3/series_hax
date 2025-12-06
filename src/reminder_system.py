import heapq
from time import time
from datetime import datetime
from src.series_api import send_message_to_chat, create_individual_chat, get_chat_history

# Priority queue: (timestamp, chat_id, phone_number, delay_seconds)
priority_queue = []


def insert_to_priority_queue(timestamp, chat_id, phone_number, delay_seconds=0):
    """
    Insert an entry into the priority queue.

    Args:
        timestamp: The time when the reminder should trigger
        chat_id: The ID of the chat
        phone_number: The phone number to remind
        delay_seconds: The delay in seconds before the reminder should trigger
    """
    heapq.heappush(priority_queue, (timestamp, chat_id, phone_number, delay_seconds))
    print(f"Added reminder to queue: chat_id={chat_id}, phone={phone_number}, timestamp={timestamp}, delay={delay_seconds}s")


def send_reminder(chat_id, phone_number, phone_to_chat, numbers_in_chat, delay_seconds):
    """
    Send a reminder message to a phone number.
    Before sending, check if the user responded within the delay window.
    If they did, cancel the reminder.
    If chat with that phone exists, send to existing chat.
    Otherwise, create a new chat and send the reminder.

    Args:
        chat_id: The ID of the original chat
        phone_number: The phone number to send the reminder to
        phone_to_chat: Dictionary mapping phone_number to chat_id
        numbers_in_chat: List of phone numbers in the chat
        delay_seconds: Delay in seconds before reminder should trigger
    """
    print(f"\n[REMINDER] Checking if reminder should be sent to {phone_number} in chat {chat_id}")

    # Get the current time minus (delay_seconds + 1 second)
    current_time = time()
    cutoff_time = current_time - (delay_seconds + 1)

    print(f"[REMINDER] Current time: {current_time}")
    print(f"[REMINDER] Cutoff time: {cutoff_time} (delay_seconds={delay_seconds})")

    # Get chat history
    chat_history = get_chat_history(chat_id)

    # Check if the user (phone_number) responded after the cutoff time
    user_responded_after_cutoff = False
    if chat_history:
        for msg in chat_history:
            msg_from = msg.get('sent_from', '')
            msg_sent_at = msg.get('sent_at', '')

            # Parse the timestamp if it exists
            if msg_sent_at:
                try:
                    # Handle multiple timestamp formats
                    msg_timestamp = 0

                    # Try ISO format with timezone (2025-12-06 06:42:12 -0600)
                    if ' ' in msg_sent_at and '-' in msg_sent_at.split()[-1]:
                        try:
                            msg_time = datetime.strptime(msg_sent_at, '%Y-%m-%d %H:%M:%S %z')
                            msg_timestamp = msg_time.timestamp()
                        except ValueError:
                            pass

                    # Try ISO format with T separator
                    elif 'T' in msg_sent_at:
                        msg_time = datetime.fromisoformat(msg_sent_at.replace('Z', '+00:00'))
                        msg_timestamp = msg_time.timestamp()

                    # Try numeric timestamp
                    else:
                        msg_timestamp = float(msg_sent_at)

                except Exception as e:
                    print(f"[REMINDER] Error parsing timestamp '{msg_sent_at}': {e}")
                    msg_timestamp = 0

                # Check if this message is from the user and after cutoff
                if msg_from == phone_number and msg_timestamp > cutoff_time:
                    print(f"[REMINDER] User {phone_number} responded at {msg_sent_at} (after cutoff)")
                    user_responded_after_cutoff = True
                    break

    # If user responded after cutoff, cancel the reminder
    if user_responded_after_cutoff:
        print(f"[REMINDER] ✓ User {phone_number} already responded! Canceling reminder.")
        return

    print(f"[REMINDER] ✗ No response from {phone_number} after cutoff. Sending reminder...")

    reminder_message = f"You haven't responded to your chat with {', '.join([e for e in numbers_in_chat if e != phone_number])} yet! Do you want to continue the conversation?"
    # Check if we already have a chat with this phone number
    if phone_number in phone_to_chat:
        # Use existing chat
        target_chat_id = phone_to_chat[phone_number]
        print(f"[REMINDER] Using existing chat {target_chat_id} for {phone_number}")
        send_message_to_chat(target_chat_id, reminder_message)
    else:
        # Create new chat with this phone number
        print(f"[REMINDER] Creating new chat for {phone_number}")
        new_chat_id = create_individual_chat(phone_number)
        if new_chat_id:
            phone_to_chat[phone_number] = new_chat_id
            print(f"[REMINDER] Added {phone_number} to phone_to_chat: {new_chat_id}")
            send_message_to_chat(new_chat_id, reminder_message)

    print(f"[REMINDER] Reminder sent to {phone_number}\n")
