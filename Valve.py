import time
from datetime import datetime
from decimal import Decimal

from GPIOManager import GPIOManager
from Logger import Log
from VO.Keg import Keg
from VO.Pour import Pour


class Valve:
    flow_correction_coefficient = 4
    flow_correction_coefficient_per_bar = Decimal(0.20)

    def __init__(self, gpio_pin, title, pressure=0.75):
        # initialize the pin
        self.gpio_pin = gpio_pin
        self.title = title
        self.pressure = pressure  # Pressure in bars at the tap
        GPIOManager.setup(self.gpio_pin, GPIOManager.OUT)
        self.close()
        self.last_open_timestamp = None
        self.last_close_timestamp = None
        self.keg = None

    def pour(self, pour: Pour):
        self.open_for(Valve.calculate_open_time(pour.get_glass().get_volume(), pour.get_keg().get_pressure()))

    def open_for(self, milliseconds):
        Log.info("Opening valve %s for %d milliseconds" % (self.title, milliseconds))
        self._open()
        time.sleep(milliseconds / 1000)  # Convert to a fraction of a second
        self.close()

    def _open(self):
        Log.debug_detailed("Opening valve associated with GPIO pin %d" % self.gpio_pin)
        GPIOManager.output(self.gpio_pin, GPIOManager.HIGH)
        self.last_open_timestamp = datetime.now()

    def close(self):
        Log.debug_detailed("Closing valve associated with GPIO pin %d" % self.gpio_pin)
        GPIOManager.output(self.gpio_pin, GPIOManager.LOW)
        self.last_close_timestamp = datetime.now()

    def get_title(self):
        return self.title

    def get_gpio_pin(self):
        return self.gpio_pin

    def get_id(self):
        return self.get_gpio_pin()

    def get_last_pour_time(self):
        if self.last_open_timestamp is not None and self.last_close_timestamp is not None:
            Log.debug_detailed("Time difference %dms" % ((self.last_close_timestamp - self.last_open_timestamp).total_seconds() * 1000))
            return (self.last_close_timestamp - self.last_open_timestamp).total_seconds() * 1000  # return actual milliseconds of last pour

    @staticmethod
    def calculate_open_time(glass_volume: Decimal, keg_pressure: Decimal):
        return int(((glass_volume / keg_pressure) * Valve.flow_correction_coefficient * 1000) * (1 + keg_pressure * Valve.flow_correction_coefficient_per_bar))  # return milliseconds

    def set_keg(self, keg: Keg):
        self.keg = keg

    def get_keg(self) -> Keg:
        return self.keg
