# 🤖 Atlas AI V3

A sophisticated local conversational AI assistant with dual interfaces (Qt GUI & Web API), built with event-driven architecture, persistent memory, and extensible plugin system.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 🌟 Features

### Core Capabilities
- **Local AI Processing** - Runs completely offline using Ollama + Qwen2.5:1.5b model
- **Dual Interfaces** - Desktop GUI (Qt/PySide6) + Web API (FastAPI)
- **Context-Aware Web Research** - Deep web retrieval, HTML extraction, table parsing, passage ranking, and grounded synthesis with citation traceability
- **Hinglish Support** - Native support for Hindi + English conversations 🇮🇳
- **Persistent Memory** - Remembers user identity, preferences, and conversation history
- **Smart Intent Detection** - Routes messages to appropriate plugins or LLM
- **Conversation Management** - Auto-titles, history trimming, persistence
- **Streaming Responses** - Real-time response generation with chunk-by-chunk delivery
- **Plugin System** - Extensible architecture for custom tools (Web Search, Calculator, Time, etc.)

### AI Processing Pipeline
1. **Memory Extraction** - Learns facts from natural language
2. **Intent Detection** - Identifies if message is a query, tool request, or memory recall
3. **Tool Execution** - Runs plugins (web research, calculator, time, etc.) when applicable
4. **Context Building** - Combines user memory + conversation history + current message + retrieved evidence
5. **LLM Generation** - Streams response from local Ollama model with strict untrusted data isolation
6. **Persistence** - Saves conversations and memory to disk

### Web Research Pipeline
Atlas AI V3 implements a multi-stage web research architecture:

```
User Query
    │
    ▼
[Search & Query Analysis] ──► Decomposes multi-intent queries, strips conversational tails, expands synonyms
    │
    ▼
[Candidate Filtering]     ──► Filters ads/sponsored links, detects DDG 202/rate-limits, ensures domain diversity
    │
    ▼
[Page Fetching]           ──► Concurrently retrieves live web pages with per-host timeouts and fail-soft handling
    │
    ▼
[Content Extraction]      ──► Strips navigation, scripts, and boilerplate; preserves structured tables as Markdown
    │
    ▼
[Passage Ranking]         ──► Segments content into structured chunks; ranks by heading weight & lexical relevance
    │
    ▼
[Evidence Selection]      ──► Selects top passages within adaptive context budgets (e.g. 4000 characters)
    │
    ▼
[Grounded Synthesis]      ──► Sandboxes untrusted web data with boundary markers; guides model to cite and synthesize
    │
    ▼
Answer with Citations     ──► Direct factual answer with inline [Source X] references and verifiable URLs
```

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
│       ├── time.py            # Time queries
│       └── web_search.py      # Context-aware web research & retrieval
│
├── benchmarks/                  # Benchmark Suites
│   └── local_models/
│       └── benchmark.py       # Isolated local model benchmark runner
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
├── tests/                       # Test Suites
│   ├── test_web_research.py   # Web retrieval, extraction, ranking tests
│   ├── test_web_research_fixes.py # DDG resilience & injection defense tests
│   ├── test_plugins.py        # Plugin detection & routing tests
│   └── test_brain_memory.py   # Memory persistence tests
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

### Research the Web
```
You: "What is the release status of Python 3.13?"
Atlas: "Python 3.13 is the latest stable release of Python [Source 1], featuring improvements such as an experimental free-threaded build and an improved interactive interpreter [Source 2]."

• [Source 1] Status of Python Branches (python.org) — https://devguide.python.org/versions/
• [Source 2] Python 3.13 Release Notes (docs.python.org) — https://docs.python.org/3/whatsnew/3.13.html
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

# Web Research Pipeline
ENABLE_WEB_RESEARCH = True            # Enable deep web retrieval
WEB_RESEARCH_MAX_PAGES = 5           # Max candidate pages to fetch
WEB_RESEARCH_PAGE_TIMEOUT = 8        # Per-page fetch timeout in seconds
WEB_RESEARCH_CONTEXT_BUDGET_CHARS = 4000  # Character budget for evidence
WEB_RESEARCH_PASSAGE_MAX_CHARS = 450 # Max passage size
WEB_RESEARCH_MAX_PASSAGES_PER_DOMAIN = 3 # Ensure domain diversity
WEB_RESEARCH_CACHE_TTL_SECONDS = 3600    # Cache TTL for URLs/queries
WEB_RESEARCH_CACHE_MAX_ENTRIES = 250     # Cache size limit

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
# Run web research test suite (28 tests)
pytest tests/test_web_research.py tests/test_web_research_fixes.py -v

# Run core unit and plugin tests
pytest tests/test_plugins.py tests/test_brain_memory.py tests/test_memory_manager.py -v
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
- **Single-user** - Designed for local, single-user operation
- **JSON storage** - Conversation indexing is JSON-based; not intended for large-scale multi-user persistence
- **Lightweight Lexical Retrieval** - Passage segmentation and relevance ranking use fast lexical matching (BM25/heading awareness) rather than dense neural embeddings, designed specifically for CPU efficiency alongside local lightweight models (e.g. Qwen 2.5 1.5B)
- **Static Web Extraction** - Web research fetches and parses static HTML pages; client-side JavaScript execution and Single Page Application (SPA) rendering are not supported
- **Search Engine Rate Limits** - Live queries use DuckDuckGo HTML endpoints; under high frequency or bot challenges (HTTP 202), requests may be throttled. Automatic backoff and snippet fallback mitigate this, but live page extraction can intermittently degrade to search snippets
- **Local Model Grounding** - Answer synthesis is constrained by the reasoning capacity of the local LLM. While prompt guardrails isolate untrusted web data and demand evidence-backed claims, local models are not immune to hallucination or synthesis errors
- **Memory search** - Long-term memory extraction remains heuristic and pattern-based
- **Web API** - Local developer interface without built-in authentication or rate limiting

### Workarounds
- Use local network only (no remote access)
- Archive old conversations periodically
- Run multiple instances for different users
- Implement reverse proxy with auth for production

## 📈 Roadmap

- [ ] Database migration (SQLite/PostgreSQL)
- [ ] Dense vector embeddings for memory and retrieval
- [ ] Headless browser rendering for dynamic web pages
- [ ] Multi-language support beyond Hindi
- [ ] Voice input/output (speech recognition)
- [ ] Authentication & multi-user support
- [ ] Mobile app
- [ ] Docker containerization
- [ ] Cloud deployment options

## 🔐 Privacy & Security

- ✅ **100% Local Processing** - No conversation or memory data sent to external servers
- ✅ **Offline Ready** - Core chat, memory, and local tools work without internet connection
- ✅ **Prompt Injection Boundaries** - Untrusted web data is fenced within explicit delimiters during synthesis
- ✅ **No API Keys** - No external paid services required
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

- [Memory & Context Benchmark](docs/MEMORY_CONTEXT_BENCHMARK.md) - Diagnostic audit of memory retention and context layer
- [Design System V1](docs/design/ATLAS_DESIGN_SYSTEM_V1.md) - Desktop UI design specifications and themes

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
