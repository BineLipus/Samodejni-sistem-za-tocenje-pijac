# This class represents an object (record) in a database table
from datetime import datetime

from VO.Glass import Glass
from VO.Keg import Keg


class Pour:
    def __init__(self, id: int, keg: Keg, glass: Glass, timestamp: datetime):
        self.id = id
        self.keg = keg
        self.glass = glass
        self.timestamp = timestamp

    def get_id(self) -> int:
        return self.id

    def get_keg(self) -> Keg:
        return self.keg

    def get_glass(self) -> Glass:
        return self.glass

    def get_timestamp(self) -> datetime:
        return self.timestamp

