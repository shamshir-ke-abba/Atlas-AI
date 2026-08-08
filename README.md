# 🤖 Atlas AI V3

A sophisticated local conversational AI assistant with dual interfaces (Qt GUI & Web API), built with event-driven architecture, persistent memory, and extensible plugin system.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 🌟 Features

### Core Capabilities
- **Local AI Processing** - Runs completely offline using Ollama + Qwen2.5:1.5b model
- **Dual Interfaces** - Desktop GUI (Qt/PySide6) + Web API (FastAPI)
- **Hinglish Support** - Native support for Hindi + English conversations 🇮🇳
- **Persistent Memory** - Remembers user identity, preferences, and conversation history
- **Smart Intent Detection** - Routes messages to appropriate plugins or LLM
- **Conversation Management** - Auto-titles, history trimming, persistence
- **Streaming Responses** - Real-time response generation with chunk-by-chunk delivery
- **Plugin System** - Extensible architecture for custom tools (Calculator, Time, etc.)

### AI Processing Pipeline
1. **Memory Extraction** - Learns facts from natural language
2. **Intent Detection** - Identifies if message is a query, tool request, or memory recall
3. **Tool Execution** - Runs plugins (calculator, time, etc.) when applicable
4. **Context Building** - Combines user memory + conversation history + current message
5. **LLM Generation** - Streams response from local Ollama model
6. **Persistence** - Saves conversations and memory to disk

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed and running locally (http://localhost:11434)
- [Ollama Download](https://ollama.ai)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd AtlasAI_V3

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download model (if not already done)
ollama pull qwen2.5:1.5b
```

### Running Atlas

#### Desktop GUI
```bash
python3 main.py
```

#### Web Interface
```bash
uvicorn interfaces.web.server:app --host 127.0.0.1 --port 8000
# Access at http://localhost:8000
```

## 📁 Project Structure

```
AtlasAI_V3/
├── ai/                          # AI Processing Pipeline
│   ├── brain.py                # Core orchestrator
│   ├── model.py                # Ollama integration
│   ├── context_builder.py      # Prompt construction
│   ├── planner.py              # Intent detection
│   ├── router.py               # (unused)
│   ├── memory_patterns.py      # Memory extraction patterns
│   ├── translator.py           # Hinglish support
│   └── prompts.py              # System prompts
│
├── core/                        # Runtime & Services
│   ├── runtime.py              # Shared runtime initialization
│   ├── controller.py           # Orchestrator
│   ├── bus.py                  # Event system (Pub/Sub)
│   ├── state.py                # Shared state
│   ├── ai_service.py           # Threading wrapper
│   ├── workers.py              # AI worker thread
│   ├── conversation.py         # Conversation management
│   ├── conversation_store.py   # JSON persistence
│   ├── memory.py               # Memory manager
│   ├── intent.py               # Plugin routing
│   ├── tool_manager.py         # Plugin executor
│   ├── plugin_manager.py       # Plugin loader
│   └── logger.py               # Logging setup
│
├── gui/                         # Desktop Interface (Qt/PySide6)
│   ├── app.py                  # Qt Application
│   ├── window.py               # Main window
│   ├── theme.py                # Styling
│   ├── widgets/
│   │   ├── chat.py            # Chat display
│   │   ├── inputbar.py        # Input field
│   │   ├── message.py         # Message widget
│   │   ├── sidebar.py         # Conversation list
│   │   └── statusbar.py       # Status indicator
│   ├── dialogs/
│   │   └── settings.py        # Settings dialog
│   ├── styles/
│   │   └── atlas.qss          # Qt stylesheet
│   └── resources/             # Assets
│
├── interfaces/                  # API Interfaces
│   └── web/
│       ├── server.py          # FastAPI app
│       ├── runtime.py         # Shared runtime
│       └── static/            # Web UI
│           ├── index.html
│           ├── app.js
│           └── style.css
│
├── plugins/                     # Extensible Plugins
│   ├── base.py                # Plugin base class
│   └── system/
│       ├── calculator.py      # Math operations
│       └── time.py            # Time queries
│
├── memory/                      # Memory Layer
│   ├── manager.py
│   └── history.py
│
├── knowledge/                   # Knowledge Storage
│   └── store.py
│
├── tools/                       # System Tools
│   ├── registry.py
│   ├── filesystem.py
│   ├── linux.py
│   ├── time.py
│   └── clock.py
│
├── data/                        # Runtime Data
│   ├── memory.json            # User memory
│   ├── history.json           # Chat history index
│   ├── knowledge.json         # Knowledge base
│   └── conversations/         # Individual chats
│
├── logs/                        # Log files
│   └── atlas.log
│
├── tests/                       # Test Suite
│   └── test_plugins.py
│
├── config.py                    # Configuration
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## 🎯 Usage Examples

### Chat in English
```
You: "What's the weather like today?"
Atlas: [Responds based on system knowledge]
```

### Chat in Hinglish 🇮🇳
```
You: "Tera naam kya hai?"
Atlas: "I'm Atlas, an AI assistant created by Saad."

You: "Mera naam Saad hai"
Atlas: [Stores your name]

You: "Kya haal hai?"
Atlas: [Responds naturally in Hindi/English mix]
```

### Store Memories
```
You: "My favorite color is blue"
Atlas: [Learns your preference]

You: "I live in Mumbai"
Atlas: [Stores your location]
```

### Use Built-in Tools
```
You: "Calculate 25 * 4"
Atlas: "100" [Uses calculator plugin]

You: "What time is it?"
Atlas: [Shows current time using time plugin]
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# AI Model
MODEL_NAME = "qwen2.5:1.5b"          # Ollama model
OLLAMA_HOST = "http://localhost:11434"
TEMPERATURE = 0.2                    # Response creativity

# GUI Settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Memory
AUTO_SAVE_MEMORY = True
MAX_MEMORY_RESULTS = 10

# Conversation
MAX_HISTORY = 20                      # Messages to keep

# Logging
LOG_LEVEL = "INFO"
```

## 🧠 Architecture Patterns

### Event-Driven (Pub/Sub)
- Components publish events without knowing subscribers
- `EventBus` enables loose coupling
- Example: `ChunkReceived` → `AIService` → GUI

### Plugin/Strategy Pattern
- `AtlasPlugin` base class for extensibility
- Auto-discovery from `plugins/system/` directory
- Easy to add new tools without core changes

### Threading
- `AIWorker` runs on separate `QThread`
- Prevents GUI freezing during LLM inference
- Signal/slot communication (thread-safe)

### Dependency Injection
- Components receive dependencies via constructor
- `Controller` injects into widgets
- `EventBus` injected everywhere

## 🧪 Testing

```bash
# Test Hinglish support
python3 test_hinglish.py

# Test plugin detection
python3 -m pytest tests/test_plugins.py

# Run individual module tests
python3 test_fix.py
```

## 🌐 API Endpoints (Web Interface)

### Chat Endpoint (Sync)
```bash
POST /chat
Content-Type: application/json

{
  "message": "What's your name?"
}

Response: {"response": "I'm Atlas..."}
```

### Stream Endpoint (Async)
```bash
POST /stream
Content-Type: application/json

{
  "message": "Tell me a story"
}

Response: NDJSON stream of chunks
```

### Home
```
GET /
# Serves index.html
```

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Memory Usage | ~150-200 MB | Qt GUI overhead |
| Startup Time | ~3-5 seconds | Loads plugins, connects to Ollama |
| Response Latency | Depends on model | Streaming mitigates perception |
| Context Size | ~2000 tokens | Configurable in context_builder |
| Conversation Storage | ~1KB/chat | JSON-based |

## 🐛 Known Issues & Limitations

### Current Limitations
- **Single-user** - Not designed for multi-user deployment
- **JSON storage** - Doesn't scale beyond 10K conversations (use DB for production)
- **Memory search** - Pattern-based only (no semantic similarity)
- **Model quality** - Depends on Ollama's underlying training
- **Web API** - Lacks authentication and rate limiting

### Workarounds
- Use local network only (no remote access)
- Archive old conversations periodically
- Run multiple instances for different users
- Implement reverse proxy with auth for production

## 📈 Roadmap

- [ ] Database migration (SQLite/PostgreSQL)
- [ ] Semantic memory search (embeddings)
- [ ] Multi-language support beyond Hindi
- [ ] Voice input/output (speech recognition)
- [ ] Authentication & multi-user support
- [ ] Mobile app
- [ ] Docker containerization
- [ ] Cloud deployment options

## 🔐 Privacy & Security

- ✅ **100% Local Processing** - No data sent to servers
- ✅ **Offline Ready** - Works without internet connection
- ✅ **No API Keys** - No external services required
- ✅ **Transparent** - All code is open source

⚠️ For production use:
- Add authentication layer
- Implement HTTPS for web interface
- Encrypt sensitive data at rest
- Run behind reverse proxy

## 🤝 Contributing

Contributions welcome! Areas to help:

1. **New Plugins** - Extend functionality
2. **Hinglish Improvements** - More Hindi patterns
3. **UI/UX** - Better interface design
4. **Performance** - Optimization
5. **Tests** - Better coverage

## 📚 Documentation

- [Hinglish Guide](HINGLISH_GUIDE.md) - Complete language support docs
- [Hinglish Quickstart](HINGLISH_QUICKSTART.md) - Quick examples
- [Bug Fix Log](BUG_FIX_HINGLISH_ECHO.md) - Recent fixes
- [Implementation Details](HINGLISH_IMPLEMENTATION.md) - Technical info

## 🛠️ Troubleshooting

### Ollama Connection Failed
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, test connection
curl http://localhost:11434/api/tags
```

### Model Not Found
```bash
# Download the model
ollama pull qwen2.5:1.5b

# List available models
ollama list
```

### GUI Not Starting
```bash
# Check dependencies
pip install -r requirements.txt

# Verify PySide6 installation
python3 -c "from PySide6.QtWidgets import QApplication; print('OK')"
```

### Memory Not Being Saved
```bash
# Check data directory permissions
chmod -R 755 data/

# Check logs
tail -f logs/atlas.log
```

## 📝 License

This project is open source under the MIT License.

## 👤 Author

Created by **Saad**

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference engine
- **Qwen** - Underlying language model
- **PySide6** - Qt bindings for Python
- **FastAPI** - Modern web framework

---

**Questions?** Check the documentation files or open an issue.

**Ready to chat?** Run `python3 main.py` and start exploring! 🚀
