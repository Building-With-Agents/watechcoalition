import inspect
from pathlib import Path
from types import FrameType
from typing import cast


def get_file_dirname() -> Path:
    """Returns the callee (`__file__`) directory name"""
    frame = cast(FrameType, inspect.currentframe()).f_back
    module = inspect.getmodule(frame)
    assert module
    assert module.__file__
    return Path(module.__file__).parent.absolute()
