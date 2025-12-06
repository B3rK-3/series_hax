import os
import json
import requests
import dotenv
from time import time
from src.series_api import send_message_to_chat

dotenv.load_dotenv()

# Gemini API Configuration
gemini_api_key = os.getenv('GEMINI_API_KEY', '')
gemini_model = "gemini-2.5-flash"


def get_ai_response(prompt, chat_history):
    """
    Simple function to get AI response for a given prompt and chat history.

    Args:
        prompt: The prompt to send to the AI
        chat_history: The chat history for context

    Returns:
        The AI response as a string
    """
    if not gemini_api_key:
        print("[AI] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return ""

    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"

    # Construct the full prompt
    full_prompt = f"""{prompt}

Chat History:
{history_text}"""

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        print("[AI] Calling Gemini API...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[AI] HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            try:
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                print(f"[AI] Response: {ai_response}")
                return ai_response.strip()
            except (KeyError, IndexError) as e:
                print(f"[AI] Error parsing Gemini response: {e}")
                return ""
        else:
            print(f"[AI] Error from Gemini API: {r.text}")
            return ""

    except Exception as e:
        print(f"[AI] Failed to call Gemini API: {e}")
        return ""


def chat_analyze(phone_number, chat_history):
    """
    Analyze a user's chat behavior using the reputation prompt and Gemini API.

    Args:
        phone_number: The phone number of the user to analyze
        chat_history: The chat history to analyze

    Returns:
        The analysis result from Gemini (typically a JSON with reputation score)
    """
    if not gemini_api_key:
        print("[ANALYZE] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return ""

    # Load reputation prompt
    try:
        with open('config/reputation_prompt.txt', 'r') as f:
            reputation_prompt = f.read()
    except Exception as e:
        print(f"[ANALYZE] Error loading reputation_prompt.txt: {e}")
        return ""

    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"

    # Construct the full prompt
    full_prompt = f"""{reputation_prompt}

User Phone: {phone_number}

Chat History:
{history_text}"""

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        print(f"[ANALYZE] Calling Gemini API to analyze {phone_number}...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[ANALYZE] HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            print(f"[ANALYZE] Gemini response received")
            try:
                analysis_result = response_data['candidates'][0]['content']['parts'][0]['text']
                print(f"[ANALYZE] Raw analysis result: {analysis_result}")
                analysis_result = analysis_result[7:-3]
                print(f"[ANALYZE] Trimmed analysis result: {analysis_result}")
                analysis_result_json = json.loads(analysis_result)

                reputation_reduction = analysis_result_json.get("score", None)
                reasoning = analysis_result_json.get("reasoning", "")

                print(f"\n{'='*60}")
                print(f"[ANALYZE] User Reputation Analysis")
                print(f"{'='*60}")
                print(f"Phone Number: {phone_number}")
                print(f"Reputation Score: {reputation_reduction}")
                print(f"Reasoning: {reasoning}")
                print(f"{'='*60}\n")

                return analysis_result.strip()
            except (KeyError, IndexError) as e:
                print(f"[ANALYZE] Error parsing Gemini response: {e}")
                return ""
        else:
            print(f"[ANALYZE] Error from Gemini API: {r.text}")
            return ""

    except Exception as e:
        print(f"[ANALYZE] Failed to call Gemini API: {e}")
        return ""


def ai_respond(chat_id, message, from_phone, prompt, chat_history):
    """
    Use Google Gemini 2.5 Flash to respond to a personal message.

    Args:
        chat_id: The ID of the chat
        message: The message content
        from_phone: The phone number of the sender
        prompt: The AI system prompt
        chat_history: The chat history for context
    """
    print(f"[AI RESPOND] Processing message from {from_phone} in personal chat {chat_id}")
    print(f"[AI RESPOND] Message: {message}")

    if not gemini_api_key:
        print("[AI RESPOND] ERROR: GEMINI_API_KEY not set. Please set the environment variable.")
        return

    # Format chat history for the prompt
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"

    # Construct the full prompt with system prompt and chat history
    full_prompt = f"""{prompt}

Chat History:
{history_text}

Latest message from {from_phone}: {message}

Please respond appropriately."""

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        print("[AI RESPOND] Calling Gemini API...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[AI RESPOND] HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            # Extract the generated text
            try:
                ai_response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                print(f"[AI RESPOND] Generated response:\n{ai_response_text}")

                # Try to parse as JSON
                try:
                    ai_json = json.loads(ai_response_text[7:-3])
                    action = ai_json.get('action')
                    message_to_send = ai_json.get('message', '')
                    next_message = ai_json.get('next_message', 0)

                    print(f"[AI RESPOND] Parsed JSON - action: {action}, next_message: {next_message}")

                    # Send only the message text
                    send_message_to_chat(chat_id, message_to_send)

                    # If action is "remind", insert into priority queue
                    if action == "remind" and next_message > 0:
                        # Late import to avoid circular dependency
                        from src.reminder_system import insert_to_priority_queue
                        current_time = time()
                        reminder_timestamp = current_time + next_message
                        insert_to_priority_queue(reminder_timestamp, chat_id, from_phone, next_message)

                except json.JSONDecodeError:
                    # Response is not JSON, send as is
                    print("[AI RESPOND] Response is not JSON, sending as plain text")
                    send_message_to_chat(chat_id, ai_response_text)

            except (KeyError, IndexError) as e:
                print(f"[AI RESPOND] Error parsing Gemini response: {e}")
                print(f"[AI RESPOND] Full response: {response_data}")
        else:
            print(f"[AI RESPOND] Error from Gemini API: {r.text}")

    except Exception as e:
        print(f"[AI RESPOND] Failed to call Gemini API: {e}")


def get_convo_starters(chat_history):
    """
    Generate conversation starters based on chat history using Gemini API.

    Args:
        chat_history: The chat history to analyze

    Returns:
        List of conversation starter strings
    """
    if not gemini_api_key:
        print("[CONVO] ERROR: GEMINI_API_KEY not set.")
        return []

    # Format chat history
    history_text = ""
    if chat_history:
        for msg in chat_history:
            text = msg.get('text', '')
            history_text += f"{text}\n"

    prompt = f"""Based on the following chat history, generate 3 creative and engaging conversation starters to keep the chat going. Make them relevant to the context and short (1-2 sentences each).

Chat History:
{history_text}

Please provide exactly 3 conversation starters, one per line."""

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        print("[CONVO] Calling Gemini API for conversation starters...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"[CONVO] HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            try:
                response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                # Split by newlines and filter out empty lines
                starters = [line.strip() for line in response_text.split('\n') if line.strip()]
                print(f"[CONVO] Generated {len(starters)} conversation starters")
                return starters
            except (KeyError, IndexError) as e:
                print(f"[CONVO] Error parsing Gemini response: {e}")
                return []
        else:
            print(f"[CONVO] Error from Gemini API: {r.text}")
            return []

    except Exception as e:
        print(f"[CONVO] Failed to call Gemini API: {e}")
        return []
