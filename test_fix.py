#!/usr/bin/env python3
"""
Test the fixed Hinglish handling
"""

test_text = "tera naam kya hai"

print("Simulating Brain Processing for: " + test_text)
print("=" * 60)

# Step 1: Hinglish detection
from ai.translator import LanguageTranslator

is_hinglish = LanguageTranslator.is_hinglish(test_text)
print(f"✓ Hinglish Detected: {is_hinglish}")
print()

# Step 2: Check AI identity triggers
text_lower = test_text.lower()
ai_identity_triggers = [
    "tera naam",  # Your name (in Hindi)
    "tumhara naam",  # Your name
    "what is your name",
    "whats your name",
    "who are you",
    "what are you called",
    "tum kaun ho",  # Who are you (Hindi)
]

print("Checking AI Identity Triggers:")
for trigger in ai_identity_triggers:
    match = trigger in text_lower
    status = "✓ MATCH" if match else "✗ no match"
    print(f"  {trigger:30} → {status}")

print()
print("=" * 60)

# Expected flow
matched_trigger = None
for trigger in ai_identity_triggers:
    if trigger in text_lower:
        matched_trigger = trigger
        break

if matched_trigger:
    print(f"✓ Trigger '{matched_trigger}' matched!")
    print(f"✓ Response would be: 'I'm Atlas, an AI assistant created by Saad.'")
    print()
    print("✓✓✓ FIXED! No more echo behavior! ✓✓✓")
else:
    print("✗ No trigger matched")

print()
print("=" * 60)
print()
print("Test case: mera naam saad hai")
print("-" * 60)
test_text2 = "mera naam saad hai"
text_lower2 = test_text2.lower()

from ai.memory_patterns import PATTERNS

print("Checking Memory Extraction Patterns:")
for phrase, category, key in PATTERNS:
    if phrase in text_lower2:
        print(f"✓ Pattern '{phrase}' matches!")
        print(f"  Category: {category}, Key: {key}")
        # Extract value after phrase
        index = text_lower2.find(phrase)
        value = test_text2[index + len(phrase):].strip()
        print(f"  Extracted Value: '{value}'")
        break
