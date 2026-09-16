"""Regression tests for chat horizontal layout and scroll bounds."""

from PySide6.QtWidgets import QApplication
from gui.widgets.chat import AtlasChat


def test_chat_horizontal_bounds_and_no_scroll():
    app = QApplication.instance() or QApplication([])

    chat = AtlasChat(bus=None)
    chat.resize(460, 600)
    chat.show()
    app.processEvents()

    # Initial state
    assert chat.scroll.horizontalScrollBar().maximum() == 0

    # 1. Short message
    chat.add_message("User", "Hello")
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()

    # 2. Long paragraph
    chat.add_message(
        "Atlas",
        "This is an extensive paragraph specifically formatted to verify that natural word wrapping "
        "occurs smoothly across the available viewport width without expanding the MessagesContainer "
        "or triggering horizontal scrollbar ranges.",
    )
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()

    # 3. 600-char unbroken token
    chat.add_message("Atlas", "LongToken: " + "W" * 600)
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()

    # 4. Code block with long line
    chat.add_message("Atlas", "```python\n" + "x = " + "9" * 400 + "\n```")
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()

    # 5. Simulated streaming chunks
    stream_msg = chat.add_message("Atlas", "")
    for chunk in ["Streaming ", "token ", "accumulation ", "over ", "time ", "with ", "code: ", "`inline_code_token`"]:
        stream_msg.set_text(stream_msg.text + chunk)
        app.processEvents()
        assert chat.scroll.horizontalScrollBar().maximum() == 0
        assert chat.messages.width() <= chat.scroll.viewport().width()

    # 6. Resize narrower (e.g. 320px)
    chat.resize(320, 600)
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()

    # 7. Resize wider (e.g. 950px)
    chat.resize(950, 700)
    app.processEvents()
    assert chat.scroll.horizontalScrollBar().maximum() == 0
    assert chat.messages.width() <= chat.scroll.viewport().width()
