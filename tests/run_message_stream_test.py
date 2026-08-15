from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys

from gui.widgets.message import AtlasMessage

app = QApplication.instance() or QApplication(sys.argv)

m = AtlasMessage('Atlas', '')

chunks = [
    "Gravity is a force.\n\n",
    "1. **JavaScript Interference**\n",
    "2. **CSS Conflicts**",
]

acc = ''
for c in chunks:
    acc += c
    m.set_text(acc)
    fmt = m.message_label.textFormat()
    text = m.message_label.text()
    assert fmt == Qt.RichText, f"Expected RichText, got {fmt}"
    # Ensure no escaped HTML entities remain
    assert '&lt;' not in text, f"Found escaped < in text: {text}"
    assert '&#' not in text, f"Found numeric entity in text: {text}"

print('Streaming text test passed')
