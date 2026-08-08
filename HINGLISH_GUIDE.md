# 🇮🇳 Hinglish Support - Feature Documentation

## Overview

Your Atlas AI now supports **Hinglish** (Hindi + English mix) conversations! This feature automatically detects when you're speaking in Hinglish and processes it correctly.

## What is Hinglish?

Hinglish is a mix of Hindi and English commonly spoken in India. Examples:
- "Kya haal hai?" (How are you?)
- "Mera naam Saad hai" (My name is Saad)
- "Main aaj office nahi jaunga" (I won't go to office today)
- "Bohot acha hai" (It's very good)

## Features Added

### 1. **Hinglish Detection**
- Automatically detects when you're writing in Hinglish
- Works with transliterated Hindi (Roman script)
- Also detects pure Devanagari script (native Hindi script)

### 2. **Intelligent Normalization**
- Converts Hinglish to English for better model understanding
- Preserves original message in conversation history
- Maps common Hinglish words to English equivalents

### 3. **Memory in Hinglish**
You can store memories in Hinglish:
- "Mera naam Saad hai" → Stores name in memory
- "Mera pasand rang blue hai" → Stores favorite color
- "Main Mumbai mein raata hoon" → Stores city

### 4. **Smart Recall**
Query your memories in Hinglish:
- "Mera naam kya hai?" → Recalls your name
- "Main kaha rhata hoon?" → Recalls your city
- "Mera naam?" → Recalls your name

### 5. **Devanagari Support**
The system can handle Hindi text written in Devanagari script:
- क्या हाल है? (Devanagari)
- Will be transliterated and processed correctly

## How It Works

### Processing Pipeline

```
User Input (Hinglish)
    ↓
Language Detection
    ↓
Hinglish Normalization (if needed)
    ↓
Pattern Matching & Memory Operations
    ↓
Context Building (with Hinglish awareness)
    ↓
LLM Processing
    ↓
Response Generation
    ↓
Conversation History (preserves original + response)
```

## Supported Hinglish Words

### Common Conversational Words
| Hinglish | English | Meaning |
|----------|---------|---------|
| haan | yes | Yes/Affirmative |
| nahi | no | No/Negative |
| kya | what | What |
| kaun | who | Who |
| kahaan | where | Where |
| kab | when | When |
| kaise | how | How |
| kyon | why | Why |
| thik | ok | Okay |
| acha | okay | Good/Okay |
| shukriya | thanks | Thank you |
| namaskar | hello | Hello |
| namaste | hello | Greetings |
| phir milenge | goodbye | See you later |

### Identity & Memories
| Hinglish | English | Pattern |
|----------|---------|---------|
| mera naam | my name | Identity storage |
| mujhe ghar | my home | Location storage |
| mera pasand | my preference | Preference storage |
| main | i | Subject reference |
| tumhara | your | Possession |
| uska | his/her | Possession |

### Action Words
| Hinglish | English | Meaning |
|----------|---------|---------|
| kar | do | Action |
| karte | doing | Continuous action |
| kara | did | Past action |
| de | give | Give |
| deta | gives | Gives |
| diye | gave | Gave |
| jao | go | Go |
| jata | goes | Goes |
| gaya | went | Went |
| aao | come | Come |
| ata | comes | Comes |
| aya | came | Came |

### Emotions & Descriptors
| Hinglish | English | Meaning |
|----------|---------|---------|
| sukh | happiness | Happy/Joy |
| dukh | sadness | Sad |
| pyar | love | Love |
| acha | good | Good |
| bura | bad | Bad |
| bada | big | Big |
| chota | small | Small |
| sunder | beautiful | Beautiful |

## Usage Examples

### Example 1: Memory Storage
```
You: "Mera naam Saad hai"
Atlas: [Stores "Saad" as your name]

You: "Main Delhi mein raata hoon"
Atlas: [Stores "Delhi" as your city]

You: "Mera pasand rang blue hai"
Atlas: [Stores "blue" as favorite color]
```

### Example 2: Memory Recall
```
You: "Mera naam kya hai?"
Atlas: "Your name is Saad"

You: "Main kaha rhata hoon?"
Atlas: "You live in Delhi"
```

### Example 3: Hinglish Conversation
```
You: "Aaj kaisa din raha?"
Atlas: [Processes: "How was your day today?"]
Atlas: [Responds with appropriate conversation]

You: "Mujhe samajh nahi aya"
Atlas: [Processes: "I didn't understand"]
Atlas: [Provides clarification]
```

### Example 4: Mixed Hinglish-English
```
You: "Mera name Saad hai aur main software engineer hoon"
Atlas: [Detects & normalizes Hinglish]
Atlas: [Responds in English, understanding the mix]
```

## Technical Details

### Language Detection Algorithm
- Scans for Devanagari Unicode range (0x0900 to 0x097F)
- Checks for English letters mixed with Hindi script
- Falls back to pattern matching for transliterated Hinglish

### Hinglish Normalization Process
1. **Devanagari Detection**: Checks if text contains Hindi script
2. **Transliteration**: Converts Devanagari to Latin script if found
3. **Pattern Matching**: Applies Hinglish-to-English rules
4. **Cleanup**: Removes extra spaces and normalizes formatting

### Files Modified
- `ai/translator.py` - NEW: Core Hinglish translation engine
- `ai/brain.py` - Added Hinglish detection & processing
- `ai/context_builder.py` - Added Hinglish awareness to context
- `ai/prompts.py` - Enhanced system prompt for language support
- `ai/memory_patterns.py` - Added Hinglish memory patterns

## Performance Notes

✅ **Pros:**
- Lightweight (no external API calls)
- Fast processing (pattern-based)
- Privacy-focused (all processing local)
- Transparent (original message preserved in history)

⚠️ **Current Limitations:**
- Dictionary-based approach (may miss new slang)
- Transliterated Hinglish works best (phonetic spelling)
- Some colloquialisms may not be recognized
- Model quality depends on Ollama's base training

## Future Enhancements

Potential improvements:
1. **Semantic Memory Search** - Find memories by meaning, not just exact matches
2. **Advanced Transliteration** - Better handling of regional variations
3. **Devanagari Expansion** - More comprehensive Hindi script support
4. **Language-Specific Responses** - Generate responses in Hinglish too
5. **Phonetic Flexibility** - Handle variations in spelling (e.g., "hain" vs "haan")

## Testing

To verify Hinglish support is working:

```python
from ai.translator import LanguageTranslator

# Test detection
text = "Kya haal hai aur tum kaise ho?"
converted, is_hinglish, lang = LanguageTranslator.detect_and_convert(text)

print(f"Original: {text}")
print(f"Normalized: {converted}")
print(f"Detected as: {lang}")
```

## Troubleshooting

**Q: My Hinglish isn't being recognized**
A: Make sure you're using transliterated Hindi (Roman script). Pure English-Hindi mixes work best.

**Q: Responses seem off**
A: The underlying model (qwen2.5:1.5b) may have limited Hinglish training. Try clearer English or pure English queries.

**Q: Can I disable Hinglish processing?**
A: The system is backward compatible. English-only conversations work as before.

---

**Enjoy chatting with Atlas in Hinglish! 🎉**
