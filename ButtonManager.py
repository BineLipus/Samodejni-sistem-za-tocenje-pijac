from GPIOManager import GPIOManager
from Logger import Log


class ButtonManager:
    BUTTON_A_GPIO_LED_PIN = 7
    BUTTON_A_GPIO_PIN = 11
    BUTTON_B_GPIO_LED_PIN = 13
    BUTTON_B_GPIO_PIN = 15

    beerTapMachineInstance = None
    error = False

    @staticmethod
    def initialize(beer_tap_machine_instance):
        ButtonManager.beerTapMachineInstance = beer_tap_machine_instance
        GPIOManager.setup(ButtonManager.BUTTON_A_GPIO_PIN, GPIOManager.IN, GPIOManager.PUD_UP)
        GPIOManager.setup(ButtonManager.BUTTON_A_GPIO_LED_PIN, GPIOManager.OUT)
        GPIOManager.setup(ButtonManager.BUTTON_B_GPIO_PIN, GPIOManager.IN, GPIOManager.PUD_UP)
        GPIOManager.setup(ButtonManager.BUTTON_B_GPIO_LED_PIN, GPIOManager.OUT)
        GPIOManager.add_event_detect(ButtonManager.BUTTON_A_GPIO_PIN, GPIOManager.FALLING,
                                     ButtonManager.select_valve_handler, 300)
        GPIOManager.add_event_detect(ButtonManager.BUTTON_B_GPIO_PIN, GPIOManager.FALLING,
                                     ButtonManager.select_valve_handler, 300)
        # Lighten up default (A) button
        GPIOManager.output(ButtonManager.BUTTON_A_GPIO_LED_PIN, GPIOManager.HIGH)
        GPIOManager.output(ButtonManager.BUTTON_B_GPIO_LED_PIN, GPIOManager.LOW)

    @staticmethod
    def select_valve_handler(pin_number):
        if not ButtonManager.beerTapMachineInstance.isPouring():
            if not ButtonManager.error:
                if pin_number == ButtonManager.BUTTON_A_GPIO_PIN:
                    if ButtonManager.beerTapMachineInstance.set_active_valve(ButtonManager.beerTapMachineInstance.VALVE_A_GPIO_PIN):
                        GPIOManager.output(ButtonManager.BUTTON_A_GPIO_LED_PIN, GPIOManager.HIGH)
                        GPIOManager.output(ButtonManager.BUTTON_B_GPIO_LED_PIN, GPIOManager.LOW)
                    else:
                        ButtonManager.error = True
                elif pin_number == ButtonManager.BUTTON_B_GPIO_PIN:
                    if ButtonManager.beerTapMachineInstance.set_active_valve(ButtonManager.beerTapMachineInstance.VALVE_B_GPIO_PIN):
                        GPIOManager.output(ButtonManager.BUTTON_B_GPIO_LED_PIN, GPIOManager.HIGH)
                        GPIOManager.output(ButtonManager.BUTTON_A_GPIO_LED_PIN, GPIOManager.LOW)
                    else:
                        ButtonManager.error = True
                Log.debug("Button %s pressed, valve %s is now active." % (
                    "A" if pin_number == ButtonManager.BUTTON_A_GPIO_PIN else "B", ButtonManager.beerTapMachineInstance.get_active_valve().get_title()))
            else:
                ButtonManager.error = False