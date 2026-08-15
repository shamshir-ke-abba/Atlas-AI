import sys
from pathlib import Path
import tempfile
import subprocess
import os

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Some test environments don't have PySide6 installed. Create a small shim
# so `from PySide6.QtCore import QObject, Signal, Slot` works when importing
# production modules during tests.
def _inject_pyside_shim():
    import types
    if 'PySide6' in sys.modules:
        return
    qtcore = types.ModuleType('PySide6.QtCore')

    class Signal:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self, *a, **k):
            pass

        def emit(self, *a, **k):
            pass

    def Slot(*args, **kwargs):
        def _decor(f):
            return f
        return _decor

    class QObject:
        pass

    qtcore.Signal = Signal
    qtcore.Slot = Slot
    qtcore.QObject = QObject

    pyside = types.ModuleType('PySide6')
    pyside.QtCore = qtcore

    sys.modules['PySide6'] = pyside
    sys.modules['PySide6.QtCore'] = qtcore


_inject_pyside_shim()

import core.memory as core_memory
from core.workers import AIWorker


def make_temp_memory_file():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    return Path(tmp.name)


def run_subprocess_save(tmp_path):
    # Create a small script that uses production path to save memory
    # Include a small PySide6 shim for subprocess too
    script = f"""
import sys
from pathlib import Path
import types
ROOT = Path('{ROOT.as_posix()}')
sys.path.insert(0, str(ROOT))

def _inject_pyside_shim():
    if 'PySide6' in sys.modules:
        return
    qtcore = types.ModuleType('PySide6.QtCore')
    class Signal:
        def __init__(self, *a, **k): pass
        def connect(self, *a, **k): pass
        def emit(self, *a, **k): pass
    def Slot(*a, **k):
        def _decor(f): return f
        return _decor
    class QObject: pass
    qtcore.Signal = Signal
    qtcore.Slot = Slot
    qtcore.QObject = QObject
    pyside = types.ModuleType('PySide6')
    pyside.QtCore = qtcore
    sys.modules['PySide6'] = pyside
    sys.modules['PySide6.QtCore'] = qtcore

_inject_pyside_shim()

import core.memory as core_memory
from core.workers import AIWorker
core_memory.MEMORY_FILE = Path('{tmp_path.as_posix()}')

w = AIWorker()
print(w.brain.process_message('My name is Saad'))
print('SAVED:', w.brain.memory.recall('identity','name'))
"""
    p = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def run_subprocess_recall(tmp_path):
    script = f"""
import sys
from pathlib import Path
import types
ROOT = Path('{ROOT.as_posix()}')
sys.path.insert(0, str(ROOT))

def _inject_pyside_shim():
    if 'PySide6' in sys.modules:
        return
    qtcore = types.ModuleType('PySide6.QtCore')
    class Signal:
        def __init__(self, *a, **k): pass
        def connect(self, *a, **k): pass
        def emit(self, *a, **k): pass
    def Slot(*a, **k):
        def _decor(f): return f
        return _decor
    class QObject: pass
    qtcore.Signal = Signal
    qtcore.Slot = Slot
    qtcore.QObject = QObject
    pyside = types.ModuleType('PySide6')
    pyside.QtCore = qtcore
    sys.modules['PySide6'] = pyside
    sys.modules['PySide6.QtCore'] = qtcore

_inject_pyside_shim()

import core.memory as core_memory
from core.workers import AIWorker
core_memory.MEMORY_FILE = Path('{tmp_path.as_posix()}')

w = AIWorker()
print('RECALL RESP:', w.brain.process_message('What is my name?'))
print('LOADED:', w.brain.memory.recall('identity','name'))
"""
    p = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_production_worker_path_and_restart():
    tmp = make_temp_memory_file()

    # Ensure no accidental use of real memory
    core_memory.MEMORY_FILE = tmp

    # Instantiate a production worker (which creates AtlasBrain internally)
    w = AIWorker()

    # Use the worker's brain (production-created) to remember name
    resp = w.brain.process_message('My name is Saad')
    assert w.brain.memory.recall('identity', 'name') == 'Saad'

    # Simulate restart by running a subprocess that uses the same production path
    rc, out, err = run_subprocess_recall(tmp)
    assert rc == 0, f"Subprocess failed: {err}"
    assert 'Saad' in out

    # Test streaming path: remember favorite color via stream
    gen = w.brain.stream_message('Remember that my favorite color is blue')
    list(gen)  # exhaust generator
    assert w.brain.memory.recall('preferences', 'favorite_color') == 'blue'

    # Now forget via production brain path
    fr = w.brain.process_message('Forget my favorite color')
    assert w.brain.memory.recall('preferences', 'favorite_color') is None

    # Cross-conversation persistence: create a new worker/brain
    w2 = AIWorker()
    resp2 = w2.brain.process_message('What is my name?')
    assert 'Saad' in resp2

    # Cleanup tmp file
    try:
        tmp.unlink()
    except Exception:
        pass


if __name__ == '__main__':
    test_production_worker_path_and_restart()
    print('Production path tests passed')
