import RPi.GPIO as GPIO


class GPIOManager:
    # static constants from GPIO to avoid having multiple imports for the same thing and unwanted GPIO accesses
    IN = GPIO.IN
    OUT = GPIO.OUT
    FALLING = GPIO.FALLING
    RISING = GPIO.RISING
    BOARD = GPIO.BOARD
    BCM = GPIO.BCM
    LOW = GPIO.LOW
    HIGH = GPIO.HIGH
    PUD_UP = GPIO.PUD_UP
    PUD_DOWN = GPIO.PUD_DOWN

    @staticmethod
    def initialize(mode=GPIO.BOARD, warnings_enabled=False):
        GPIOManager.mode = mode
        GPIOManager.warnings_enabled = warnings_enabled
        GPIO.setwarnings(GPIOManager.warnings_enabled)
        GPIO.cleanup()
        GPIO.setmode(GPIOManager.mode)

    @staticmethod
    def setup(pin, direction, resistance=None):
        if resistance is not None:
            GPIO.setup(pin, direction, resistance)
        else:
            GPIO.setup(pin, direction)

    @staticmethod
    def add_event_detect(pin, edge, callback_function, bouncetime):
        GPIO.add_event_detect(pin, edge, callback_function, bouncetime)

    @staticmethod
    def cleanup():
        GPIO.cleanup()

    @staticmethod
    def output(pin, state):
        GPIO.output(pin, state)
