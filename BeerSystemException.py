from decimal import Decimal
from enum import Enum
from Logger import Log


class BeerSystemException(Exception):
    """Beer System exception class"""

    def __init__(self, error_code, log_argument=None, message=None):
        super().__init__(message)
        self.error_code = error_code
        if log_argument is not None:
            Log.error(self.error_code.get_log_message() % log_argument)
        else:
            Log.error(self.error_code.get_log_message())
        self.success_rate = None
        self.beer = None
        self.glass = None
        self.keg = None
        self.pour = None

    def get_error_code(self):
        return self.error_code

    def set_success_rate(self, success_rate: Decimal):
        self.success_rate = Decimal(success_rate)
        return self

    def get_success_rate(self):
        return self.success_rate

    def set_beer(self, beer):
        self.beer = beer
        return self

    def get_beer(self):
        return self.beer

    def set_keg(self, keg):
        self.keg = keg
        return self

    def get_keg(self):
        return self.keg

    def set_glass(self, glass):
        self.glass = glass
        return self

    def get_glass(self):
        return self.glass

    def set_pour(self, pour):
        self.pour = pour
        return self

    def get_pour(self):
        return self.pour

    def set_all(self, glass, keg, beer, pour):
        self.set_glass(glass)
        self.set_keg(keg)
        self.set_beer(beer)
        self.set_pour(pour)
        return self

    class ErrorCode(Enum):
        GENERAL_ERROR = ("GENERAL_ERROR", "General Error")
        NETWORK_PROBLEM = ("NETWORK_PROBLEM", "Network is not reachable, please ensure a wired network connection.")
        DATABASE_CONNECTION_PROBLEM = ("DATABASE_CONNECTION_PROBLEM", "There is a database connection problem. Please ensure that local network has access to the internet.")
        GLASS_REMOVED_PREMATURELY = ("GLASS_REMOVED_PREMATURELY", "Glass removed prematurely")
        INSUFFICIENT_BALANCE = ("INSUFFICIENT_BALANCE", "Glass with id %s has insufficient balance.")
        GLASS_NOT_RECOGNIZED = ("GLASS_NOT_RECOGNIZED", "Glass with id %d not recognized in the database")
        KEG_EMPTY = ("KEG_EMPTY", "Keg with id %s has insufficient contents to pour a whole glass.")
        TAP_NOT_CONNECTED = ("TAP_NOT_CONNECTED", "Tap %s Not Connected.")
        # This functionality could be supported with tube splitters, but no need for it on a low scale
        MULTIPLE_TAPS_CONNECTED = ("MULTIPLE_TAPS_CONNECTED", "Multiple Taps Connected To The Same Keg")

        def __init__(self, error_code, log_message):
            self.error_code = error_code
            self.log_message = log_message

        def get_error_code_name(self):
            return self.error_code

        def get_log_message(self):
            return self.log_message
