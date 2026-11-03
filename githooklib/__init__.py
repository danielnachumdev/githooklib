from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from .git_hook import *
from .context import *
from .command import *
from .logger import *
from .version import is_version_compatible, MINIMUM_COMPATIBLE_VERSION

try:
    __version__ = package_version("githooklib")
except PackageNotFoundError:
    __version__ = "0.0.0"
