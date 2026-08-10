from ai.brain import AtlasBrain

brain = AtlasBrain()

tests = [
    "What is 2 + 2?",
    "Explain Newton's second law.",
    "What is the latest Ubuntu release?",
    "Who won yesterday's match?",
    "How does Python recursion work?",
    "Explain a new physics discovery from 2026.",
]

for question in tests:

    result = brain.knowledge_decider.decide(
        question
    )

    print()
    print("QUESTION:", question)
    print("DECISION:", result.decision.value)
    print("CONFIDENCE:", result.confidence)
    print("REASON:", result.reason)
