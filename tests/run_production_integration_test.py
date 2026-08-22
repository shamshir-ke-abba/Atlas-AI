from ai.brain import AtlasBrain


class CapturingModel:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt, stream=True):
        # Capture the prompt provided by the brain/context builder
        self.last_prompt = prompt
        # yield a dummy response
        if stream:
            yield "Here is a fact."
        else:
            return "Here is a fact."

    def cancel_current(self):
        pass


def run_test():
    model = CapturingModel()
    brain = AtlasBrain(model=model, memory=None)

    # Simulate a previous assistant message in conversation history
    history = [
        {"sender": "User", "text": "Tell me a niche fact", "is_user": True},
        {"sender": "Atlas", "text": "Did you know that honeybees can remember and navigate through multiple routes and even communicate via waggle dances.", "is_user": False},
    ]

    # Now send a short follow-up that should trigger clarification
    resp = brain.process_message("I already know that", conversation_history=history)

    assert model.last_prompt is not None, "Model did not receive a prompt"
    assert "FOLLOW-UP CLARIFICATION" in model.last_prompt or "honeybees" in model.last_prompt.lower(), "Clarification not injected into prompt"

    print('Follow-up clarification included in prompt:')
    print(model.last_prompt)

    # Test pronoun resolution for 'Explain that more simply'
    history2 = [
        {"sender": "User", "text": "Explain gravity", "is_user": True},
        {"sender": "Atlas", "text": "Gravity is a force that attracts two bodies toward each other.", "is_user": False},
    ]
    model.last_prompt = None
    resp2 = brain.process_message("Explain that more simply", conversation_history=history2)
    assert model.last_prompt is not None
    assert "Gravity is a force" in model.last_prompt, "Pronoun resolution failed"

    print('Pronoun resolution passes')

    # Test topic switch: no clarification should be injected
    history3 = [
        {"sender": "User", "text": "Explain gravity", "is_user": True},
        {"sender": "Atlas", "text": "Gravity explanation...", "is_user": False},
    ]
    model.last_prompt = None
    resp3 = brain.process_message("What's the capital of Japan?", conversation_history=history3)
    assert model.last_prompt is not None
    assert "FOLLOW-UP CLARIFICATION" not in model.last_prompt, "Unwanted clarification injected"

    print('Topic switch isolation passes')


if __name__ == '__main__':
    run_test()
    print('Production integration checks passed')
