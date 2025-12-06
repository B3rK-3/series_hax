import os
import json
import requests
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
import dotenv

dotenv.load_dotenv()


class MemoryCategory(Enum):
    """Categories for memory classification."""
    EXAM_TEST = "exam/test"
    ACHIEVEMENT = "achievement"
    EVENT_ATTENDED = "event_attended"
    EVENT_PLANNED = "event_planned"
    PLAN_WITH_USER = "plan_with_user"
    UNRESOLVED_PLAN = "unresolved_plan"
    CAREER_UPDATE = "career_update"
    PERSONAL_CHALLENGE = "personal_challenge"
    RELATIONSHIP_UPDATE = "relationship_update"
    HEALTH_CONCERN = "health_concern"
    GENERAL_IMPORTANT = "general_important"


@dataclass
class ExtractedMemory:
    """Represents an extracted memory."""
    person: str
    phone: str
    category: str
    summary: str
    importance: int
    event_date: Optional[str] = None
    status: str = "active"
    extracted_at: str = None
    source_chat_id: str = None
    structured_data: dict = None
    original_text: str = None

    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.now().isoformat()
        if self.structured_data is None:
            self.structured_data = {}


class MemoryExtractor:
    """Extracts important memories from chat messages using AI."""

    def __init__(self, gemini_api_key, contact_manager):
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY', '')
        self.contact_manager = contact_manager
        self.gemini_model = "gemini-2.5-flash"

    def analyze_messages(self, chat_id, messages, chat_history):
        """
        Batch analyze recent messages to extract memories.

        Args:
            chat_id: The chat ID
            messages: List of recent message dicts
            chat_history: Full chat history for context

        Returns:
            List of ExtractedMemory objects
        """
        extracted_memories = []

        for msg in messages:
            phone = msg.get('phone')
            message_text = msg.get('message')
            timestamp = msg.get('timestamp')

            if not phone or not message_text:
                continue

            # Get person name
            person_name = self.contact_manager.get_name(phone)

            if not person_name:
                # Track unknown and skip
                self.contact_manager.track_unknown(phone)
                print(f"[MEMORY] Skipping unknown contact: {phone}")
                continue

            # Extract memory from this message
            memory = self.extract_from_text(
                person_name,
                phone,
                message_text,
                chat_history,
                chat_id,
                timestamp
            )

            if memory:
                extracted_memories.append(memory)

        return extracted_memories

    def extract_from_text(self, person, phone, message_text, context, chat_id, timestamp):
        """
        Use Gemini to determine if message contains memory-worthy information.

        Args:
            person: Person's name
            phone: Phone number
            message_text: The message text
            context: Chat history for context
            chat_id: Source chat ID
            timestamp: Message timestamp

        Returns:
            ExtractedMemory object if memorable, None otherwise
        """
        if not self.gemini_api_key:
            print("[MEMORY] ERROR: GEMINI_API_KEY not set")
            return None

        # Build context from chat history
        context_text = ""
        if context:
            recent_context = context[-5:]  # Last 5 messages
            for msg in recent_context:
                text = msg.get('text', '')
                context_text += f"{text}\n"

        # Construct extraction prompt
        prompt = f"""TASK: Determine if this message contains memory-worthy information that would be valuable to remember weeks or months later.

MESSAGE:
From: {person}
Text: "{message_text}"

RECENT CONTEXT:
{context_text}

CRITERIA FOR MEMORABLE:
✓ Specific events with dates (exams, interviews, deadlines)
✓ Important achievements (got a job, passed exam, won award)
✓ Plans made together (coffee, dinner, hangout)
✓ Significant life updates (moving, new job, relationship)
✓ Emotional moments with context (stressed about X, excited for Y)
✓ Unresolved plans (suggested meeting but didn't schedule)
✗ Small talk ("hey", "what's up", "lol", "ok")
✗ Simple reactions without context ("nice", "cool", "thanks")
✗ Everyday chitchat

CATEGORIES:
- exam/test: Exams, tests, academic assessments
- achievement: Accomplishments, awards, successes
- event_attended: Events they went to
- event_planned: Future events they're planning
- plan_with_user: Plans made with you
- unresolved_plan: Suggested plans that weren't scheduled
- career_update: Job, career, professional updates
- personal_challenge: Struggles, difficulties they're facing
- relationship_update: Dating, relationships
- health_concern: Health-related topics
- general_important: Other important information

OUTPUT FORMAT (JSON only, no markdown):
If memorable:
{{
  "is_memorable": true,
  "category": "exam/test",
  "importance": 7,
  "summary": "Brief summary (under 10 words)",
  "event_date": "YYYY-MM-DD or null",
  "status": "upcoming or completed or unresolved",
  "emotional_state": "stressed/excited/worried/happy/null",
  "reasoning": "Why this is memorable"
}}

If NOT memorable:
{{
  "is_memorable": false
}}

Respond with ONLY the JSON, no other text."""

        # Call Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        headers = {"Content-Type": "application/json"}

        try:
            r = requests.post(
                f"{url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if r.ok:
                response_data = r.json()
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text']

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

                if result.get('is_memorable'):
                    memory = ExtractedMemory(
                        person=person,
                        phone=phone,
                        category=result.get('category', 'general_important'),
                        summary=result.get('summary', message_text[:50]),
                        importance=result.get('importance', 5),
                        event_date=result.get('event_date'),
                        status=result.get('status', 'active'),
                        source_chat_id=str(chat_id),
                        structured_data={
                            'emotional_state': result.get('emotional_state'),
                            'reasoning': result.get('reasoning')
                        },
                        original_text=message_text
                    )

                    print(f"[MEMORY] ✓ Extracted: {person} - {memory.summary} ({memory.category})")
                    return memory
                else:
                    print(f"[MEMORY] ✗ Not memorable: {person} - {message_text[:30]}...")
                    return None

            else:
                print(f"[MEMORY] Gemini API error: {r.status_code}")
                return None

        except json.JSONDecodeError as e:
            print(f"[MEMORY] Failed to parse Gemini response: {e}")
            return None
        except Exception as e:
            print(f"[MEMORY] Extraction error: {e}")
            return None
