from mfrc522 import SimpleMFRC522
from Logger import Log
from threading import Thread
import time


class RFIDReader:
    reader = None

    def __init__(self):
        RFIDReader.reader = SimpleMFRC522()
        self.thread = None
        self.id = None

    def read_tag_id(self):
        self.id = None
        Log.debug_extra_detailed("Waiting for RFID tag to be read.")
        self.id, text = self.reader.read()
        Log.debug_extra_detailed("RFID Tag with ID %d read." % self.id)
        return self.id

    def read_tag_id_non_blocking(self, timeout: float):
        if self.thread is None or not self.thread.is_alive():
            Log.debug_extra_detailed("Starting new RFID thread")
            # If thread is not running, start it. It is running, and it hasn't finished execution, use already
            # running one
            self.thread = Thread(target=self.read_tag_id, daemon=True)
            self.thread.start()
        else:
            Log.debug_extra_detailed("Reusing RFID thread")
        self.thread.join(timeout)
        if self.id is not None and timeout is None:
            Log.info("RFID Tag with ID %d read." % self.id)
        return self.id

    def _wait_for_tag_to_be_removed_(self):
        while self.read_tag_id_non_blocking(0.1) is not None:
            time.sleep(1)  # Wait for glass to be removed

    def wait_for_user_to_remove_glass(self):
        thread = Thread(target=self._wait_for_tag_to_be_removed_, daemon=True, args=())
        thread.start()
        Log.debug("Waiting for user to remove the glass.")
        thread.join()
