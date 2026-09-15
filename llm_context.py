# ============================================================
# NEXIS 5.13 - CONTEXT BUILDER FOR LLM
# ============================================================
# Transforms memory, facts, and history into rich LLM context

from typing import List, Tuple, Optional, Dict
import datetime


class ContextBuilder:
    """
    Builds rich system prompts from NEXIS memory and history.
    Manages context window and token budgets for LLM calls.
    """

    def __init__(self, db=None):
        """
        Initialize context builder.
        
        Args:
            db: NexisDatabase instance for retrieving facts and history
        """
        self.db = db
        self.max_history_turns = 8
        self.max_facts = 15
        self.conversation_turns = []  # Track recent turns for context

    def add_turn(self, user_message: str, assistant_response: str):
        """
        Add a conversation turn to context history.
        
        Args:
            user_message: What the user said
            assistant_response: What NEXIS responded
        """
        self.conversation_turns.append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.datetime.now()
        })
        
        # Keep only recent turns
        if len(self.conversation_turns) > self.max_history_turns:
            self.conversation_turns.pop(0)

    def build_system_prompt(
        self,
        user_name: Optional[str] = None,
        include_facts: bool = True,
        include_history: bool = True
    ) -> str:
        """
        Build a rich system prompt from memory and context.
        
        Args:
            user_name: User's name (if known)
            include_facts: Include personal facts from memory
            include_history: Include recent conversation history
        
        Returns:
            System prompt string for LLM
        """
        lines = [
            "You are NEXIS 5.13, an advanced personal AI assistant.",
            "You are helpful, conversational, friendly, and intelligent.",
            "You provide accurate information and engage in natural dialogue.",
            ""
        ]
        
        # Add user context
        if user_name:
            lines.append(f"The user's name is {user_name}.")
        
        lines.append("")
        
        # Add personal facts from memory
        if include_facts and self.db:
            try:
                facts = self.db.get_all_facts(limit=self.max_facts)
                if facts:
                    lines.append("PERSONAL KNOWLEDGE:")
                    for fact_key, fact_value, _ in facts:
                        # Skip the name (handled above)
                        if fact_key.lower() != "my name":
                            lines.append(f"- {fact_key}: {fact_value}")
                    lines.append("")
            except Exception as error:
                print(f"NEXIS CONTEXT: Error reading facts: {error}")
        
        # Add recent conversation history
        if include_history and self.conversation_turns:
            lines.append("RECENT CONVERSATION CONTEXT:")
            for turn in self.conversation_turns[-3:]:  # Last 3 turns
                lines.append(f"User: {turn['user']}")
                lines.append(f"You: {turn['assistant']}")
            lines.append("")
        
        lines.append("Be concise but helpful. Ask clarifying questions if needed.")
        
        return "\n".join(lines)

    def build_user_message(
        self,
        command: str,
        include_context_hint: bool = True
    ) -> str:
        """
        Build a user message with optional context hints.
        
        Args:
            command: The actual user command/question
            include_context_hint: Add a hint about conversation context
        
        Returns:
            Formatted user message for LLM
        """
        message = command
        
        if include_context_hint and self.conversation_turns:
            # Give LLM a hint about context
            last_topic = self.conversation_turns[-1]["user"] if self.conversation_turns else None
            if last_topic and last_topic != command:
                # Detect if this might be a follow-up
                if any(word in command.lower() for word in ["that", "it", "more", "explain"]):
                    message += f"\n[Context: Previous question was about '{last_topic[:50]}...']"
        
        return message

    def get_conversation_summary(self, max_turns: int = 5) -> str:
        """
        Get a summary of recent conversation.
        
        Args:
            max_turns: Number of recent turns to include
        
        Returns:
            Formatted conversation history
        """
        if not self.conversation_turns:
            return "No conversation history yet."
        
        lines = ["Recent Conversation:"]
        for turn in self.conversation_turns[-max_turns:]:
            timestamp = turn["timestamp"].strftime("%H:%M")
            lines.append(f"[{timestamp}] User: {turn['user']}")
            lines.append(f"[{timestamp}] NEXIS: {turn['assistant'][:100]}...")
        
        return "\n".join(lines)

    def extract_entities(
        self,
        text: str
    ) -> Dict[str, List[str]]:
        """
        Extract potential entities from text (names, places, concepts).
        
        Args:
            text: Text to extract from
        
        Returns:
            Dictionary with entity types and values
        """
        entities = {
            "potential_names": [],
            "potential_topics": [],
            "potential_dates": []
        }
        
        # Simple heuristics (can be enhanced with NLP)
        words = text.split()
        
        # Look for capitalized words (potential names)
        for word in words:
            if word[0].isupper() and len(word) > 2:
                entities["potential_names"].append(word.rstrip(",.!?"))
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities

    def clear_history(self):
        """
        Clear in-memory conversation history.
        (Database history persists separately)
        """
        self.conversation_turns = []

    def get_context_stats(self) -> Dict:
        """
        Get statistics about current context.
        
        Returns:
            Dictionary with context metrics
        """
        stats = {
            "conversation_turns": len(self.conversation_turns),
            "recent_topics": [],
            "context_depth": "shallow" if len(self.conversation_turns) < 3 else "medium" if len(self.conversation_turns) < 6 else "deep"
        }
        
        if self.conversation_turns:
            stats["recent_topics"] = [
                turn["user"][:30] for turn in self.conversation_turns[-3:]
            ]
        
        return stats
