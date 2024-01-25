import ctypes
import inspect, importlib

from pykinect_azure.k4a._k4a import k4a_dll
from pykinect_azure.k4a import Device, Configuration, default_configuration
from pykinect_azure.k4abt import _k4abt, Tracker
from pykinect_azure.k4arecord import _k4arecord
from pykinect_azure.k4arecord.playback import Playback
from pykinect_azure.utils import get_k4a_module_path, get_k4abt_module_path, get_k4arecord_module_path

class pykinectclass:

    def __init__(self):
        # set constants as attributes
        for name, cls in inspect.getmembers(importlib.import_module('pykinect_azure.k4a._k4atypes')):
            if inspect.isclass(cls) or name.isupper():
                setattr(self, name, cls)

        self.default_configuration = Configuration()

    def initialize_libraries(self, module_k4a_path=None, module_k4abt_path=None, track_body=False):
        
        # Search the module path for k4a if not available
        if module_k4a_path is None:
            module_k4a_path = get_k4a_module_path()

        module_k4arecord_path = get_k4arecord_module_path(module_k4a_path)

        # Initialize k4a related wrappers
        dll =self.init_k4a(module_k4a_path)

        # Initialize k4arecord related wrappers
        self.init_k4arecord(module_k4arecord_path)

        if track_body:
            # Search the module path for k4abt if not available
            if module_k4abt_path is None:
                module_k4abt_path = get_k4abt_module_path()

            # Initialize k4abt related wrappers
            self.init_k4abt(module_k4abt_path)

        return dll

    def init_k4a(self, module_k4a_path):
        self._k4a = k4a_dll()
        self._k4a.setup_library(module_k4a_path)
        print(f"initialized k4a {self._k4a}")

        return self._k4a

    def init_k4abt(self, module_k4abt_path):

        _k4abt.setup_library(module_k4abt_path)

    def init_k4arecord(self, module_k4arecord_path):

        _k4arecord.setup_library(module_k4arecord_path)

    def start_device(self, device_index=0, config=default_configuration, record=False, record_filepath="output.mkv"):
        if not hasattr(self, '_k4a'):
            self.initialize_libraries()
        
        # Create device object
        device = Device(device_index, k4a_dll_obj=self._k4a)

        # Start device
        device.start(config, record, record_filepath)

        return device

    def start_body_tracker(self, model_type=_k4abt.K4ABT_DEFAULT_MODEL, calibration=None):
        if calibration:
            return Tracker(calibration, model_type)
        else:
            return Tracker(Device.calibration, model_type)

    def start_playback(self, filepath):

        return Playback(filepath)


