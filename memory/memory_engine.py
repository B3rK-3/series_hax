import json
import os
import google.generativeai as genai
from datetime import datetime

class MemoryEngine:
    def __init__(self):
        # 1. Configure Gemini
        # TODO: Move to environment variables later
        api_key = "AIzaSyB4KJsuAbdjXbp0IRanuN-pi9nBuLRX0_Y"

        try:
            genai.configure(api_key=api_key)  # type: ignore
            self.model = genai.GenerativeModel('gemini-2.5-flash')  # type: ignore
            print("[OK] MemoryEngine initialized successfully")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Gemini: {e}")
            raise
        
        # json storage
        self.file_path = "demo_chat_history.json"
        
        # Load existing history or start fresh
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                try:
                    self.history = json.load(f)
                except json.JSONDecodeError:
                    self.history = []
        else:
            self.history = []

    def save_memory(self, user_name, message_text):
        """
        Saves a message to the local JSON file.
        """
        entry = {
            "author": user_name,
            "text": message_text,
            "timestamp": str(datetime.now())
        }
        self.history.append(entry)
        
        # Save immediately to disk
        with open(self.file_path, 'w') as f:
            json.dump(self.history, f, indent=2)
            
        print(f"[MEMORY] Saved: {user_name} -> '{message_text}'")

    def analyze_user_traits(self, target_person):
        """
        Scans the chat history for a specific person and
        extracts their 'Vibe', 'Hobbies', and 'Current Status'.
        """
        print(f"[BRAIN] Building psychological profile for: {target_person}...")

        # Filter for messages from this person
        related_msgs = [m for m in self.history if m['author'].lower() == target_person.lower()]

        if not related_msgs:
            return "No history found for this user."

        # Format the messages with timestamps for better context
        messages_text = "\n".join([f"[{m['timestamp']}] {m['text']}" for m in related_msgs])

        # Ask Gemini to summarize their situation
        today = datetime.now().strftime("%B %d, %Y")
        prompt = f"""
        Today's date is {today}.

        Here are recent text messages from {target_person}:
        {messages_text}

        TASK:
        Analyze these messages and extract key facts about {target_person}'s recent situation.
        Focus on:
        - Important events they mentioned (exams, deadlines, etc.)
        - What they were stressed or worried about
        - Any time-sensitive events that may have already occurred

        OUTPUT FORMAT:
        List 2-3 specific, actionable facts.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[ERROR] Trait analysis failed: {e}")
            return "Could not analyze traits."

    def generate_recall_nudge(self, target_person):
        """
        Generates a reminder/suggestion message for the user to reach out to someone.
        This is sent TO THE USER, not to the friend.
        """
        # Get the Profile first 
        traits = self.analyze_user_traits(target_person)
        print(f"\n[PROFILE DATA FOUND]:\n{traits}\n")

        # Generate the Reminder Message (for the user)
        today = datetime.now().strftime("%B %d, %Y")
        prompt = f"""
        Today is {today}.

        CONTEXT:
        You are an AI assistant helping someone stay connected with their friends.
        The user hasn't texted their friend {target_person} in a while.

        Here's what you know about {target_person}'s recent situation:
        {traits}

        TASK:
        Write a friendly reminder message TO THE USER suggesting they reach out to {target_person}.
        The message should:
        1. Mention it's been a while since they talked
        2. Suggest what they could ask about (based on the facts above)
        3. Be helpful and encouraging

        EXAMPLES OF GOOD REMINDER MESSAGES:
        - "it's been a while since you texted eren. you should ask him how that calc exam went on dec 4th!"
        - "haven't reached out to sarah lately. maybe check in about her job interview?"
        - "you could text mike and see how his move to the new apartment is going"

        SPECIFIC REQUIREMENTS:
        - If an event ALREADY HAPPENED (exam, interview, deadline), use past tense: "how did X go?"
        - If event is UPCOMING, use future/supportive tone: "good luck with X tomorrow!"
        - Reference specific dates when mentioned (like "dec 4th")
        - Be encouraging and personal, not robotic
        - If they just told you good news recently, suggest congratulating them

        TONE REQUIREMENTS:
        - Casual, friendly, lowercase
        - Direct and actionable
        - Keep it under 25 words
        - Make it feel like a helpful nudge from a friend

        OUTPUT: Only the reminder message text, nothing else.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[ERROR] Nudge generation failed: {e}")
            return f"it's been a while since you texted {target_person}. maybe reach out and see how they're doing?"

# Initialize the engine so it can be imported
engine = MemoryEngine()