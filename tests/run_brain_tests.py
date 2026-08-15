import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_brain_memory import *

if __name__ == '__main__':
    test_brain_remember_recall_forget_stream_and_restart()
    print('OK')
