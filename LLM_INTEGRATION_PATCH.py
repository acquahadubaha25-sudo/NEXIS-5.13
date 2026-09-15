# ============================================================
# NEXIS 5.13 - LLM INTEGRATION PATCH
# ============================================================
# Add this code to NEXIS_5.13_VOICE_correct_LISTENING.py
# Insert these imports at the top (after existing imports)
# and add the LLM initialization in the NexisApp.build() method

# ============================================================
# ADD THESE IMPORTS (after existing imports section)
# ============================================================

from llm_engine import OllamaEngine
from llm_context import ContextBuilder

# ============================================================
# ADD TO NexisApp.build() METHOD (after self.db initialization)
# ============================================================

# Initialize LLM Engine
print("NEXIS: Initializing Ollama LLM engine...")
self.llm = OllamaEngine(
    host="localhost",
    port=11434,
    model="mistral",
    timeout=30
)

# Initialize Context Builder
self.context_builder = ContextBuilder(db=self.db)

if self.llm.is_ready():
    print("NEXIS: LLM engine online and ready.")
else:
    print(
        "NEXIS: LLM engine unavailable. Ensure Ollama is running:\n"
        "  1. Download from https://ollama.ai\n"
        "  2. Run: ollama serve\n"
        "  3. Pull model: ollama pull mistral\n"
        "Falling back to pattern-based responses."
    )

# ============================================================
# ADD THIS NEW METHOD TO NexisApp CLASS
# ============================================================

def generate_llm_response(
    self,
    command: str
) -> tuple:
    """
    Generate intelligent response using Ollama LLM.
    
    Args:
        command: User command/question
    
    Returns:
        Tuple of (answer, intent) or (None, None) if LLM unavailable
    """
    try:
        if not self.llm.is_ready():
            return None, None
        
        # Get user name from memory
        user_name = self.db.get_fact("my name")
        
        # Build rich system prompt from memory
        system_prompt = self.context_builder.build_system_prompt(
            user_name=user_name,
            include_facts=True,
            include_history=True
        )
        
        # Generate response
        print("NEXIS: Querying LLM...")
        response = self.llm.generate(
            prompt=command,
            system=system_prompt,
            temperature=0.7,
            top_p=0.9,
            max_tokens=512
        )
        
        if response:
            # Add to context for future reference
            self.context_builder.add_turn(command, response)
            
            return response, "LLM_GENERATED"
        
        return None, None
        
    except Exception as error:
        print(f"NEXIS LLM ERROR: {error}")
        return None, None

# ============================================================
# MODIFY run_nexis_engine() METHOD - Add LLM as fallback
# ============================================================
# Replace the "# 15. GENERAL FALLBACK" section with:

# 15. LLM INTELLIGENT FALLBACK
# Try Ollama if pattern matching didn't work
if not handled:
    llm_answer, llm_intent = self.generate_llm_response(command)
    if llm_answer:
        answer = llm_answer
        intent = llm_intent or "LLM_GENERATED"
        handled = True

# 16. PATTERN-BASED FALLBACK (if LLM also unavailable)
if not handled:
    fallback_responses = [
        (
            "I understand your message, but I do not yet have "
            "a specialized response for that request. You can "
            "say help to see my current capabilities."
        ),
        (
            "I processed your command, but that capability is "
            "not currently part of my intelligence engine. "
            "It can be added in a future NEXIS upgrade."
        ),
        (
            "I am still expanding my knowledge and capabilities. "
            "Try asking me in a different way, or say help."
        )
    ]
    answer = random.choice(fallback_responses)
    intent = "GENERAL"

# ============================================================
# INTEGRATION COMPLETE
# ============================================================
# The LLM will now handle:
# - Natural language questions
# - Complex reasoning tasks
# - Personal context-aware responses
# - Fallback when pattern matching fails
#
# While preserving existing features:
# - Voice recognition & TTS
# - Memory & task management
# - Calculator & unit conversion
# - Web search integration
# ============================================================
