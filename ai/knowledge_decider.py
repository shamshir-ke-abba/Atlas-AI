"""
Atlas V3 Knowledge Decider

Decides whether a question should use:

LOCAL -> Local model
WEB   -> Web search
BOTH  -> Local model + web search

Lightweight rule-based routing layer.
"""

import re

from dataclasses import dataclass
from enum import Enum


# ============================================================
# Decision Types
# ============================================================


class Decision(Enum):

    LOCAL = "local"

    WEB = "web"

    BOTH = "both"


@dataclass
class DecisionResult:

    decision: Decision
    reason: str
    confidence: float


# ============================================================
# Knowledge Decider
# ============================================================


class KnowledgeDecider:

    def __init__(self):

        # ----------------------------------------------------
        # Explicit capability questions
        # ----------------------------------------------------

        self.capability_patterns = [

            r"\bwhat tools do you have\b",
            r"\bwhat tools are available\b",
            r"\bwhat capabilities do you have\b",
            r"\bwhat can you do\b",
            r"\bwhat are your capabilities\b",

            r"\bcan you search the web\b",
            r"\bcan you search online\b",
            r"\bcan you browse the web\b",
            r"\bcan you browse online\b",
            r"\bcan you access the internet\b",

            r"\bdo you have web search\b",
            r"\bdo you have web access\b",
            r"\bdo you have internet access\b",
            r"\bdo you have access to the internet\b",

            r"\bcan atlas search the web\b",
            r"\bcan atlas browse the web\b",
            r"\bdoes atlas have web search\b",
            r"\bdoes atlas have web access\b",
        ]

        # ----------------------------------------------------
        # Explicit current / live information
        # ----------------------------------------------------

        self.web_patterns = [

            r"\btoday\b",
            r"\btonight\b",
            r"\byesterday\b",
            r"\btomorrow\b",

            r"\bcurrently\b",
            r"\bcurrent\b",
            r"\bright now\b",

            r"\blatest\b",
            r"\brecent\b",
            r"\bnewest\b",

            r"\bthis week\b",
            r"\bthis month\b",
            r"\bthis year\b",

            r"\blive\b",
            r"\bnews\b",

            r"\bcurrent price\b",
            r"\bstock price\b",
            r"\bshare price\b",

            r"\bweather\b",
            r"\btemperature\b",

            r"\bwho won\b",
            r"\bwho is winning\b",

            r"\bwhat happened\b",
            r"\bwhat's happening\b",

            r"\brelease date\b",
            r"\bversion\b",

            r"\bscore\b",
            r"\bscores\b",
            r"\bstandings\b",

            r"\bmarket\b",
            r"\bprice\b",
        ]

        # ----------------------------------------------------
        # Questions requiring fresh information + reasoning
        # ----------------------------------------------------

        self.both_patterns = [

            r"\bnew discovery\b",
            r"\bnew research\b",
            r"\brecent research\b",
            r"\blatest research\b",

            r"\bnew technology\b",
            r"\bnew model\b",
            r"\bnew feature\b",

            r"\b2026\b",
            r"\b2027\b",

            r"\bwhat has changed\b",
            r"\bwhat changed\b",

            r"\bis .+ still\b",
            r"\bis .+ still relevant\b",
        ]

        # ----------------------------------------------------
        # Established knowledge domains
        # ----------------------------------------------------

        self.local_patterns = [

            # Mathematics

            r"\bmath\b",
            r"\bmathematics\b",
            r"\bsolve\b",
            r"\bcalculate\b",
            r"\bdifferentiate\b",
            r"\bintegrate\b",
            r"\bintegral\b",
            r"\bderivative\b",
            r"\blimit\b",
            r"\bequation\b",
            r"\bquadratic\b",
            r"\bprobability\b",
            r"\bvector\b",
            r"\bmatrix\b",
            r"\bgeometry\b",
            r"\btrigonometry\b",
            r"\bcalculus\b",

            # Physics

            r"\bphysics\b",
            r"\bnewton\b",
            r"\bforce\b",
            r"\bvelocity\b",
            r"\bacceleration\b",
            r"\bprojectile\b",
            r"\bmomentum\b",
            r"\benergy\b",
            r"\bwork\b",
            r"\bpower\b",
            r"\bgravity\b",
            r"\belectricity\b",
            r"\bmagnetic\b",
            r"\bwave\b",
            r"\boptics\b",

            # Chemistry

            r"\bchemistry\b",
            r"\batomic\b",
            r"\batom\b",
            r"\belectron\b",
            r"\bproton\b",
            r"\bneutron\b",
            r"\bbond\b",
            r"\bchemical\b",
            r"\bion\b",
            r"\bmolecule\b",
            r"\bperiodic table\b",
            r"\boxidation\b",
            r"\breduction\b",
            r"\bcompound\b",
            r"\bequilibrium\b",

            # Programming

            r"\bpython\b",
            r"\bprogramming\b",
            r"\bcode\b",
            r"\bfunction\b",
            r"\bvariable\b",
            r"\balgorithm\b",
            r"\bdebug\b",
            r"\bbug\b",
            r"\bsyntax\b",
            r"\brecursion\b",
            r"\bclass\b",
            r"\bobject\b",
            r"\blist\b",
            r"\bdictionary\b",
            r"\bapi\b",
            r"\bprogram\b",

            # Linux

            r"\blinux\b",
            r"\bubuntu\b",
            r"\bterminal\b",
            r"\bshell\b",
            r"\bchmod\b",
            r"\bsudo\b",
            r"\bprocess\b",
            r"\bcommand\b",
            r"\bfilesystem\b",
            r"\bkernel\b",
            r"\bsystemd\b",

            # General established knowledge

            r"\bhow does\b",
            r"\bwhy does\b",
            r"\bwhat is\b",
            r"\bwhat are\b",
            r"\bexplain\b",
        ]

        # ----------------------------------------------------
        # Computational questions
        # ----------------------------------------------------

        self.calculation_patterns = [

            r"\d+\s*[\+\-\*/]\s*\d+",

            r"\d+\s*[xX]\s*[\+\-]",

            r"\bhow many\b",
            r"\bhow much\b",

            r"\bcalculate\b",
            r"\bcompute\b",
            r"\bsolve\b",

            r"\bevaluate\b",
            r"\bfind the value\b",
        ]

        # ----------------------------------------------------
        # Reasoning indicators
        # ----------------------------------------------------

        self.reasoning_patterns = [

            r"\bexplain\b",
            r"\bcompare\b",
            r"\banalyze\b",
            r"\banalyse\b",
            r"\bwhy\b",
            r"\bhow\b",
            r"\bshould\b",
            r"\bwhich is better\b",
            r"\bdifference\b",
            r"\bimpact\b",
            r"\beffect\b",
            r"\bmeaning\b",
            r"\bhow does\b",
            r"\bwhy does\b",
        ]

        # ----------------------------------------------------
        # Explicit requests for external information
        # ----------------------------------------------------

        self.explicit_web_patterns = [

            r"\bsearch the web\b",
            r"\bsearch online\b",
            r"\blook online\b",
            r"\blook it up\b",
            r"\blook this up\b",
            r"\bfind online\b",
            r"\bfrom the internet\b",
            r"\bon the internet\b",
            r"\baccording to the latest\b",

            r"\bsearch the internet\b",
            r"\bbrowse the web\b",
            r"\bbrowse online\b",
        ]

        # ----------------------------------------------------
        # Current-event entities
        # ----------------------------------------------------

        self.current_entity_patterns = [

            r"\bpresident\b",
            r"\bprime minister\b",
            r"\belection\b",
            r"\bgovernment\b",

            r"\bfifa\b",
            r"\bfootball\b",
            r"\bsoccer\b",
            r"\bcricket\b",
            r"\bnba\b",
            r"\bipl\b",

            r"\bstock\b",
            r"\bnvidia\b",
            r"\btesla\b",
            r"\bbitcoin\b",
            r"\bcrypto\b",

            r"\bubuntu\b",
            r"\bwindows\b",
            r"\bandroid\b",
            r"\bios\b",
        ]

    # ============================================================
    # Public API
    # ============================================================

    def decide(
        self,
        question,
    ):

        question = question.strip()

        if not question:

            return DecisionResult(
                Decision.LOCAL,
                "Empty question.",
                1.0,
            )

        text = question.lower()

        # ====================================================
        # 1. Capability questions
        # ====================================================
        #
        # These must happen BEFORE web detection.
        #
        # "Can you search the web?"
        # should NOT actually perform a search.
        #
        # It is asking about Atlas's capability.
        #

        if self._matches(
            text,
            self.capability_patterns,
        ):

            return DecisionResult(
                Decision.LOCAL,
                "User is asking about Atlas capabilities.",
                0.99,
            )

        # ====================================================
        # 2. Explicit web request
        # ====================================================

        if self._matches(
            text,
            self.explicit_web_patterns,
        ):

            return DecisionResult(
                Decision.WEB,
                "User explicitly requested external information.",
                0.99,
            )

        # ====================================================
        # 3. Current information
        # ====================================================

        is_current = self._matches(
            text,
            self.web_patterns,
        )

        has_reasoning = self._matches(
            text,
            self.reasoning_patterns,
        )

        # Current + reasoning = BOTH

        if is_current and has_reasoning:

            return DecisionResult(
                Decision.BOTH,
                "Question requires current information plus reasoning.",
                0.95,
            )

        # Pure current fact = WEB

        if is_current:

            return DecisionResult(
                Decision.WEB,
                "Question depends on current or changing information.",
                0.98,
            )

        # ====================================================
        # 4. New / recent technical knowledge
        # ====================================================

        if self._matches(
            text,
            self.both_patterns,
        ):

            return DecisionResult(
                Decision.BOTH,
                "Question may require current external knowledge plus local reasoning.",
                0.90,
            )

        # ====================================================
        # 5. Current-event entities
        # ====================================================

        if self._matches(
            text,
            self.current_entity_patterns,
        ):

            if has_reasoning:

                return DecisionResult(
                    Decision.BOTH,
                    "Question involves a potentially changing topic and requires reasoning.",
                    0.88,
                )

            return DecisionResult(
                Decision.WEB,
                "Question involves a topic whose information may change over time.",
                0.90,
            )

        # ====================================================
        # 6. Mathematical / computational questions
        # ====================================================

        if self._matches(
            text,
            self.calculation_patterns,
        ):

            return DecisionResult(
                Decision.LOCAL,
                "Question is computational and does not require current information.",
                0.98,
            )

        # ====================================================
        # 7. Established knowledge
        # ====================================================

        if self._matches(
            text,
            self.local_patterns,
        ):

            return DecisionResult(
                Decision.LOCAL,
                "Question concerns established knowledge suitable for local reasoning.",
                0.90,
            )

        # ====================================================
        # 8. Default
        # ====================================================

        return DecisionResult(
            Decision.LOCAL,
            "No indication that current external information is required.",
            0.70,
        )

    # ============================================================
    # Helper
    # ============================================================

    @staticmethod
    def _matches(
        text,
        patterns,
    ):

        return any(
            re.search(
                pattern,
                text,
            )
            for pattern in patterns
        )