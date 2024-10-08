import ctypes

from pykinect_azure.k4a.capture import Capture
from pykinect_azure.k4a.imu_sample import ImuSample
from pykinect_azure.k4a.calibration import Calibration
from pykinect_azure.k4arecord.record import Record
from pykinect_azure.k4a._k4atypes import K4A_WAIT_INFINITE
from pykinect_azure.utils import get_k4a_module_path
from pykinect_azure.k4a._k4a import k4a_dll

class Device:

	def __init__(self, index=0, k4a_dll_obj=None):
		if k4a_dll_obj is None:
			self._k4a = k4a_dll()
			self._k4a.setup_library()
			# print(f"[Device] Initialized k4a library {self._k4a}")
		else:
			self._k4a = k4a_dll_obj

		self._handle = None
		self._handle = self.open(index)
		self.recording = False

		self.calibration = None
		self.capture = None
		self.imu_sample = None

	def __del__(self):
		self.close()

	def is_valid(self):
		return self._handle

	def is_capture_initialized(self):
		return self.capture

	def is_imu_sample_initialized(self):
		return self.imu_sample

	def handle(self):
		return self._handle

	def start(self, configuration, record=False, record_filepath="output.mkv"):
		self.configuration = configuration
		try:
			self.start_cameras(configuration)
			self.start_imu()
		except Exception as e:
			raise e

		if record:
			self.record = Record(self._handle, self.configuration.handle(), record_filepath)
			self.recording = True

	def close(self):
		if self.is_valid():
			self.stop_imu()
			self.stop_cameras()
			self._k4a.k4a_device_close(self._handle)

			# Clear members
			self._handle = None
			self.record = None
			self.recording = False

	def update(self, timeout_in_ms=K4A_WAIT_INFINITE):
		# Get cameras capture
		try:
			capture_handle = self.get_capture(timeout_in_ms)
		except Exception as e:
			raise e

		if self.is_capture_initialized():
			self.capture._handle = capture_handle
		else :
			self.capture = Capture(capture_handle, self.calibration, k4a_dll=self._k4a)
		
		# Write capture if recording
		if self.recording:
			self.record.write_capture(self.capture.handle())
			
		return self.capture

	def update_imu(self, timeout_in_ms=K4A_WAIT_INFINITE):
		
		# Get imu sample
		imu_sample = self.get_imu_sample(timeout_in_ms)

		if self.is_imu_sample_initialized():
			self.imu_sample._struct = imu_sample
			self.imu_sample.parse_data()
		else :
			self.imu_sample = ImuSample(imu_sample)
				
		return self.imu_sample

	def get_capture(self, timeout_in_ms=None):
		if timeout_in_ms is None:
			timeout_in_ms = self._k4a.K4A_WAIT_INFINITE

		# Release current handle
		if self.is_capture_initialized():
			self.capture.release_handle()

		capture_handle = self._k4a.k4a_capture_t()
		self._k4a.VERIFY(self._k4a.k4a_device_get_capture(self._handle, capture_handle, timeout_in_ms),"Get capture failed!")
			
		return capture_handle

	def get_imu_sample(self, timeout_in_ms=None):
		if timeout_in_ms is None:
			timeout_in_ms = self._k4a.K4A_WAIT_INFINITE

		imu_sample = self._k4a.k4a_imu_sample_t()

		self._k4a.VERIFY(self._k4a.k4a_device_get_imu_sample(self._handle,imu_sample,timeout_in_ms),"Get IMU failed!")

		return imu_sample

	def start_cameras(self, device_config):
		self.calibration = self.get_calibration(device_config.depth_mode, device_config.color_resolution)

		self._k4a.VERIFY(self._k4a.k4a_device_start_cameras(self._handle, device_config.handle()),"Start K4A cameras failed!")

	def stop_cameras(self):

		self._k4a.k4a_device_stop_cameras(self._handle)

	def start_imu(self):

		self._k4a.VERIFY(self._k4a.k4a_device_start_imu(self._handle),"Start K4A IMU failed!")

	def stop_imu(self):

		self._k4a.k4a_device_stop_imu(self._handle)

	def get_serialnum(self):

		serial_number_size = ctypes.c_size_t()
		result = self._k4a.k4a_device_get_serialnum(self._handle, None, serial_number_size)

		if result == self._k4a.K4A_BUFFER_RESULT_TOO_SMALL:
			serial_number = ctypes.create_string_buffer(serial_number_size.value)

		self._k4a.VERIFY(self._k4a.k4a_device_get_serialnum(self._handle,serial_number,serial_number_size),"Read serial number failed!")

		return serial_number.value.decode("utf-8") 

	def get_calibration(self, depth_mode, color_resolution):

		calibration_handle = self._k4a.k4a_calibration_t()

		self._k4a.VERIFY(self._k4a.k4a_device_get_calibration(self._handle,depth_mode,color_resolution,calibration_handle),"Get calibration failed!")
		
		return Calibration(calibration_handle, k4a_dll=self._k4a)

	def get_version(self):

		version = self._k4a.k4a_hardware_version_t()

		self._k4a.VERIFY(self._k4a.k4a_device_get_version(self._handle,version),"Get version failed!")

		return version

	def open(self, index=0):
		device_handle = self._k4a.k4a_device_t()

		self._k4a.VERIFY(self._k4a.k4a_device_open(index, device_handle),"Open K4A Device failed!")

		return device_handle

	def device_get_installed_count(self):
		return int(self._k4a.k4a_device_get_installed_count())
	
	def is_sync_in_connected(self):
		sync_in_bool = ctypes.c_bool()
		sync_out_bool = ctypes.c_bool()

		self._k4a.VERIFY(self._k4a.k4a_device_get_sync_jack(self._handle, sync_in_bool, sync_out_bool), "Sync connection check failed!")

		return sync_in_bool.value
	
	def is_sync_out_connected(self):
		sync_in_bool = ctypes.c_bool()
		sync_out_bool = ctypes.c_bool()

		self._k4a.VERIFY(self._k4a.k4a_device_get_sync_jack(self._handle, sync_in_bool, sync_out_bool), "Sync connection check failed!")
		return sync_out_bool.value

