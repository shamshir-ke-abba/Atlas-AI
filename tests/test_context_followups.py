from ai.context_builder import ContextBuilder


def make_msg(sender, text, is_user=False):
    return {"sender": sender, "text": text, "is_user": is_user}


def test_direct_followup_clarification():
    cb = ContextBuilder()
    history = [
        make_msg("User", "Tell me an interesting niche fact", True),
        make_msg("Atlas", "Did you know that honeybees can remember and navigate through multiple routes and even communicate via waggle dances."),
    ]
    prompt = cb.build(history, "I already know that")
    assert "FOLLOW-UP CLARIFICATION" in prompt
    assert "honeybees" in prompt.lower()


def test_pronoun_reference_resolves_to_last_assistant():
    cb = ContextBuilder()
    history = [
        make_msg("User", "Explain gravity", True),
        make_msg("Atlas", "Gravity is a force that attracts two bodies toward each other."),
    ]
    prompt = cb.build(history, "Explain that more simply")
    assert "Gravity is a force" in prompt


def test_second_item_resolution():
    cb = ContextBuilder()
    history = [
        make_msg("User", "Give me three examples", True),
        make_msg("Atlas", "1. Apples\n2. Bananas\n3. Cherries"),
    ]
    prompt = cb.build(history, "Explain the second one")
    assert "enumerated item #2" in prompt or "Bananas" in prompt


def test_topic_switch_no_clarification():
    cb = ContextBuilder()
    history = [
        make_msg("User", "Explain gravity", True),
        make_msg("Atlas", "Gravity explanation..."),
    ]
    prompt = cb.build(history, "What's the capital of Japan?")
    assert "FOLLOW-UP CLARIFICATION" not in prompt
