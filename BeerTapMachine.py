import os
import time
import traceback
from datetime import datetime
from decimal import Decimal
from threading import Thread
from urllib import request
from urllib.error import URLError

from mysql.connector import DatabaseError

import Drawer
from GPIOManager import GPIOManager
from DisplayManager import DisplayManager
from DatabaseRepository import DatabaseRepository
from LanguageManager import LanguageManager
from RFIDReader import RFIDReader
from Valve import Valve
from Logger import Log
import signal  # for GPIO cleanup
import sys  # for GPIO cleanup
import argparse  # For command-line arguments
from subprocess import check_output
import os
import signal

from ButtonManager import ButtonManager
from BeerSystemException import BeerSystemException
from VO.Pour import Pour

GPIOManager.initialize()


def signal_handler(sig, frame):
    Log.warn("Signal %s received, cleaning the GPIO and exiting the application" % sig)
    GPIOManager.cleanup()
    DisplayManager.terminate()
    Log.warn("Cleanup completed.")
    pids = map(int, check_output(["pidof", "python3"]).split())
    for pid in pids:
        os.kill(pid, signal.SIGTERM)  # or signal.SIGKILL
    sys.exit(0)


class BeerTapMachine:
    database_repository = None
    rfid_reader = None
    button_manager = None
    currently_pouring: bool = False  # Used for disabling button input while pouring.

    VALVE_A_GPIO_PIN = 31
    VALVE_B_GPIO_PIN = 33

    valves = {
        VALVE_A_GPIO_PIN: Valve(VALVE_A_GPIO_PIN, "Valve A"),
        VALVE_B_GPIO_PIN: Valve(VALVE_B_GPIO_PIN, "Valve B")
    }
    activeValve = valves.get(VALVE_A_GPIO_PIN)

    def __init__(self, args=None):
        self.initialize_system(args)
        self.main()

    def set_active_valve(self, active_valve_pin_number) -> bool:
        success = True
        oldValve = self.activeValve
        self.activeValve = self.get_valve(active_valve_pin_number)
        beer = None
        if self.activeValve.get_keg() is None and self.database_repository is not None:
            try:
                self.activeValve.set_keg(self.database_repository.resolve_keg_and_beer_by_tap(self.activeValve))
            except BeerSystemException as e:
                self.activeValve = oldValve
                self.handle_exception(e)
                #DisplayManager.showPromptFrame()
                success = False
        if self.activeValve.get_keg() is not None:
            beer = self.activeValve.get_keg().get_beer()
        if beer is not None:
            DisplayManager.setDisplayDataValue("beer", beer)
            DisplayManager.showSelectedBeerFrame()
            thread = Thread(target=DisplayManager.switchBackToPromptFrame, daemon=True, args=())
            thread.start()
        return success

    def get_valve(self, pin_number):
        return self.valves.get(pin_number)

    def get_active_valve(self):
        return self.activeValve

    def wait_for_user_to_remove_the_glass(self):
        while self.rfid_reader.read_tag_id_non_blocking(0.5) is not None:
            time.sleep(0.1)

    def isPouring(self) -> bool:
        return BeerTapMachine.currently_pouring

    def main(self):
        while True:
            try:
                # Get glass ID and valve ID (Pin)
                self.wait_for_user_to_remove_the_glass()
                BeerTapMachine.currently_pouring = False
                DisplayManager.clearDisplayDataValue("remaining_balance_label")
                DisplayManager.showPromptFrame()
                Log.info("Please select a beer and bring a glass in front of the tap to begin pouring.")
                glass_id = self.rfid_reader.read_tag_id_non_blocking(None)
                BeerTapMachine.currently_pouring = True
                glass = self.database_repository.resolve_glass_by_rfid(glass_id)
                keg = self.database_repository.resolve_keg_and_beer_by_tap(self.activeValve)
                self.database_repository.start_transaction()

                DisplayManager.setDisplayDataValue("remaining_balance_label", glass.get_balance_string())

                if glass.get_volume() <= keg.get_remaining_content():
                    pour_price = keg.get_beer().get_price_per_liter() * glass.get_volume()
                    if glass.get_balance() >= pour_price:

                        # pour using valve opening
                        pour = Pour(0, keg, glass, datetime.now())
                        self.handle_transaction(pour)

                        DisplayManager.showPouringFrame()
                        thread = Thread(target=self.activeValve.pour, daemon=True, args=(pour,))
                        thread.start()
                        try:
                            while thread.is_alive():
                                if self.rfid_reader.read_tag_id_non_blocking(0.5) is None:
                                    # glass is removed
                                    self.activeValve.close()
                                    success_rate = self.activeValve.get_last_pour_time() / Valve.calculate_open_time(
                                        glass.get_volume(), keg.get_pressure())
                                    Log.debug("Success rate: %f" % success_rate)
                                    # Don't wait for thread, it will finish  anyway as we already closed the valve.
                                    raise BeerSystemException(BeerSystemException.ErrorCode.GLASS_REMOVED_PREMATURELY) \
                                        .set_success_rate(success_rate) \
                                        .set_all(glass, keg, keg.beer, pour)
                            thread.join()
                        except BeerSystemException as e:
                            if e.get_error_code() == BeerSystemException.ErrorCode.GLASS_REMOVED_PREMATURELY:
                                Log.debug("Glass removed prematurely. Only charging for success rate %f" % success_rate)
                                e.set_pour(pour)
                                self.database_repository.rollback_transaction()
                                self.database_repository.start_transaction()
                                self.handle_transaction(pour, e.get_success_rate())
                                self.handle_exception(e)
                            else:
                                raise e  # Pass exception to outer except block, which will handle it
                    else:
                        raise BeerSystemException(BeerSystemException.ErrorCode.INSUFFICIENT_BALANCE, glass.get_id()) \
                            .set_glass(glass) \
                            .set_keg(keg) \
                            .set_beer(keg.get_beer())
                else:
                    raise BeerSystemException(BeerSystemException.ErrorCode.KEG_EMPTY, keg.get_id()) \
                        .set_glass(glass) \
                        .set_keg(keg) \
                        .set_beer(keg.get_beer())

                self.database_repository.commit_transaction()
                Log.info("Glass successfully poured, please remove it from the tap.")
                if DisplayManager.active_frame != DisplayManager.frame_error:
                    # Don't switch to pouring finished if glass is removed prematurely
                    DisplayManager.setDisplayDataValue("remaining_balance_label", glass.get_balance_string())
                    DisplayManager.showPouringFinishedFrame()
            except Exception as e:
                self.database_repository.rollback_transaction()
                if not isinstance(e, BeerSystemException):
                    Log.error("General exception was raised.")
                    print(e)
                    traceback.print_exception(*sys.exc_info())  # Prints stack trace
                    e = BeerSystemException(BeerSystemException.ErrorCode.GENERAL_ERROR, "General exception occurred.")
                self.handle_exception(e)

    def handle_transaction(self, pour: Pour, success_rate: Decimal = None):
        if success_rate is None:
            success_rate = Decimal(1)
        else:
            pour.get_glass().void_last_transaction()
            pour.get_keg().void_last_transaction()
        keg = pour.get_keg()
        glass = pour.get_glass()
        pour_price = Decimal(round(keg.get_beer().get_price_per_liter() * glass.get_volume() * success_rate, 2))
        volume_poured = Decimal(round(glass.get_volume() * success_rate, 2))
        # deduct the balance and update it in DB
        glass.deduct_balance(pour_price)
        self.database_repository.update_glass_balance(glass)
        # adjust remaining contents and update it in DB
        keg.deduct_remaining_content(volume_poured)
        self.database_repository.update_keg_remaining_content(keg)
        # Insert pour in DB
        self.database_repository.insert_pour(pour)

    @staticmethod
    def handle_exception(beer_system_exception: BeerSystemException) -> None:
        text = LanguageManager.get_text("error." + BeerSystemException.ErrorCode.GENERAL_ERROR.get_error_code_name())

        if LanguageManager.get_text(
                "error." + beer_system_exception.get_error_code().get_error_code_name()) is not None:
            text = LanguageManager.get_text("error." + beer_system_exception.get_error_code().get_error_code_name())

        DisplayManager.setDisplayDataValue("error_label", text)

        if beer_system_exception.get_pour() is not None:
            DisplayManager.setDisplayDataValue("remaining_balance_label",
                                               beer_system_exception.get_pour().get_glass()
                                               .get_balance_string())
        elif beer_system_exception.get_glass() is not None:
            DisplayManager.setDisplayDataValue("remaining_balance_label",
                                               beer_system_exception.get_glass()
                                               .get_balance_string())
        else:
            DisplayManager.setDisplayDataValue("remaining_balance_label", None)

        DisplayManager.showErrorFrame()

        if beer_system_exception.get_error_code() == BeerSystemException.ErrorCode.GLASS_REMOVED_PREMATURELY or \
                beer_system_exception.get_error_code() == BeerSystemException.ErrorCode.GENERAL_ERROR or \
                beer_system_exception.get_error_code() == BeerSystemException.ErrorCode.TAP_NOT_CONNECTED:
            time.sleep(8)  # Glass removed prematurely error needs to be shown for a static amount of time,
            # as this cannot hide when glass is removed (it was already removed)

    def initialize_system(self, args=None):
        # Setup signal handler for interruptions
        signal.signal(signal.SIGINT, signal_handler)
        try:
            # Set which logs will be displayed
            Log.set_minimum_severity_rating(Log.SeverityRating.get_by_name(args.log_rating))
            # Setup Display Manager
            DisplayManager.initialize(args.language)
            # Reset GPIO if it was used before and setup buttons and interrupt handlers for buttons
            self.button_manager = ButtonManager.initialize(self)
            # Setup RFID reader
            self.rfid_reader = RFIDReader()
            # Check connection to the internet
            while not BeerTapMachine.__is_connected_to_internet__():
                Log.warn("Not connected to the internet. Waiting for connection.")
                time.sleep(1)
            # Setup Database Repository
            self.database_repository = DatabaseRepository()

            # Load beer information for connected kegs
            try:
                if self.database_repository is not None:
                    for valve in self.valves.values():
                        valve.set_keg(self.database_repository.resolve_keg_and_beer_by_tap(valve))
                        Drawer.color_beer_image(
                            int(valve.get_keg().get_beer().get_ebc()))  # This will cache all the pictures for later use
            except BeerSystemException as e:
                Log.warn("Tap not connected, continuing.")
            Log.info("System initialized")
        except Exception as e:
            if isinstance(e, DatabaseError):
                Log.error("Couldn't connect to mysql database. Error number: %s." % e.errno)
            else:
                Log.error("General exception in initialization.")
                traceback.print_exception(*sys.exc_info())  # Prints stack trace
            time.sleep(5)
            signal_handler(1, 0)  # End execution by cleaning setup GPIO

    @staticmethod
    def __is_connected_to_internet__() -> bool:
        try:
            request.urlopen('http://google.com', timeout=3)
            return True
        except URLError as err:
            return False


if __name__ == '__main__':
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Lets pour some beer!")

    # Add arguments
    parser.add_argument('--log_rating', type=str,
                        help='Minimum log rating that is displayed. [DEBUG, INFO, WARNING, ERROR]', default="INFO")
    parser.add_argument('--language', type=str,
                        help='Language of GUI, according to two-letter ISO639-1 standard. [en, sl]', default="en")

    # Parse the arguments
    args = parser.parse_args()

    beerTapMachine = BeerTapMachine(args)
    beerTapMachine.main()
