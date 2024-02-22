# This class represents an object (record) in a database table
from decimal import Decimal


class Beer:
    def __init__(self, name: str, style: str, abv: Decimal, ebc: Decimal, ibu: int, kcal: Decimal, price_per_liter: Decimal):
        self.name = name
        self.style = style
        self.abv = abv
        self.ebc = ebc
        self.ibu = ibu
        self.kcal = kcal
        self.price_per_liter = price_per_liter

    def get_name(self) -> str:
        return self.name

    def get_style(self) -> str:
        return self.style

    def get_abv(self) -> Decimal:
        return self.abv

    def get_ebc(self) -> Decimal:
        return self.ebc

    def get_ibu(self) -> int:
        return self.ibu

    def get_kcal(self) -> Decimal:
        return self.kcal

    def get_price_per_liter(self) -> Decimal:
        return self.price_per_liter
