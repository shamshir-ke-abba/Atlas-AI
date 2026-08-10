from ai.knowledge_decider import (
    KnowledgeDecider,
)


def main():

    decider = KnowledgeDecider()

    questions = [

        "What is 2 + 2?",

        "Explain Newton's second law.",

        "Solve this quadratic equation.",

        "What is the latest Ubuntu release?",

        "Who won yesterday's match?",

        "What is NVIDIA's current stock price?",

        "Explain a new physics discovery from 2026.",

        "How does Python recursion work?",

        "Why is the sky blue?",

    ]


    print()
    print("=" * 70)
    print("ATLAS KNOWLEDGE DECIDER TEST")
    print("=" * 70)


    for question in questions:

        result = decider.decide(
            question
        )

        print()
        print("QUESTION:")
        print(question)

        print(
            f"DECISION: {result.decision.value.upper()}"
        )

        print(
            f"CONFIDENCE: {result.confidence:.2f}"
        )

        print(
            f"REASON: {result.reason}"
        )


if __name__ == "__main__":
    main()