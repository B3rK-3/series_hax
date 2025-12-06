from time import time
from src.ai_services import chat_analyze, ai_respond, get_convo_starters
from src.reminder_system import insert_to_priority_queue
from src.series_api import get_chat_history, send_message_to_chat


def think_and_act(chat_id, message, from_phone, chat_mapping, priority_queue, reminder_delay, ai_prompt):
    """
    Process a message received from Kafka and manage priority queue for reminders.

    Args:
        chat_id: The ID of the chat/conversation
        message: The message content to process
        from_phone: The phone number of the sender
        chat_mapping: Dictionary mapping chat_id to list of phone_numbers in that chat
        priority_queue: Priority queue for tracking reminders (heap)
        reminder_delay: Delay in seconds before sending reminders
        ai_prompt: The AI system prompt
    """
    print(f"Processing message for chat_id: {chat_id}")
    print(f"From phone: {from_phone}")
    print(f"Message: {message}")

    # Check if this is a group chat or personal message
    if chat_id in chat_mapping:
        # This is a group chat
        chat_phones = chat_mapping[chat_id]
        print(f"Chat phones: {chat_phones}")

        # Get chat history and analyze the sender
        chat_history = get_chat_history(chat_id)
        print(f"Analyzing chat behavior for {from_phone}")
        chat_analyze(from_phone, chat_history)

        current_time = time()
        reminder_time = current_time + reminder_delay

        # For each phone number that isn't the sender
        for phone in chat_phones:
            if phone != from_phone:
                # Check if this (chat_id, phone) pair already exists in priority queue
                exists = False
                for timestamp, qid, qphone, delay_seconds in priority_queue:
                    if qid == chat_id and qphone == phone:
                        exists = True
                        print(f"Entry for {phone} in chat {chat_id} already exists, skipping")
                        break

                # Only add if it doesn't exist
                if not exists:
                    insert_to_priority_queue(reminder_time, chat_id, phone, reminder_delay)
    else:
        # This is a personal message
        print(f"Chat ID {chat_id} not found in chat_mapping - treating as personal message")

        # Get chat history
        chat_history = get_chat_history(chat_id)

        # Call AI respond
        ai_respond(chat_id, message, from_phone, ai_prompt, chat_history)

    print(f"Current priority queue size: {len(priority_queue)}")


def scan_inactive_chats(chat_mapping, last_activity_tracker, last_activity_threshold, phone_to_chat):
    """
    Scan all chats in chat_mapping and check for inactive conversations.
    If a chat hasn't had activity in more than last_activity_threshold seconds,
    generate conversation starters and send them to the participants.

    Args:
        chat_mapping: Dictionary mapping chat_id to phone_numbers
        last_activity_tracker: Dictionary tracking last activity time for each chat_id
        last_activity_threshold: Seconds of inactivity before sending starters
        phone_to_chat: Dictionary mapping phone_number to individual chat_id
    """
    current_time = time()

    for chat_id, phone_numbers in chat_mapping.items():
        # Get last activity time for this chat (default to current time if not tracked)
        last_activity = last_activity_tracker.get(chat_id, current_time)
        time_since_activity = current_time - last_activity

        print(f"[SCAN] Chat {chat_id}: {time_since_activity:.1f}s since last activity (threshold: {last_activity_threshold}s)")

        if time_since_activity > last_activity_threshold:
            print(f"[SCAN] Chat {chat_id} is inactive! Getting conversation starters...")

            # Get chat history
            chat_history = get_chat_history(chat_id)

            # Generate conversation starters
            starters = get_convo_starters(chat_history)

            if starters:
                # Format starters into a message
                starters_str = ""
                for i, starter in enumerate(starters, 1):
                    starters_str += f"{i}. {starter}\n"

                # Send to all phone numbers in the chat
                for phone in phone_numbers:
                    print(f"[SCAN] Sending conversation starters to {phone}")

                    starter_message = f"You haven't messaged  {', '.join([e for e in phone_numbers if e != phone])} in a while!  How about we continue the conversation? Here are some ideas:\n\n{starters_str}"
                    individual_chat_id = phone_to_chat.get(phone)
                    if individual_chat_id:
                        send_message_to_chat(individual_chat_id, starter_message)
                    else:
                        print(f"[SCAN] No individual chat found for phone {phone}")

                # Update last activity time for this chat
                last_activity_tracker[chat_id] = current_time
            else:
                print(f"[SCAN] Failed to generate conversation starters for chat {chat_id}")
        else:
            # Update last activity time if this is a new chat
            if chat_id not in last_activity_tracker:
                last_activity_tracker[chat_id] = current_time
