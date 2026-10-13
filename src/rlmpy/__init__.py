from importlib.metadata import PackageNotFoundError, version

from .rlmpy import rlmInfo

try:
    __version__ = version("rlmpy")
except PackageNotFoundError:
    try:
        from ._version import version as __version__
    except ImportError:
        __version__ = "0.0.0"

__all__ = ["rlmInfo", "__version__"]
