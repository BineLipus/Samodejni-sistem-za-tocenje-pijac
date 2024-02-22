import time

from urllib import request
from urllib.error import URLError

import mysql.connector
from mysql.connector import DatabaseError

from Logger import Log
from BeerSystemException import BeerSystemException
from VO.Glass import Glass
from VO.Beer import Beer
from VO.Keg import Keg
from VO.Pour import Pour


class DatabaseRepository:
    host = "server.domain"
    user = "db_username"
    password = "db_password"
    database = "AutomaticBeerTap"
    connection_timeout = 1800
    connection_attempts = 5

    def __init__(self):
        Log.debug("Initializing database connection.")

        attempt = 0
        while attempt < self.connection_attempts:
            attempt += 1
            try:
                self.connection = None
                self.connect()
            except DatabaseError as e:
                Log.error("Couldn't connect to mysql database. Error number: %s. Retrying..." % e.errno)

        #ping_thread = threading.Thread(target=self.ping, daemon=True)
        #ping_thread.start()
        Log.debug("Connected to database %s on host %s" % (self.database, self.host))

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            connection_timeout=self.connection_timeout)
        # Calling the same select query without doing a commit, won't update the results.
        self.connection.autocommit = True  # Sets auto commit

    @staticmethod
    def __is_connected_to_internet__() -> bool:
        try:
            request.urlopen('http://google.com', timeout=3)
            return True
        except URLError as err:
            return False

    def ping(self):
        while True:
            if self.connection is not None and not self.connection.in_transaction:
                time.sleep(10)  # Send ping every minute
                # Keep the connection alive by pinging while not in transaction. Not the best solution
                Log.debug_extra_detailed("DB PING")
                cursor = self.get_cursor()
                cursor.execute("SELECT 'PING'")
                cursor.fetchone()
                Log.debug_extra_detailed("DB PING finished successfully, timestamp: " + time.strftime("%H:%M:%S", time.localtime()))

    def get_cursor(self):
        Log.debug_extra_detailed("Trying to get database cursor")
        # if not DatabaseRepository.__is_connected_to_internet__():
        #     Log.warn("Connection to network dropped!")
        #     raise BeerSystemException(BeerSystemException.ErrorCode.NETWORK_PROBLEM)
        # if not self.connection.is_connected() or self.connection.is_closed():
        #     Log.debug("Trying to reconnect to database %s on host %s" % (self.database, self.host))
        #     self.connection.reconnect(5, 1)
        #     if self.connection.is_connected():
        #         Log.debug("Reconnected to database %s on host %s" % (self.database, self.host))
        #     else:
        #         # if connection failed to reconnect, create a new connection
        #         self.connect()
        # return self.connection.cursor(dictionary=True)  # dictionary enables us to access columns by their name
        if not self.connection.in_transaction:
            self.connect()
        return self.connection.cursor(dictionary=True)

    def start_transaction(self):
        self.connection.autocommit = False
        self.connection.start_transaction()

    def commit_transaction(self):
        self.connection.commit()
        self.connection.autocommit = True

    def rollback_transaction(self):
        self.connection.rollback()
        self.connection.autocommit = True

    def resolve_glass_by_rfid(self, rfid) -> Glass:
        cursor = self.get_cursor()
        cursor.execute(DatabaseRepository.PreparedStatement.SELECT_GLASS_BY_RFID % rfid)
        result = cursor.fetchone()

        if result is not None:
            return Glass(str(result["rfid"]), float(result["volume"]), float(result["balance"]))
        else:
            Log.warn("Glass with rfid %d not recognized in the database" % rfid)
            raise BeerSystemException(BeerSystemException.ErrorCode.GLASS_NOT_RECOGNIZED, rfid)

    def resolve_keg_and_beer_by_tap(self, valve) -> Keg:
        cursor = self.get_cursor()
        cursor.execute(DatabaseRepository.PreparedStatement.SELECT_KEG_BY_VALVE_ID % valve.get_id())
        result = cursor.fetchone()

        if result:
            return Keg(result["keg_id"], result["keg_volume"], valve.get_id(),
                       Beer(result["name"], result["style"], result["abv"], result["ebc"], result["ibu"],
                            result["kcal"], result["price_per_liter"]),
                       result["keg_pressure"], result["keg_remaining_content"])
        else:
            Log.warn(
                "Valve %s not attached to any keg in the database. Check database configuration." % valve.get_title())
            raise BeerSystemException(BeerSystemException.ErrorCode.TAP_NOT_CONNECTED, valve.get_title())

    def update_glass_balance(self, glass: Glass) -> None:
        cursor = self.get_cursor()
        cursor.execute(
            DatabaseRepository.PreparedStatement.UPDATE_GLASS_BALANCE % (glass.get_balance(), glass.get_id()))
        if cursor.rowcount != 1:
            # If multiple glasses have been updated or no glass was updated, there was an error.
            raise BeerSystemException(BeerSystemException.ErrorCode.GENERAL_ERROR)

    def update_keg_remaining_content(self, keg: Keg) -> None:
        cursor = self.get_cursor()
        cursor.execute(
            DatabaseRepository.PreparedStatement.UPDATE_KEG_REMAINING_CONTENT % (
                keg.get_remaining_content(), keg.get_id()))
        if cursor.rowcount != 1:
            # If multiple kegs have been updated or no keg was updated, there was an error.
            raise BeerSystemException(BeerSystemException.ErrorCode.GENERAL_ERROR)

    def insert_pour(self, pour: Pour) -> None:
        cursor = self.get_cursor()
        cursor.execute(
            DatabaseRepository.PreparedStatement.INSERT_POUR % (
                pour.get_keg().get_id(), pour.get_glass().get_id(), pour.get_timestamp()))
        if cursor.rowcount != 1:
            raise BeerSystemException(BeerSystemException.ErrorCode.GENERAL_ERROR)

    class PreparedStatement:
        SELECT_GLASS_BY_RFID = """SELECT * FROM glass where rfid='%s'"""
        SELECT_KEG_BY_VALVE_ID = """SELECT keg.id as 'keg_id', keg.volume as 'keg_volume', 
                                 keg.pressure as 'keg_pressure', keg.remaining_content as 'keg_remaining_content', 
                                 beer.* FROM keg join beer on keg.beer = beer.name where keg.valve_id=%d"""
        UPDATE_GLASS_BALANCE = """UPDATE glass SET glass.balance = %f WHERE glass.rfid = %s"""
        UPDATE_KEG_REMAINING_CONTENT = """UPDATE keg SET keg.remaining_content = %f WHERE keg.id = %d"""
        INSERT_POUR = """INSERT INTO pour (keg, glass, timestamp) VALUES (%d, '%s', '%s')"""
