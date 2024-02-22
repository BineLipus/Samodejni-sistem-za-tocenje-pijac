# This class represents an object (record) in a database table
from decimal import Decimal

from BeerSystemException import BeerSystemException
from VO.Beer import Beer


class Keg:
    def __init__(self, id: int, volume: int, valve_id: int, beer: Beer, pressure: Decimal, remaining_content: Decimal):
        self.id = id
        self.volume = volume  # Volume specified in liters
        self.valve_id = valve_id
        self.beer = beer
        self.pressure = pressure
        self.remaining_content = remaining_content  # Volume specified in liters (two decimals)
        self.last_remaining_content_deduction = None

    def get_id(self) -> int:
        return self.id

    def get_volume(self) -> int:
        return self.volume

    def get_valve_id(self) -> int:
        return self.valve_id

    def get_beer(self) -> Beer:
        return self.beer

    def get_pressure(self) -> Decimal:
        return self.pressure

    def get_remaining_content(self) -> Decimal:
        return self.remaining_content

    def deduct_remaining_content(self, amount: Decimal) -> Decimal:
        if self.remaining_content - amount < 0:
            raise BeerSystemException(BeerSystemException.ErrorCode.KEG_EMPTY)
        self.remaining_content -= amount
        self.last_remaining_content_deduction = amount
        return self.get_remaining_content()

    def void_last_transaction(self):
        if self.last_remaining_content_deduction is not None:
            self.remaining_content += self.last_remaining_content_deduction
            self.last_remaining_content_deduction = None
