from datetime import datetime, timedelta


class NudgeGenerator:
    """Generates contextual nudges based on categorized memories."""

    @staticmethod
    def generate_contextual_nudge(person_name, enhanced_memory_engine):
        """
        Generate a smart nudge for a person based on their memories.

        Priority:
        1. Recent completed events (follow-up opportunity)
        2. Upcoming events (within 7 days)
        3. Unresolved plans
        4. High-importance memories
        5. Generic nudge

        Args:
            person_name: Name of the person
            enhanced_memory_engine: EnhancedMemoryEngine instance

        Returns:
            Nudge message string
        """
        today = datetime.now().date()

        # Get all memories for this person
        memories = enhanced_memory_engine.get_memories_for_person(person_name)

        if not memories:
            return f"it's been a while since you texted {person_name.lower()}. maybe reach out and see how they're doing?"

        # Priority 1: Recent completed events (past 3 days)
        for memory in memories:
            if memory.get('event_date'):
                try:
                    event_date = datetime.fromisoformat(memory['event_date']).date()
                    days_since = (today - event_date).days

                    if 0 <= days_since <= 3 and memory.get('status') != 'upcoming':
                        # Event happened recently
                        date_str = event_date.strftime("%b %d")
                        return f"{person_name.lower()}'s {memory['summary'].lower()} was on {date_str}. ask how it went!"
                except:
                    pass

        # Priority 2: Upcoming events (within 7 days)
        upcoming = enhanced_memory_engine.get_upcoming_events(person_name, days_ahead=7)
        if upcoming:
            memory = upcoming[0]
            try:
                event_date = datetime.fromisoformat(memory['event_date']).date()
                days_until = (event_date - today).days

                if days_until == 0:
                    return f"reminder: {person_name.lower()}'s {memory['summary'].lower()} is today! send them good vibes!"
                elif days_until == 1:
                    return f"reminder: {person_name.lower()}'s {memory['summary'].lower()} is tomorrow! send them good luck!"
                else:
                    date_str = event_date.strftime("%b %d")
                    return f"reminder: {person_name.lower()} has {memory['summary'].lower()} coming up on {date_str}. maybe send encouragement!"
            except:
                pass

        # Priority 3: Unresolved plans
        unresolved = enhanced_memory_engine.get_unresolved_plans(person_name)
        if unresolved:
            memory = unresolved[0]
            return f"you and {person_name.lower()} talked about {memory['summary'].lower()} but never scheduled it. maybe follow up?"

        # Priority 4: High-importance memories (importance >= 7)
        high_importance = [m for m in memories if m.get('importance', 0) >= 7]
        if high_importance:
            # Sort by most recent
            high_importance.sort(key=lambda m: m.get('extracted_at', ''), reverse=True)
            memory = high_importance[0]
            return f"hey! you haven't checked in on {person_name.lower()} lately. they mentioned {memory['summary'].lower()}. reach out?"

        # Priority 5: Generic nudge
        return f"it's been a while since you texted {person_name.lower()}. maybe reach out and see how they're doing?"
