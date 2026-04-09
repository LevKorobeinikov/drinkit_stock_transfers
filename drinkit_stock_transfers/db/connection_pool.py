from __future__ import annotations

from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from drinkit_stock_transfers.config import DB_PARAMS


class DBConnectionPool:
    _pool: pool.ThreadedConnectionPool | None = None

    @classmethod
    def initialize(cls, minconn=1, maxconn=10):
        if cls._pool is None:
            cls._pool = psycopg2.pool.ThreadedConnectionPool(minconn, maxconn, **DB_PARAMS)

    @classmethod
    def get_conn(cls):
        if cls._pool is None:
            raise Exception("DBConnectionPool is not initialized")
        return cls._pool.getconn()

    @classmethod
    def release_conn(cls, conn):
        if cls._pool:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        if cls._pool:
            cls._pool.closeall()


@contextmanager
def get_db_connection():
    conn = DBConnectionPool.get_conn()
    try:
        yield conn
    finally:
        DBConnectionPool.release_conn(conn)
