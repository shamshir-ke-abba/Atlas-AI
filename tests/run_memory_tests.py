import sys
from pathlib import Path

# Ensure repository root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_memory_manager import *

if __name__ == '__main__':
    print('Running test_memory_save_reload_update_forget...')
    test_memory_save_reload_update_forget()
    print('OK')

    print('Running test_extract_from_message_and_persistence...')
    test_extract_from_message_and_persistence()
    print('OK')

    print('Running test_explicit_remember_command_simulation...')
    test_explicit_remember_command_simulation()
    print('OK')
