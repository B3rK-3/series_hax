import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import asdict
import uuid


class EnhancedMemoryEngine:
    """Enhanced memory storage with categorization and smart querying."""

    def __init__(self, memories_file='data/memories.json'):
        self.memories_file = memories_file
        self.memories = []
        self.memory_index = {
            'by_person': {},
            'by_category': {},
            'by_date': {}
        }
        self._load_memories()

    def _load_memories(self):
        """Load memories from JSON file."""
        try:
            if os.path.exists(self.memories_file):
                with open(self.memories_file, 'r') as f:
                    data = json.load(f)
                    self.memories = data.get('memories', [])
                    self.memory_index = data.get('memory_index', {
                        'by_person': {},
                        'by_category': {},
                        'by_date': {}
                    })
                    print(f"[MEMORY ENGINE] Loaded {len(self.memories)} memories")
            else:
                print("[MEMORY ENGINE] No existing memories file, starting fresh")
        except Exception as e:
            print(f"[MEMORY ENGINE] Error loading memories: {e}")

    def _save_memories(self):
        """Save memories to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.memories_file), exist_ok=True)
            with open(self.memories_file, 'w') as f:
                json.dump({
                    'memories': self.memories,
                    'memory_index': self.memory_index,
                    'metadata': {
                        'total_memories': len(self.memories),
                        'last_updated': datetime.now().isoformat()
                    }
                }, f, indent=2)
        except Exception as e:
            print(f"[MEMORY ENGINE] Error saving memories: {e}")

    def _update_indices(self, memory_dict):
        """Update search indices for a memory."""
        memory_id = memory_dict['id']
        person = memory_dict['person']
        category = memory_dict['category']
        event_date = memory_dict.get('event_date')

        # Index by person
        if person not in self.memory_index['by_person']:
            self.memory_index['by_person'][person] = []
        if memory_id not in self.memory_index['by_person'][person]:
            self.memory_index['by_person'][person].append(memory_id)

        # Index by category
        if category not in self.memory_index['by_category']:
            self.memory_index['by_category'][category] = []
        if memory_id not in self.memory_index['by_category'][category]:
            self.memory_index['by_category'][category].append(memory_id)

        # Index by date (YYYY-MM format)
        if event_date:
            try:
                date_key = event_date[:7]  # Get YYYY-MM
                if date_key not in self.memory_index['by_date']:
                    self.memory_index['by_date'][date_key] = []
                if memory_id not in self.memory_index['by_date'][date_key]:
                    self.memory_index['by_date'][date_key].append(memory_id)
            except:
                pass

    def save_memory(self, memory):
        """
        Save an ExtractedMemory to storage.

        Args:
            memory: ExtractedMemory object
        """
        # Convert to dict
        memory_dict = asdict(memory)

        # Generate unique ID
        memory_dict['id'] = f"mem_{uuid.uuid4().hex[:8]}"

        # Add metadata
        memory_dict['metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'mentioned_count': 1,
            'follow_up_sent': False
        }

        # Check for duplicates (similar summary within 7 days)
        is_duplicate = self._check_duplicate(memory_dict)

        if is_duplicate:
            print(f"[MEMORY ENGINE] Duplicate detected, updating existing memory")
            return

        # Add to memories list
        self.memories.append(memory_dict)

        # Update indices
        self._update_indices(memory_dict)

        # Save to disk
        self._save_memories()

        print(f"[MEMORY ENGINE] Saved: {memory_dict['person']} - {memory_dict['summary']}")

    def _check_duplicate(self, new_memory):
        """Check if similar memory already exists."""
        person = new_memory['person']
        category = new_memory['category']
        summary = new_memory['summary'].lower()

        for existing in self.memories:
            if (existing['person'] == person and
                existing['category'] == category and
                existing['summary'].lower() in summary or summary in existing['summary'].lower()):

                # Update existing memory
                existing['metadata']['mentioned_count'] += 1
                existing['metadata']['last_updated'] = datetime.now().isoformat()
                self._save_memories()
                return True

        return False

    def get_memories_for_person(self, person, categories=None, date_range=None):
        """
        Get memories for a specific person.

        Args:
            person: Person's name
            categories: Optional list of categories to filter
            date_range: Optional tuple (start_date, end_date)

        Returns:
            List of memory dicts
        """
        memory_ids = self.memory_index['by_person'].get(person, [])

        memories = [m for m in self.memories if m['id'] in memory_ids]

        # Filter by category
        if categories:
            memories = [m for m in memories if m['category'] in categories]

        # Filter by date range
        if date_range:
            start, end = date_range
            memories = [m for m in memories
                       if m.get('event_date') and start <= m['event_date'] <= end]

        return memories

    def get_upcoming_events(self, person=None, days_ahead=7):
        """
        Get upcoming events.

        Args:
            person: Optional person name filter
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming event memories
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)

        upcoming = []

        for memory in self.memories:
            if memory.get('event_date') and memory.get('status') == 'upcoming':
                try:
                    event_date = datetime.fromisoformat(memory['event_date']).date()
                    if today <= event_date <= future_date:
                        if person is None or memory['person'] == person:
                            upcoming.append(memory)
                except:
                    pass

        # Sort by date
        upcoming.sort(key=lambda m: m.get('event_date', ''))

        return upcoming

    def get_unresolved_plans(self, person):
        """Get unresolved plans for a person."""
        memories = self.get_memories_for_person(person)
        return [m for m in memories if m.get('status') == 'unresolved']

    def update_memory_status(self, memory_id, new_status):
        """Update the status of a memory."""
        for memory in self.memories:
            if memory['id'] == memory_id:
                memory['status'] = new_status
                memory['metadata']['last_updated'] = datetime.now().isoformat()
                self._save_memories()
                print(f"[MEMORY ENGINE] Updated status: {memory_id} -> {new_status}")
                return True
        return False

    def get_all_memories(self):
        """Get all memories."""
        return self.memories.copy()
