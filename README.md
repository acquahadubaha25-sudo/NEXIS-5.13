# NEXIS 5.13 - Personal AI Assistant with LLM Integration

A powerful, voice-enabled personal AI assistant built with Python, featuring local Ollama LLM integration, persistent memory, task management, and real-time text-to-speech.

## Features

### 🧠 Intelligence
- **Ollama LLM Integration**: Uses local Mistral model for intelligent reasoning (free, runs offline)
- **Persistent Memory**: SQLite-based fact storage, conversation history, task management
- **Context Awareness**: Remembers personal facts, previous conversations, and topics
- **Advanced Calculator**: Safe AST-based math with functions (sqrt, sin, cos, log, etc.)

### 🎤 Voice Capabilities
- **Speech Recognition**: Google Speech-to-Text with dual microphone backends (sounddevice + PyAudio)
- **Text-to-Speech**: Windows native SAPI + pyttsx3 fallback with streaming support
- **Continuous Conversation Mode**: Hands-free Listen → Process → Speak → Listen loop
- **Advanced Audio Processing**: Energy thresholding, silence detection, adaptive sensitivity

### 📱 UI & Interaction
- **Kivy GUI**: Beautiful, responsive interface with Kv framework
- **Animated Sphere**: Real-time particle effects, rotating rings, pulsing core
- **State-Based Colors**: Idle (orange) → Listening (blue) → Thinking (yellow) → Speaking (purple)
- **Touch Interaction**: Drag-to-move, pinch-to-scale animated core

### 📋 Productivity
- **Task Manager**: Create, list, delete, and clear tasks
- **Reminder System**: Time-based reminders with notifications
- **Daily Briefing**: Automated morning summary with tasks and reminders
- **Conversation History**: Searchable logs with timestamps

### 🛠️ System
- **Cross-Platform**: Windows, Linux, and Android (via Kivy + PyJNIus)
- **Hardware Integration**: Battery status, device info, system diagnostics
- **Web Search**: Google Search and YouTube integration
- **Unit Conversion**: Temperature, distance, weight conversions

## Quick Start

### Prerequisites

1. **Install Ollama** (Free, ~2GB download)
   - Download: https://ollama.ai
   - Run: `ollama serve` (starts server on localhost:11434)

2. **Pull Mistral Model**
   ```bash
   ollama pull mistral
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Run NEXIS

```bash
python NEXIS_5.13_VOICE_correct_LISTENING.py
```

## Architecture

```
┌─────────────────────────────────────────┐
│         NEXIS 5.13 + Ollama LLM         │
├─────────────────────────────────────────┤
│  Voice Input (Speech-to-Text)           │
│       ↓                                  │
│  [Retrieve Facts from Memory]           │
│       ↓                                  │
│  [Build Rich Context Prompt]            │
│       ↓                                  │
│  [Send to Ollama (localhost:11434)]     │
│       ↓                                  │
│  [Intelligent Response Generation]      │
│       ↓                                  │
│  [Save to Memory + History]             │
│       ↓                                  │
│  Voice Output (Text-to-Speech)          │
└─────────────────────────────────────────┘
```

## File Structure

```
NEXIS-5.13/
├── NEXIS_5.13_VOICE_correct_LISTENING.py  # Main application
├── llm_engine.py                          # Ollama integration
├── llm_context.py                         # Context builder for LLM
├── requirements.txt                       # Python dependencies
└── README.md                              # This file
```

## Usage Examples

### Basic Commands
```
"Hello NEXIS"                           → Greeting
"What can you do?"                      → Capabilities
"My name is John"                       → Remember name
"What is my name?"                      → Retrieve fact
"Calculate 25 * 8"                      → Math
"Convert 10 km to miles"                → Unit conversion
"Remind me to study in 30 minutes"      → Set reminder
"Show my tasks"                         → Task list
"Give me my daily briefing"             → Summary
"Search for Python tutorials"           → Web search
```

### Voice Mode
- Click **LISTEN** button to capture voice command once
- Click **CONTINUOUS VOICE** to enable hands-free mode
- Click **STOP VOICE MODE** to exit voice mode

## Configuration

### Customize Ollama Settings
Edit the LLM initialization in `NEXIS_5.13_VOICE_correct_LISTENING.py`:

```python
self.llm = OllamaEngine(
    host="localhost",      # Ollama server host
    port=11434,            # Ollama server port
    model="mistral",       # Model name (mistral, neural-chat, llama2, etc.)
    timeout=30             # Request timeout in seconds
)
```

### Adjust Voice Settings
```python
set_tts_rate(165)      # Speech rate (80-260)
set_tts_volume(1.0)    # Volume (0.0-1.0)
```

### Alternative Models
```bash
ollama pull neural-chat    # Optimized for conversation (7B)
ollama pull llama2         # Most capable (7B/13B, slower)
ollama pull orca-mini      # Smallest, fastest (3B)
```

## Troubleshooting

### Ollama Not Connecting
- Ensure Ollama is running: `ollama serve`
- Check that server is accessible: `curl http://localhost:11434/api/tags`
- NEXIS will fall back to pattern matching if LLM unavailable

### Model Not Found
```bash
ollama list              # See downloaded models
ollama pull mistral      # Download Mistral
```

### Voice Recognition Not Working
- Install all audio dependencies: `pip install SpeechRecognition sounddevice numpy`
- Check microphone: `python -m speech_recognition`
- Windows: Ensure no other apps are using microphone

### TTS Issues
- Windows: TTS uses System.Speech (built-in)
- Linux: Install espeak: `sudo apt-get install espeak`
- macOS: Uses built-in speech synthesis

## Performance

- **Response Time**: 2-5 seconds with Mistral (CPU) / <1 second (GPU)
- **Memory Usage**: ~500MB base + ~4GB Mistral model
- **Conversations**: Stored indefinitely in SQLite
- **Context Window**: Recent 8 turns for LLM awareness

## Advanced Features

### Context Awareness
NEXIS tracks:
- Personal facts and preferences
- Conversation history
- Previous topics and calculations
- Current discussion context

### Memory Persistence
- **Facts**: Long-term storage of personal information
- **History**: Searchable conversation logs
- **Tasks**: Persistent to-do list
- **Reminders**: Time-based notifications

### LLM Integration
- Rich system prompts with personal context
- Streaming responses for real-time TTS
- Graceful fallback to pattern matching
- Token-aware context management

## Limitations & Known Issues

- Mistral is 7B model (slower on CPU, ~2-5s per response)
- Voice recognition requires internet for Google Speech-to-Text
- Android support requires additional Kivy/Buildozer setup
- LLM context limited to recent ~8 turns to manage token usage

## Future Enhancements

- [ ] Local speech recognition (Whisper)
- [ ] Vector embeddings for semantic search
- [ ] Plugin system for custom skills
- [ ] Cloud sync for cross-device memories
- [ ] Sentiment analysis and mood detection
- [ ] Fine-tuned models for better personalization
- [ ] Multi-user support
- [ ] GPU acceleration detection

## Performance Tips

1. **Use GPU if available**: Ollama auto-detects CUDA/Metal
2. **Use smaller models**: Orca-mini (3B) for faster responses
3. **Run on dedicated machine**: NEXIS uses all cores during inference
4. **Monitor memory**: Keep ~6GB free for model + OS

## License

MIT License - See LICENSE file

## Credits

- **Ollama**: https://ollama.ai (local LLM inference)
- **Kivy**: https://kivy.org (UI framework)
- **Mistral**: https://mistral.ai (base model)
- **SpeechRecognition**: https://github.com/Uberi/speech_recognition
- **pyttsx3**: https://github.com/nateshmbhat/pyttsx3

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section
2. Review the code comments
3. Test Ollama separately: `curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"hello"}'`

---

**NEXIS 5.13** - Your Personal AI Assistant

Built with ❤️ for intelligent, offline-first conversational AI
