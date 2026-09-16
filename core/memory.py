"""
Atlas V3 Persistent Memory Manager.

Single source of truth for general user memory.
Provides safe fact extraction, normalized attribute indexing,
relevance scoring, and bounded retrieval to prevent prompt pollution.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import MEMORY_FILE

logger = logging.getLogger(__name__)

# Common stop words for token-overlap scoring
STOP_WORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
    "in", "on", "at", "to", "for", "with", "by", "about", "like", "through",
    "over", "before", "after", "between", "under", "above", "of", "from",
    "i", "me", "my", "myself", "we", "our", "ours", "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them",
    "that", "this", "these", "those", "what", "which", "who", "whom", "whose",
    "do", "does", "did", "have", "has", "had", "and", "or", "but", "if",
    "then", "so", "than", "too", "very", "can", "will", "just", "tell",
    "know", "remember", "saved", "stored", "say", "said",
    "favorite", "favourite", "best", "prefer", "preference",
}

# Words that indicate a sentence should not be parsed as a name or location
BLOCKED_NAME_WORDS: Set[str] = {
    "tired", "studying", "busy", "building", "working", "using", "creating",
    "developing", "making", "learning", "writing", "exploring", "researching",
    "hungry", "not", "a", "an", "the", "developer", "engineer", "designer",
    "student", "teacher", "doctor", "here", "there", "back", "done", "fine",
    "good", "okay", "ok", "happy", "sad", "from", "living", "feeling",
    "wondering", "thinking", "sure", "sorry", "planning", "going", "trying",
    "later", "today", "when", "free", "tomorrow", "soon", "again", "anytime",
    "sometime", "tonight", "yesterday", "fear", "constant", "peace", "pain",
    "poverty", "denial", "danger", "hope", "silence", "chaos", "luxury",
    "shame", "secret", "near", "nearby", "front", "grocery", "store",
}

# Canonical attribute synonyms and aliases for semantic matching
ATTRIBUTE_SYNONYMS: Dict[Tuple[str, str], List[str]] = {
    ("identity", "name"): [
        "name", "naam", "call me", "who am i", "who i am", "my name", "what is my name",
    ],
    ("identity", "city"): [
        "live", "living", "stay", "staying", "city", "location", "based", "reside",
        "residing", "home", "hometown", "rehta", "ghar", "kahan", "where do i live",
        "where i live", "where am i", "address", "relocated",
    ],
    ("identity", "workplace"): [
        "work", "company", "employer", "office", "job", "workplace", "working at",
        "employed", "firm",
    ],
    ("identity", "role"): [
        "role", "profession", "occupation", "job", "career", "title", "engineer",
        "developer", "what do i do", "my job",
    ],
    ("preferences", "favorite_color"): [
        "color", "colour", "rang", "favorite color", "favourite color", "best color",
    ],
    ("preferences", "favorite_food"): [
        "food", "eat", "dish", "cuisine", "meal", "khana", "favorite food",
        "favourite food", "best food", "favorite dish",
    ],
    ("preferences", "ui_theme"): [
        "theme", "dark mode", "light mode", "mode", "appearance", "ui theme",
    ],
    ("preferences", "explanation_style"): [
        "explanation", "explain", "style", "answers", "explanations", "first principles",
        "step by step", "concise", "detailed", "preference for answers",
    ],
    ("environment", "operating_system"): [
        "os", "operating system", "distro", "distribution", "linux", "ubuntu",
        "windows", "macos", "debian", "fedora", "system", "platform", "what system do i use",
    ],
    ("projects", "project_name"): [
        "project", "app", "application", "software", "codebase", "what is my project",
        "what project", "project name", "app called", "game", "game called", "game name",
        "what game", "working on", "what am i working on", "name of the game",
    ],
    ("projects", "technology"): [
        "language", "tech", "technology", "written in", "python", "stack", "framework",
        "tech stack", "built with", "developed in",
    ],
    ("projects", "runtime"): [
        "runtime", "ollama", "local", "runs locally", "how does it run", "platform runtime",
    ],
    ("goals", "goal"): [
        "goal", "goals", "plan", "planning", "want to achieve", "target", "objective",
    ],
}


class MemoryManager:

    def __init__(self, memory_file: Optional[Any] = None):
        if memory_file is not None:
            self.file = Path(memory_file)
        else:
            self.file = MEMORY_FILE

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file.exists():
            self._save(self._default())

        self._last_extracted_text: Optional[str] = None

    # ==================================================
    # DEFAULT STRUCTURE
    # ==================================================

    @staticmethod
    def _default() -> Dict[str, Any]:
        return {
            "identity": {},
            "preferences": {},
            "projects": {},
            "environment": {},
            "facts": {},
            "goals": {},
        }

    # ==================================================
    # STORAGE
    # ==================================================

    def _load(self) -> Dict[str, Any]:
        try:
            with self.file.open(
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return self._default()

            return data

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            logger.warning(
                "Could not load memory: %s",
                exc,
            )
            return self._default()

    def _save(self, data: Dict[str, Any]) -> None:
        temporary = self.file.with_suffix(".tmp")

        with temporary.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )

        temporary.replace(self.file)

    # ==================================================
    # BASIC MEMORY API
    # ==================================================

    def remember(
        self,
        category: str,
        key: str,
        value: Any,
    ) -> None:

        category = str(category or "").strip()
        key = str(key or "").strip()

        if not category or not key:
            return

        data = self._load()

        if category not in data:
            data[category] = {}

        if not isinstance(data[category], dict):
            data[category] = {}

        data[category][key] = value

        self._save(data)

        logger.info(
            "Memory saved: %s.%s",
            category,
            key,
        )

    def recall(
        self,
        category: str,
        key: str,
    ) -> Optional[Any]:

        data = self._load()

        section = data.get(
            category,
            {},
        )

        if not isinstance(section, dict):
            return None

        return section.get(key)

    def forget(
        self,
        category: str,
        key: str,
    ) -> None:

        data = self._load()

        section = data.get(category)

        if not isinstance(section, dict):
            return

        section.pop(key, None)

        if not section:
            data.pop(category, None)

        self._last_extracted_text = None
        self._save(data)

    def all(self) -> Dict[str, Any]:
        return self._load()

    def clear(self) -> None:
        self._last_extracted_text = None
        self._save(self._default())

    # ==================================================
    # SAFE FACT EXTRACTION
    # ==================================================

    def extract_from_message(
        self,
        message: str,
    ) -> None:
        """
        Extract explicit, high-confidence personal facts from user statements.
        Supports multi-word names, relocations, dynamic preferences, Hinglish,
        and includes strict negation checks to prevent false positives.
        """

        text = " ".join(
            str(message or "").strip().split()
        )

        if not text:
            return

        if getattr(self, "_last_extracted_text", None) == text:
            return
        self._last_extracted_text = text

        lower = text.lower()

        # --------------------------------------------------
        # Explicit "remember that" statements
        # --------------------------------------------------

        match = re.search(
            r"\bremember that\s+(.+?)(?:[.!?]|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            fact = match.group(1).strip()
            if fact:
                facts = self._load().get("facts", {})
                if not isinstance(facts, dict):
                    facts = {}

                next_id = str(len(facts) + 1)
                self.remember("facts", next_id, fact)

        # --------------------------------------------------
        # Name Extraction (Single-word, Multi-word, Hinglish)
        # --------------------------------------------------

        name_extracted = False
        # Check negation for name: "my name is not...", "i am not..."
        name_negated = bool(re.search(
            r"\b(?:my name is not|my name isn't|i am not|i'm not|not named)\b",
            lower,
        ))

        if not name_negated:
            name_patterns = (
                # Hinglish: "Mera naam Saad Khan hai" or "Mera naam Saad"
                r"\bmera naam\s+([A-Za-z][A-Za-z0-9 .'-]*?)(?:\s+hai\b|[.!?,;:]|$)",
                # English: "My name is Saad Khan"
                r"\bmy name is\s+([A-Za-z][A-Za-z0-9 .'-]*?)(?:\s+(?:and|but|who|which|i am|i'm|i live|living|working|using|also|from)\b|[.!?,;:]|$)",
                # English: "Call me Saad Khan"
                r"\bcall me\s+([A-Za-z][A-Za-z0-9 .'-]*?)(?:\s+(?:and|but|who|which|i am|i'm|i live|living|working|using|also|from)\b|[.!?,;:]|$)",
                # English: "I am Saad Khan" / "I'm Saad"
                r"\b(?:i am|i'm)\s+([A-Za-z][A-Za-z0-9 .'-]*?)(?:\s+(?:and|but|who|which|i live|living|working|using|also|from)\b|[.!?,;:]|$)",
            )

            for pattern in name_patterns:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    candidate = m.group(1).strip(" .,!?:;\"'")
                    if candidate:
                        words = candidate.split()
                        words_lower = [w.lower() for w in words]

                        # Validation:
                        # - 1 to 4 words
                        # - No word in blocked list
                        # - No word ends in "ing"
                        # - Length <= 40 chars
                        is_valid = (
                            1 <= len(words) <= 4
                            and len(candidate) <= 40
                            and not any(w in BLOCKED_NAME_WORDS for w in words_lower)
                            and not any(w.endswith("ing") for w in words_lower)
                        )

                        if is_valid:
                            self.remember("identity", "name", candidate)
                            name_extracted = True
                            break

        # --------------------------------------------------
        # City / Location Extraction (With Relocation Support)
        # --------------------------------------------------

        # Check negation: "I don't live in Mumbai", "I am not from Mumbai"
        city_negated = bool(re.search(
            r"\b(?:don't live|do not live|not living|not from|never lived)\b",
            lower,
        ))

        if not city_negated:
            city_patterns = (
                # Standard: "I live in Mumbai", "I reside in Berlin", "I am based in Tokyo"
                r"\b(?:i live in|i reside in|i am based in|i'm based in|i am living in|i'm living in)\s+([A-Za-z][A-Za-z .'-]*?)(?:\s+(?:and|but|since|for|with|currently)\b|[.!?,;:]|$)",
                # Relocation: "I moved to Berlin", "I've moved to Tokyo"
                r"\b(?:i moved to|i have moved to|i've moved to|i relocated to)\s+([A-Za-z][A-Za-z .'-]*?)(?:\s+(?:and|but|since|for|from|with|recently)\b|[.!?,;:]|$)",
                # Hinglish: "Main Mumbai me rehta hu"
                r"\bmain\s+([A-Za-z][A-Za-z .'-]*?)\s+(?:me|mein)\s+rehta\s+(?:hu|hoon)\b",
            )

            for pattern in city_patterns:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    city = m.group(1).strip(" .,!?:;\"'")
                    if city and len(city) <= 40 and not any(w in BLOCKED_NAME_WORDS for w in city.lower().split()):
                        self.remember("identity", "city", city)
                        break

        # --------------------------------------------------
        # Workplace / Employment Extraction
        # --------------------------------------------------

        work_match = re.search(
            r"\b(?:i work at|i work for|employed at|employed by)\s+([A-Za-z0-9][A-Za-z0-9 .'-]*?)(?:\s+(?:as|and|but|since|in)\b|[.!?,;:]|$)",
            text,
            re.IGNORECASE,
        )
        if work_match:
            workplace = work_match.group(1).strip(" .,!?:;\"'")
            if workplace and len(workplace) <= 40:
                self.remember("identity", "workplace", workplace)

        # --------------------------------------------------
        # Preferences Extraction (Color, Food, Dynamic Categories)
        # --------------------------------------------------

        # Check general preference negation: "I don't like coffee", "I dislike..."
        pref_negated = bool(re.search(r"\b(?:don't like|do not like|dislike|hate|never like)\b", lower))

        # 1. Favorite color
        color_match = re.search(
            r"\bmy favou?rite color is\s+(?:now\s+)?(.+?)(?:\s+and\b|[.!?,;:]|$)",
            text,
            re.IGNORECASE,
        )
        if not color_match:
            color_match = re.search(
                r"\bmera pasand rang\s+(.+?)(?:\s+hai\b|[.!?,;:]|$)",
                text,
                re.IGNORECASE,
            )

        if color_match and not pref_negated:
            color_val = color_match.group(1).strip(" .,!?:;\"'")
            if color_val:
                self.remember("preferences", "favorite_color", color_val)

        # 2. Favorite food
        food_match = re.search(
            r"\bmy favou?rite food is\s+(?:now\s+)?(.+?)(?:\s+and\b|[.!?,;:]|$)",
            text,
            re.IGNORECASE,
        )
        if not food_match:
            food_match = re.search(
                r"\bmera pasand khana\s+(.+?)(?:\s+hai\b|[.!?,;:]|$)",
                text,
                re.IGNORECASE,
            )

        if food_match and not pref_negated:
            food_val = food_match.group(1).strip(" .,!?:;\"'")
            if food_val:
                self.remember("preferences", "favorite_food", food_val)

        # 3. Dynamic favorites: "my favorite <category> is <item>" (e.g. anime, movie, sport, game)
        dyn_match = re.search(
            r"\bmy favou?rite\s+([A-Za-z0-9_-]+)\s+is\s+(?:now\s+)?(.+?)(?:\s+and\b|[.!?,;:]|$)",
            text,
            re.IGNORECASE,
        )
        if dyn_match and not pref_negated:
            cat_name = dyn_match.group(1).strip().lower()
            item_val = dyn_match.group(2).strip(" .,!?:;\"'")
            if cat_name not in ("color", "food") and item_val:
                self.remember("preferences", f"favorite_{cat_name}", item_val)

        # 4. UI theme preference
        theme_match = re.search(
            r"\b(?:i love|i prefer|i like|i use)\s+(dark mode|light mode|dark theme|light theme)\b",
            lower,
        )
        if not theme_match:
            theme_match = re.search(
                r"\bmujhe\s+(dark theme|dark mode|light theme|light mode)\s+pasand hai\b",
                lower,
            )

        if theme_match and not pref_negated:
            self.remember("preferences", "ui_theme", theme_match.group(1).strip())

        # 5. Explanation style
        for style in (
            "first principles",
            "first-principles",
            "step by step",
            "step-by-step",
            "concise",
            "detailed",
            "practical",
        ):
            if style in lower and re.search(
                r"\b(?:i prefer|i like|i enjoy|i value|i usually prefer|i want)\b",
                lower,
            ) and not pref_negated:
                self.remember("preferences", "explanation_style", style)
                break

        # --------------------------------------------------
        # Project / Technology Extraction
        # --------------------------------------------------

        project_name = None
        technology = None
        runtime = None

        project_patterns = (
            r"\b(?:(?:i'?m|i am)\s+(?:working on|building|developing|creating|making)|i work on|my project|this project|project|app|application)\s+(?:an?\s+)?(?:[A-Za-z0-9 _-]*?\s+)?(?:called|named|is called|is named)\s+[\"']?([A-Za-z0-9 _-]+?)[\"']?(?:\s+in\s+([A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
            r"\b(?:i(?:'m| am)|i work on|i'm working on|i am working on|my project|this project|project)\s+(?:building|working on|developing|creating|making)\s+(?:an?\s+)?(?:[A-Za-z][A-Za-z0-9 _-]*?\s+)?(?:called|named)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
            r"\b(?:my project|this project|project|app|application)\s+(?:is|is called|called)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+(?:written|built|developed|in|using)\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
            r"\b([A-Za-z][A-Za-z0-9_-]*)\s+is\s+written\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+)",
            r"\b(?:i(?:'m| am)|i work on|i'm working on|i am working on)\s+(?:on|with)\s+([A-Za-z][A-Za-z0-9 _-]*?)(?:\s+in\s+([A-Za-z][A-Za-z0-9_.+-]+))?(?:[.!?]|$)",
        )

        for pattern in project_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                groups = m.groups() or ()
                project_name = (groups[0] if groups else "").strip(" .,!?:;\"") if groups else ""
                technology = (groups[1] if len(groups) > 1 and groups[1] is not None else "").strip(" .,!?:;\"")

                if project_name:
                    cleaned = project_name.lower()
                    if cleaned.startswith(("uses ", "runs ", "running ", "working ", "building ", "developing ", "creating ", "written ", "called ", "named ", "is ", "is called ")):
                        project_name = None
                    else:
                        project_name = re.sub(r"^(?:my project|this project|project|app|application|atlasai)\s+", "", project_name, flags=re.IGNORECASE).strip()

                if project_name or technology:
                    break

        if project_name:
            existing = self.recall("projects", "project_name")
            if existing:
                existing_norm = str(existing).strip().lower()
                project_norm = str(project_name).strip().lower()
                if project_norm.startswith(existing_norm) or existing_norm.startswith(project_norm):
                    project_name = existing
                elif project_norm.endswith("ai") and existing_norm == project_norm[:-2]:
                    project_name = existing

            self.remember("projects", "project_name", project_name)

        if technology:
            self.remember("projects", "technology", technology)

        # Runtime
        runtime_patterns = (
            r"\b(?:my project|this project|atlasai|my ai|it|the app|the application)\s+(?:uses?|is using)\s+([A-Za-z][A-Za-z0-9_.+-]+)",
            r"\b(?:my project|this project|atlasai|my ai|it|the app|the application)\s+runs?\s+locally(?:\s+using\s+([A-Za-z][A-Za-z0-9_.+-]+))?",
            r"\b(?:it|atlasai|my project|my ai|this app)\s+uses\s+ollama\b",
        )

        for pattern in runtime_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                runtime = (m.group(1) or m.group(2) or "local").strip(" .,!?:;\"")
                if runtime.lower() in {"local", "locally"}:
                    runtime = "local"
                self.remember("projects", "runtime", runtime)
                break

        if not runtime and re.search(r"\b(?:runs locally|runs locally using ollama|my ai runs locally)\b", lower):
            self.remember("projects", "runtime", "local")

        # --------------------------------------------------
        # Operating System Extraction
        # --------------------------------------------------

        os_names = (
            "ubuntu",
            "windows",
            "macos",
            "linux",
            "debian",
            "fedora",
        )

        os_negated = bool(
            re.search(
                r"\b(?:not using|don't use|do not use|not on|never use|isn't|is not|not)\s+(?:a\s+)?(?:windows|linux|ubuntu|macos|debian|fedora)\b",
                lower,
            )
        )

        if not os_negated:
            for os_name in os_names:
                if os_name in lower and re.search(
                    r"\b(?:i use|i'm using|i usually use|i run|i work on|i work with|my operating system|os|using)\b",
                    lower,
                ):
                    label = os_name.title() if os_name != "macos" else "macOS"
                    if os_name == "linux":
                        label = "Linux"
                    self.remember("environment", "operating_system", label)
                    break

    # ==================================================
    # RELEVANT MEMORY RETRIEVAL (P1)
    # ==================================================

    def relevant(
        self,
        message: str,
    ) -> Dict[str, Any]:
        """
        Return only memory segments specifically relevant to the user request.
        Uses normalized attribute matching, synonym aliases, and token overlap.
        Prevents full category dumping and context pollution.
        """
        return self.retrieve_relevant_memories(message)

    def retrieve_relevant_memories(
        self,
        query: str,
        max_items: int = 4,
        score_threshold: float = 0.45,
    ) -> Dict[str, Any]:
        """
        Lightweight, deterministic memory retrieval and relevance scoring.
        Ranks candidate memory items and returns only relevant entries.
        """

        raw_query = str(query or "").strip()
        if not raw_query:
            return {}

        lower_query = raw_query.lower()
        # Clean query tokens (letters and numbers only)
        query_tokens = set(re.findall(r"\b[a-z0-9_-]+\b", lower_query))
        meaningful_query_tokens = query_tokens - STOP_WORDS

        data = self._load()
        if not data:
            return {}

        # --------------------------------------------------
        # Step 1: Detect Broad Memory Queries
        # --------------------------------------------------

        broad_triggers = (
            "what do you remember",
            "what do you know about me",
            "tell me what you know",
            "what do you know",
            "everything you remember",
            "list my memories",
            "show memories",
            "all memories",
            "what is in your memory",
        )

        is_broad = any(t in lower_query for t in broad_triggers)

        # Check if the query is actually specific despite having 'remember'
        # e.g., "Do you remember my favorite color?" or "Do you remember where I live?"
        has_specific_term = any(
            token in query_tokens
            for token in (
                "color", "colour", "food", "city", "live", "living", "stay", "staying",
                "name", "naam", "os", "linux", "ubuntu", "windows", "macos", "project",
                "app", "technology", "anime", "movie", "sport", "game", "work", "job",
            )
        )

        if is_broad and not has_specific_term:
            # Return a bounded summary (top items from identity, preferences, facts)
            # strictly limited to avoid dumping the whole database
            bounded_result: Dict[str, Any] = {}

            ident = data.get("identity", {})
            if ident:
                bounded_result["identity"] = {k: ident[k] for k in list(ident.keys())[:2]}

            prefs = data.get("preferences", {})
            if prefs:
                bounded_result["preferences"] = {k: prefs[k] for k in list(prefs.keys())[:2]}

            env = data.get("environment", {})
            if env and "operating_system" in env:
                bounded_result["environment"] = {"operating_system": env["operating_system"]}

            facts = data.get("facts", {})
            if facts:
                bounded_result["facts"] = {k: facts[k] for k in list(facts.keys())[:2]}

            return bounded_result

        # --------------------------------------------------
        # Step 2: Score Candidate Memories
        # --------------------------------------------------

        scored_candidates: List[Tuple[float, str, str, Any]] = []

        for category, section in data.items():
            if not isinstance(section, dict):
                continue

            for key, value in section.items():
                if value is None or value == "":
                    continue

                score = 0.0
                attr_pair = (category, key)

                # 1. Attribute synonyms match
                synonyms = ATTRIBUTE_SYNONYMS.get(attr_pair, [])

                # Dynamic preference key handling: e.g. "favorite_anime" -> "anime"
                if category == "preferences" and key.startswith("favorite_"):
                    custom_tag = key.replace("favorite_", "")
                    synonyms = list(synonyms) + [custom_tag, f"favorite {custom_tag}", f"favourite {custom_tag}"]

                for syn in synonyms:
                    if attr_pair == ("identity", "city") and syn in ("city", "location"):
                        if not any(
                            w in query_tokens
                            for w in (
                                "my", "i", "me", "live", "living", "stay", "staying",
                                "reside", "residing", "based", "where", "which", "home",
                            )
                        ):
                            continue

                    if syn in lower_query:
                        # Full phrase match gets top score
                        score = max(score, 0.95 if " " in syn else 0.85)
                    else:
                        syn_meaningful = [st for st in syn.split() if st not in STOP_WORDS]
                        if syn_meaningful and all(st in query_tokens for st in syn_meaningful):
                            score = max(score, 0.80)

                # 2. Match fact text via token overlap
                if category == "facts":
                    fact_str = str(value).lower()
                    fact_tokens = set(re.findall(r"\b[a-z0-9_-]+\b", fact_str)) - STOP_WORDS
                    if fact_tokens and meaningful_query_tokens:
                        intersection = fact_tokens & meaningful_query_tokens
                        overlap_ratio = len(intersection) / len(meaningful_query_tokens)
                        if overlap_ratio >= 0.5:
                            score = max(score, 0.75 + (0.2 * overlap_ratio))
                        elif len(intersection) >= 1 and ("remember" in query_tokens or "tell" in query_tokens):
                            score = max(score, 0.60)

                # 3. Value token match (e.g. query mentions "Rex" or "Mumbai" or "Python")
                val_str = str(value).lower()
                val_tokens = set(re.findall(r"\b[a-z0-9_-]+\b", val_str)) - STOP_WORDS
                if val_tokens and (val_tokens & meaningful_query_tokens):
                    score = max(score, 0.70)

                if score >= score_threshold:
                    scored_candidates.append((score, category, key, value))

        # --------------------------------------------------
        # Step 3: Rank, Filter Top-K, and Format
        # --------------------------------------------------

        if not scored_candidates:
            return {}

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        top_score = scored_candidates[0][0]
        min_allowed = max(score_threshold, top_score - 0.20) if top_score >= 0.80 else score_threshold

        result: Dict[str, Any] = {}
        for s, category, key, value in scored_candidates[:max_items]:
            if s < min_allowed:
                continue
            if category not in result:
                result[category] = {}
            result[category][key] = value

        return result
