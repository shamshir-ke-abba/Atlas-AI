"""
Language Translator & Hinglish Handler

Detects Hinglish/Hindi input and translates to English
for processing, then translates response back.
"""

import re
from typing import Tuple


class LanguageTranslator:
    """
    Handles language detection and translation.
    Converts Hinglish to English for model processing.
    """

    # Devanagari Unicode ranges
    DEVANAGARI_RANGE = range(0x0900, 0x097F)
    
    # Common Hinglish words that indicate user is speaking Hindi/Hinglish
    HINGLISH_INDICATORS = {
        'kya', 'kaun', 'kahaan', 'kab', 'kaise', 'kyon', 'kyun',
        'haan', 'nahi', 'naa', 'haa',
        'mera', 'tera', 'tumhara', 'uska', 'unka', 'hamare',
        'main', 'tu', 'tum', 'voh', 'yeh', 'woh', 'ye',
        'naam', 'ghar', 'desh', 'shahr',
        'hai', 'hain', 'hona', 'hote', 'tha', 'the',
        'kar', 'kare', 'karta', 'karenge', 'kiya', 'kara',
        'acha', 'thik', 'bilkul', 'badhiya', 'shukriya', 'dhanyavaad',
        'namaskar', 'namaste', 'pranam', 'adab',
        'phir', 'milenge', 'bye', 'adios',
        'khaana', 'pani', 'chai', 'paani',
        'sukh', 'dukh', 'khush', 'udas',
        'pyar', 'dost', 'parivar',
        'bada', 'chota', 'sundar', 'khoobsurat',
        'aaj', 'kal', 'abhi', 'baad', 'pehle',
        'ek', 'do', 'teen', 'char', 'paanch',
    }
    
    # Common Hinglish transliteration patterns
    HINGLISH_TO_ENGLISH = {
        # Questions
        r'\bkya\b': 'what',
        r'\bkaun\b': 'who',
        r'\bkahaan\b': 'where',
        r'\bkab\b': 'when',
        r'\bkaise\b': 'how',
        r'\bkyon\b': 'why',
        r'\bkyun\b': 'why',
        
        # Affirmations
        r'\bhaan\b': 'yes',
        r'\bhaa\b': 'yes',
        r'\bnahi\b': 'no',
        r'\bnaa\b': 'no',
        r'\bthik\b': 'ok',
        r'\bbilkul\b': 'absolutely',
        r'\bacha\b': 'okay',
        
        # Possessives & Pronouns
        r'\bmera\b': 'my',
        r'\btera\b': 'your',
        r'\btumhara\b': 'your',
        r'\buska\b': 'his',
        r'\bunka\b': 'his',
        r'\bhamare\b': 'our',
        r'\bmain\b': 'i',
        r'\btu\b': 'you',
        r'\btum\b': 'you',
        r'\bvoh\b': 'he',
        r'\bwoh\b': 'he',
        r'\byeh\b': 'this',
        r'\bve\b': 'that',
        
        # Verbs
        r'\bkarte\b': 'do',
        r'\bkarta\b': 'does',
        r'\bkiya\b': 'did',
        r'\bkara\b': 'did',
        r'\bkar\b': 'do',
        r'\bde\b': 'give',
        r'\bdeta\b': 'gives',
        r'\bdiye\b': 'gave',
        r'\bjao\b': 'go',
        r'\bjata\b': 'goes',
        r'\bgaya\b': 'went',
        r'\baao\b': 'come',
        r'\bata\b': 'comes',
        r'\baya\b': 'came',
        
        # Common words
        r'\bnaam\b': 'name',
        r'\bghar\b': 'home',
        r'\bdesh\b': 'country',
        r'\bshahr\b': 'city',
        r'\bkhaana\b': 'food',
        r'\bpani\b': 'water',
        r'\bchai\b': 'tea',
        r'\bshukriya\b': 'thanks',
        r'\bdhanyavaad\b': 'thanks',
        r'\bnamaskar\b': 'hello',
        r'\bnamaste\b': 'greetings',
        
        # Adjectives
        r'\bbada\b': 'big',
        r'\bchota\b': 'small',
        r'\bsundar\b': 'beautiful',
        r'\bkhoobsurat\b': 'beautiful',
        r'\bacha\b': 'good',
        r'\bbura\b': 'bad',
        
        # Time
        r'\baaj\b': 'today',
        r'\bkal\b': 'tomorrow',
        r'\bkl\b': 'yesterday',
        r'\babhi\b': 'now',
    }

    # Devanagari to Latin transliteration (for pure Hindi text)
    DEVANAGARI_TO_LATIN = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
        'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'am', 'अः': 'ah',
        'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
        'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
        'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
        'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
        'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
        'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va',
        'श': 'sha', 'ष': 'sha', 'स': 'sa', 'ह': 'ha',
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    }

    @staticmethod
    def contains_devanagari(text: str) -> bool:
        """Check if text contains Devanagari script."""
        return any(
            ord(char) in LanguageTranslator.DEVANAGARI_RANGE
            for char in text
        )

    @staticmethod
    def contains_hinglish_words(text: str) -> bool:
        """Check if text contains common Hinglish words."""
        text_lower = text.lower()
        # Split into words and check if any are Hinglish indicators
        words = re.findall(r'\b\w+\b', text_lower)
        return any(word in LanguageTranslator.HINGLISH_INDICATORS for word in words)

    @staticmethod
    def is_hinglish(text: str) -> bool:
        """
        Detect if text is Hinglish (mix of English and Hindi).
        Checks for:
        1. Devanagari script
        2. Common Hinglish words
        """
        has_devanagari = LanguageTranslator.contains_devanagari(text)
        has_hinglish_words = LanguageTranslator.contains_hinglish_words(text)
        
        return has_devanagari or has_hinglish_words

    @staticmethod
    def transliterate_devanagari(text: str) -> str:
        """
        Basic Devanagari to Latin transliteration.
        Handles pure Hindi text conversion.
        """
        result = text
        for devanagari, latin in LanguageTranslator.DEVANAGARI_TO_LATIN.items():
            result = result.replace(devanagari, latin)
        return result

    @staticmethod
    def apply_hinglish_rules(text: str) -> str:
        """
        Apply common Hinglish-to-English translation rules.
        Case-insensitive pattern matching.
        """
        result = text
        
        # Apply transliteration patterns (case-insensitive)
        for pattern, replacement in LanguageTranslator.HINGLISH_TO_ENGLISH.items():
            compiled = re.compile(pattern, re.IGNORECASE)
            result = compiled.sub(replacement, result)
        
        return result

    @staticmethod
    def normalize_hinglish(text: str) -> str:
        """
        Normalize Hinglish text by:
        1. Transliterating Devanagari to Latin
        2. Applying Hinglish translation rules
        3. Cleaning up extra spaces
        """
        # Step 1: Transliterate Devanagari if present
        if LanguageTranslator.contains_devanagari(text):
            text = LanguageTranslator.transliterate_devanagari(text)
        
        # Step 2: Apply Hinglish rules
        text = LanguageTranslator.apply_hinglish_rules(text)
        
        # Step 3: Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def detect_and_convert(text: str) -> Tuple[str, bool, str]:
        """
        Detect language and convert if needed.
        
        Returns:
            Tuple of (converted_text, was_hinglish, original_language)
        """
        is_hinglish = LanguageTranslator.is_hinglish(text)
        
        if is_hinglish:
            converted = LanguageTranslator.normalize_hinglish(text)
            return converted, True, "hinglish"
        
        return text, False, "english"

    @staticmethod
    def add_hinglish_context(message: str) -> str:
        """
        Add Hinglish to the original message if detected.
        Helps preserve intent in the context.
        """
        if LanguageTranslator.is_hinglish(message):
            return f"[User is speaking in Hinglish/Hindi]\n{message}"
        return message


# Convenience functions
def is_hinglish(text: str) -> bool:
    """Quick check if text is Hinglish."""
    return LanguageTranslator.is_hinglish(text)


def normalize_hinglish(text: str) -> str:
    """Normalize Hinglish to English."""
    return LanguageTranslator.normalize_hinglish(text)


def detect_language(text: str) -> str:
    """Detect if text is Hinglish or English."""
    _, is_hin, lang = LanguageTranslator.detect_and_convert(text)
    return lang
