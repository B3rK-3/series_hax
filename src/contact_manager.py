import json
import os
from datetime import datetime


class ContactManager:
    """Manages phone-to-name mappings for memory extraction."""

    def __init__(self, contacts_file='config/contacts.json'):
        self.contacts_file = contacts_file
        self.contacts = {}
        self.unknown_contacts = {}
        self._load_contacts()

    def _load_contacts(self):
        """Load contacts from JSON file."""
        try:
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r') as f:
                    data = json.load(f)
                    self.contacts = data.get('contacts', {})
                    self.unknown_contacts = data.get('unknown_contacts', {})
            else:
                print(f"[CONTACT] Contacts file not found: {self.contacts_file}")
        except Exception as e:
            print(f"[CONTACT] Error loading contacts: {e}")

    def _save_contacts(self):
        """Save contacts to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.contacts_file), exist_ok=True)
            with open(self.contacts_file, 'w') as f:
                json.dump({
                    'contacts': self.contacts,
                    'unknown_contacts': self.unknown_contacts
                }, f, indent=2)
        except Exception as e:
            print(f"[CONTACT] Error saving contacts: {e}")

    def get_name(self, phone_number):
        """
        Get the name associated with a phone number.

        Args:
            phone_number: Phone number (e.g., "+14072724176")

        Returns:
            Name string if found, None otherwise
        """
        contact = self.contacts.get(phone_number)
        if contact:
            return contact.get('name')
        return None

    def add_contact(self, phone_number, name, nickname=None, relationship='friend'):
        """
        Add or update a contact.

        Args:
            phone_number: Phone number (e.g., "+14072724176")
            name: Person's name (e.g., "Eren")
            nickname: Optional nickname
            relationship: Type of relationship (default: "friend")
        """
        self.contacts[phone_number] = {
            'name': name,
            'nickname': nickname,
            'relationship': relationship
        }

        # Remove from unknown if it was there
        if phone_number in self.unknown_contacts:
            del self.unknown_contacts[phone_number]

        self._save_contacts()
        print(f"[CONTACT] Added contact: {phone_number} -> {name}")

    def track_unknown(self, phone_number):
        """
        Track an unknown phone number.

        Args:
            phone_number: Phone number to track
        """
        # Don't track if already known
        if phone_number in self.contacts:
            return

        # Update or create unknown entry
        if phone_number in self.unknown_contacts:
            self.unknown_contacts[phone_number]['message_count'] += 1
            self.unknown_contacts[phone_number]['last_seen'] = datetime.now().isoformat()
        else:
            self.unknown_contacts[phone_number] = {
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'message_count': 1,
                'suggested_name': None
            }

        self._save_contacts()

    def get_all_contacts(self):
        """Get all known contacts."""
        return self.contacts.copy()

    def get_unknown_contacts(self):
        """Get all unknown contacts."""
        return self.unknown_contacts.copy()
