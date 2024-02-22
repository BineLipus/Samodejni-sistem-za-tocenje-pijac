# This class represents an object (record) in a database table
from decimal import Decimal
from BeerSystemException import BeerSystemException


class Glass:
    def __init__(self, rfid: str, volume: Decimal, balance: Decimal):
        self.rfid = rfid
        self.volume = Decimal(volume)
        self.balance = Decimal(balance)
        self.last_balance_deduction = None  # Used to restore balance in case of GLASS_REMOVED_PREMATURELY error

    def get_id(self) -> str:
        return self.rfid

    def get_volume(self) -> Decimal:
        return self.volume

    def get_balance(self) -> Decimal:
        return self.balance

    def get_balance_string(self) -> str:
        return "{balance:.2f}".format(balance=self.balance)

    def deduct_balance(self, amount: Decimal) -> Decimal:
        if self.balance - amount < 0:
            raise BeerSystemException(BeerSystemException.ErrorCode.INSUFFICIENT_BALANCE)
        self.balance -= amount
        self.last_balance_deduction = amount
        return self.get_balance()

    def void_last_transaction(self):
        if self.last_balance_deduction is not None:
            self.balance += self.last_balance_deduction
            self.last_balance_deduction = None
