from .singleton import *

try:
    from .google_fire_mock_get_result_function import *
    from .command_result_factory import *
except ImportError:
    pass
