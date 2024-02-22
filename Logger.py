from enum import Enum


class Log:
    minimum_severity_rating = 0  # -2 - Everything will be printed, 3 - Only Errors will be printed out

    @staticmethod
    def set_minimum_severity_rating(minimum_severity_rating):
        Log.minimum_severity_rating = minimum_severity_rating.get_number_value()

    @staticmethod
    def __log__(severity, message):
        if Log.minimum_severity_rating <= severity.get_number_value():
            print(severity.get_string_value(), message)

    @staticmethod
    def debug(message):
        Log.__log__(Log.SeverityRating.DEBUG, message)

    @staticmethod
    def debug_detailed(message):
        Log.__log__(Log.SeverityRating.DEBUG_DETAILED, message)

    @staticmethod
    def debug_extra_detailed(message):
        Log.__log__(Log.SeverityRating.DEBUG_EXTRA_DETAILED, message)

    @staticmethod
    def info(message):
        Log.__log__(Log.SeverityRating.INFO, message)

    @staticmethod
    def warn(message):
        Log.__log__(Log.SeverityRating.WARNING, message)

    @staticmethod
    def error(message):
        Log.__log__(Log.SeverityRating.ERROR, message)

    class SeverityRating(Enum):
        DEBUG_EXTRA_DETAILED = ("\033[96mDEBUG EXTRA DETAILED:\033[0m", -2)
        DEBUG_DETAILED = ("\033[95mDEBUG DETAILED:\033[0m", -1)
        DEBUG = ("\033[94mDEBUG:\033[0m", 0)
        INFO = ("\033[92mINFO:\033[0m", 1)
        WARNING = ("\033[93mWARNING:\033[0m", 2)
        ERROR = ("\033[91mERROR:\033[0m", 3)

        def __init__(self, string_value, number_value):
            self.string_value = string_value
            self.number_value = number_value

        def get_number_value(self):
            return self.number_value

        def get_string_value(self):
            return self.string_value

        @staticmethod
        def get_by_name(name: str):
            rating = Log.SeverityRating.__getitem__(name)
            if rating is None:
                raise Exception("Log rating %s doesn't exist." % name)
            return rating
