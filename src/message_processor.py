from time import time
from src.ai_services import chat_analyze, ai_respond, get_convo_starters, extract_memory
from src.reminder_system import insert_to_priority_queue
from src.series_api import get_chat_history, send_message_to_chat
from datetime import datetime


def think_and_act(chat_id, message, from_phone, chat_mapping, priority_queue, reminder_delay, ai_prompt, memory_extractor=None, memory_priority_queue=None, extract_memory=None):
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
        memory_extractor: The memory extractor instance (optional)
        memory_priority_queue: Queue for memory reminders (optional)
        extract_memory: Function to extract memories (optional)
    """
    import heapq
    from time import time
    from datetime import datetime, timezone
    from src.ai_services import chat_analyze, ai_respond, get_convo_starters, extract_memory

    
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

        current_time = datetime.now(timezone.utc)
        reminder_time = current_time.timestamp() + reminder_delay

        other_phone_numbers = [phone for phone in chat_phones if phone != from_phone]
        
        # Extract memory from message (optional)
        if memory_extractor and memory_priority_queue is not None and extract_memory:
            memory_result = extract_memory(chat_id, from_phone, message, current_time.strftime('%Y-%m-%d %H:%M:%S %z'), memory_extractor)
            
            # If memory was extracted and is memorable, add to memory priority queue
            if memory_result and memory_result.get('is_memorable'):
                person_name = memory_extractor.contact_manager.get_name(from_phone) or f"User {from_phone}"
                memory_summary = memory_result.get('summary', message[:50])
                memory_category = memory_result.get('category', 'general_important')
                event_date = memory_result.get('event_date')
                print(f"[MEMORY] Extracted memory for {person_name}: {memory_summary} (Category: {memory_category}, Event Date: {event_date})")
                
                # Calculate reminder timestamp
                if event_date:
                    try:
                        from datetime import datetime
                        # Parse the event date (format: YYYY-MM-DD HH:MM:SS ±ZZZZ)
                        event_time = datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S %z')
                        event_timestamp = event_time.timestamp()
                        
                        # Remind 1 hour before the event
                        BEFORE_SECONDS = 10  # 1 hour
                        reminder_timestamp = event_timestamp - BEFORE_SECONDS
                        print(f"[MEMORY] Event date: {event_date}, Reminder will trigger at: {datetime.fromtimestamp(reminder_timestamp)}")
                    except Exception as e:
                        print(f"[MEMORY] Error parsing event date: {e}, using default 7 days")
                        MEMORY_REMINDER_SECONDS = 7 * 24 * 60 * 60  # 7 days
                        reminder_timestamp = current_time + MEMORY_REMINDER_SECONDS
                else:
                    # No event date, use default 7 days from now
                    MEMORY_REMINDER_SECONDS = 7 * 24 * 60 * 60  # 7 days
                    reminder_timestamp = current_time + MEMORY_REMINDER_SECONDS
                
                # Add to memory priority queue with all phone numbers + original phone number
                heapq.heappush(memory_priority_queue, (reminder_timestamp, other_phone_numbers, from_phone, person_name, memory_summary, memory_category, chat_id))
                print(f"[MEMORY] Added to reminder queue: {person_name} - {memory_summary}")
                print("--------------------------------")

        # For each phone number that isn't the sender
        for phone in other_phone_numbers:
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


def scan_inactive_chats(chat_mapping, last_activity_tracker, last_activity_threshold, phone_to_chat, memory_extractor):
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

                    starter_message = f"You haven't messaged  {', '.join([memory_extractor.contact_manager.get_name(e) for e in phone_numbers if e != phone])} in a while!  How about we continue the conversation? Here are some ideas:\n\n{starters_str}"
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
