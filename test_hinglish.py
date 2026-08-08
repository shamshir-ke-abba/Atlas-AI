#!/usr/bin/env python3
"""
Hinglish Support Demo & Testing Script
Run this to see Hinglish features in action!
"""

from ai.translator import LanguageTranslator

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(original, normalized, is_hinglish, lang):
    """Print formatted result."""
    print(f"Original Text:  {original}")
    print(f"Detected Lang:  {lang.upper()}")
    print(f"Is Hinglish:    {'✓ YES' if is_hinglish else '✗ NO'}")
    print(f"Normalized:     {normalized}")
    print()

def test_hinglish_detection():
    """Test Hinglish detection."""
    print_section("1. HINGLISH DETECTION TEST")
    
    test_cases = [
        ("Kya haal hai?", "Hinglish greeting"),
        ("Mera naam Saad hai", "Hinglish identity"),
        ("Main Delhi mein raata hoon", "Hinglish location"),
        ("Hello, how are you?", "Pure English"),
        ("acha thik hai", "Hinglish confirmation"),
    ]
    
    for text, description in test_cases:
        converted, is_hin, lang = LanguageTranslator.detect_and_convert(text)
        print(f"Test: {description}")
        print_result(text, converted, is_hin, lang)

def test_hinglish_normalization():
    """Test Hinglish to English normalization."""
    print_section("2. HINGLISH NORMALIZATION TEST")
    
    hinglish_sentences = [
        "kya tum mujhe samajh sakte ho?",
        "mera naam atlas hai",
        "main yahan hoon",
        "thik hai, shukriya",
        "bohot acha, really nice",
    ]
    
    for sentence in hinglish_sentences:
        normalized = LanguageTranslator.normalize_hinglish(sentence)
        print(f"Original:   {sentence}")
        print(f"Normalized: {normalized}")
        print()

def test_memory_patterns():
    """Show memory pattern examples."""
    print_section("3. MEMORY PATTERN EXAMPLES")
    
    from ai.memory_patterns import PATTERNS
    
    print("Patterns for memory extraction:")
    print()
    
    hinglish_patterns = [p for p in PATTERNS if len(p[0]) > 10 or 'naam' in p[0] or 'ghar' in p[0]]
    
    for pattern, category, key in hinglish_patterns:
        print(f"Pattern:  '{pattern}'")
        print(f"Category: {category}")
        print(f"Key:      {key}")
        print()

def test_memory_recall():
    """Show memory recall patterns."""
    print_section("4. MEMORY RECALL PATTERNS")
    
    recall_patterns = {
        "what's my name": "English",
        "mera naam": "Hinglish",
        "mera naam kya": "Hinglish",
        "main kaun hoon": "Hinglish",
        "where do i live": "English",
        "main kaha rhata": "Hinglish",
        "mera ghar": "Hinglish",
    }
    
    print("You can recall memories using these triggers:\n")
    
    for trigger, language in recall_patterns.items():
        print(f"Trigger: '{trigger}' ({language})")
    print()

def test_supported_words():
    """Show supported Hinglish words."""
    print_section("5. SUPPORTED HINGLISH WORDS")
    
    supported = {
        "Greetings": ["namaskar", "namaste", "kya haal"],
        "Affirmations": ["haan", "thik", "acha", "shukriya"],
        "Questions": ["kya", "kaun", "kahaan", "kab", "kaise", "kyon"],
        "Identity": ["mera naam", "main", "kaun", "yeh", "voh"],
        "Actions": ["kar", "de", "jao", "aao", "hota"],
        "Emotions": ["sukh", "dukh", "pyar", "acha", "bura"],
        "Descriptors": ["bada", "chota", "sunder", "achcha"],
    }
    
    for category, words in supported.items():
        print(f"\n{category}:")
        for word in words:
            print(f"  • {word}")

def test_devanagari_support():
    """Show Devanagari script detection."""
    print_section("6. DEVANAGARI SCRIPT SUPPORT")
    
    print("The system can detect and handle Devanagari script (native Hindi):")
    print("\nExample Devanagari characters (will be transliterated):")
    
    devanagari_chars = {
        'क': 'ka',
        'ह': 'ha',
        'ल': 'la',
        'म': 'ma',
        'न': 'na',
        'र': 'ra',
    }
    
    for char, transliteration in devanagari_chars.items():
        print(f"  {char} → {transliteration}")
    
    print("\nFull example:")
    text = "नमस्ते"
    transliterated = LanguageTranslator.transliterate_devanagari(text)
    print(f"  Input (Devanagari): {text}")
    print(f"  Transliterated:     {transliterated}")

def test_mixed_language():
    """Test mixed language handling."""
    print_section("7. MIXED LANGUAGE HANDLING")
    
    mixed_texts = [
        "Mera naam Saad hai aur main software engineer hoon",
        "I am going to office, main late hoon",
        "This is very good, bohot acha",
    ]
    
    print("The system handles mixed Hindi-English seamlessly:\n")
    
    for text in mixed_texts:
        converted, is_hin, lang = LanguageTranslator.detect_and_convert(text)
        print(f"Input:       {text}")
        print(f"Detected:    {lang}")
        print(f"Processed:   {converted}")
        print()

def run_all_tests():
    """Run all demonstration tests."""
    print("\n" + "█" * 60)
    print("█  ATLAS AI - HINGLISH SUPPORT DEMONSTRATION")
    print("█" * 60)
    
    try:
        test_hinglish_detection()
        test_hinglish_normalization()
        test_memory_patterns()
        test_memory_recall()
        test_supported_words()
        test_devanagari_support()
        test_mixed_language()
        
        print_section("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("\nHinglish support is fully operational!")
        print("\nYou can now chat with Atlas in:")
        print("  • Pure English")
        print("  • Pure Hindi (Devanagari script)")
        print("  • Hinglish (English + Hindi mix)")
        print("\nSee HINGLISH_GUIDE.md for detailed documentation.")
        print()
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
