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
        # print(f"[ANALYZE] Calling Gemini API to analyze {phone_number}...")
        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        # print(f"[ANALYZE] HTTP {r.status_code}")

        if r.ok:
            response_data = r.json()
            print(f"[ANALYZE] Gemini response received")
            try:
                analysis_result = response_data['candidates'][0]['content']['parts'][0]['text']
                if analysis_result.startswith("```json") and analysis_result.endswith("```"):
                    analysis_result = analysis_result[7:-3]
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

    prompt = f"""Based on the following chat history, generate 3 creative and engaging conversation starters to keep the chat going. Make them relevant to the context and short (1-2 sentences each). Keep it casual and gen-z but dont try too hard.

Chat History:
{history_text}

Please provide exactly 2 conversation starters, one per line.
Tone: Casual, lower case, Gen Z, warm.
NO robotic "I hope you are well".
Reference the specific memory.
Keep it under 15 words.
"""

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


def extract_memory(chat_id, phone_number, message_text, timestamp, memory_extractor=None, get_chat_history=None):
    """
    Extract memory from a single message using Gemini AI.
    
    Args:
        chat_id: The ID of the chat
        phone_number: The phone number of the sender
        message_text: The text of the message
        timestamp: The timestamp of the message
        memory_extractor: The MemoryExtractor instance (used for contact manager)
        get_chat_history: Function to retrieve chat history (not used)
    """
    if not memory_extractor:
        print("[MEMORY] No memory extractor provided")
        return
    
    if not gemini_api_key:
        print("[MEMORY] ERROR: GEMINI_API_KEY not set")
        return

    try:
        # Get person name
        person_name = memory_extractor.contact_manager.get_name(phone_number)
        if not person_name:
            memory_extractor.contact_manager.track_unknown(phone_number)
            print(f"[MEMORY] Skipping unknown contact: {phone_number}")
            return

        print("Timestamp:", timestamp)
        # Construct extraction prompt (same as memory_extractor but without chat context)
        prompt = f"""TASK: Determine whether the given message contains information that would still matter to the user weeks or months from now, meaning it is memorable.

MESSAGE:
From: {person_name}
Text: "{message_text}"
Timestamp: {timestamp}

A MESSAGE IS MEMORABLE IF IT CONTAINS:
- **Specific future events or dates** (exams, interviews, deadlines, trips)
- **Achievements or milestones** (job offer, passed exam, promotion, award)
- **Concrete plans** (especially those involving the user)
- **Life updates** (moving, new job, school changes, relationship changes)
- **Emotional context** tied to meaningful situations (stress, excitement, worry)
- **Unresolved plans** or suggestions that may require follow-up
- **Important personal circumstances** (health issues, major decisions, conflicts)

A MESSAGE IS *NOT* MEMORABLE IF IT IS:
- Routine small talk (hey, lol, ok, thanks, wsp, hi)
- Casual check-ins without meaningful content
- Everyday activities (eating, commuting, chores)
- Generic or low-impact comments without future relevance

CATEGORIES:
exam/test, achievement, event_attended, event_planned,
plan_with_user, unresolved_plan, career_update,
personal_challenge, relationship_update, health_concern,
general_important


OUTPUT (JSON ONLY):

If memorable:{{
  "is_memorable": "true",
  "category": "<one category>",
  "summary": "<under 10 words, include the person's name>",
  "event_date": "<YYYY-MM-DD HH:MM:SS %z, or timestamp+30 seconds if no timeframe is given by user>",
  "status": "upcoming | completed | unresolved",
  "emotional_state": "stressed | excited | worried | happy | null",
  "reasoning": "<why this matters>"
}}

If not memorable:
{{
  "is_memorable": "false"
}}

Return only the JSON.
"""


        # Call Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        headers = {"Content-Type": "application/json"}

        r = requests.post(
            f"{url}?key={gemini_api_key}",
            headers=headers,
            json=payload,
            timeout=30
        )
        # print(f"[MEMORY] HTTP {r.status_code}")

        if r.ok:
            print("--------------------------------")
            response_data = r.json()
            ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
            print(f"[MEMORY] Gemini response: {ai_response}")

            # Clean up response (remove markdown if present)
            ai_response = ai_response.strip()
            if ai_response.startswith('```json'):
                ai_response = ai_response[7:]
            if ai_response.startswith('```'):
                ai_response = ai_response[3:]
            if ai_response.endswith('```'):
                ai_response = ai_response[:-3]
            ai_response = ai_response.strip()

            # Parse JSON
            result = json.loads(ai_response)

            if result.get('is_memorable') == 'true':
                print(f"[MEMORY] ✓ Memorable: {person_name} - {message_text[:30]}... - {result.get('event_date')}")
                print("--------------------------------")
                return result
            else:
                print(f"[MEMORY] ✗ Not memorable: {person_name} - {message_text[:30]}...")
                print("--------------------------------")
                return None

        else:
            print(f"[MEMORY] Gemini API error: {r.status_code}")
            print("--------------------------------")
            return None

    except json.JSONDecodeError as e:
        print(f"[MEMORY] Failed to parse Gemini response: {e}")
        print("--------------------------------")
        return None
    except Exception as e:
        print(f"[MEMORY] Error extracting memory: {e}")
        print("--------------------------------")
        return None