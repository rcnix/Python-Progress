import os
import hashlib
import hmac
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000,
    )
    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    salt_hex, hash_hex = stored_hash.split(":")
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt_hex),
        100000,
    )
    return hmac.compare_digest(new_hash.hex(), hash_hex)


def authenticate(username, password):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,),
            )
            result = cursor.fetchone()

    return result is not None and verify_password(password, result[0])


def add_ticket(ticket_number, counter_number=1):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO queue_tickets (ticket_number, counter_number)
                VALUES (%s, %s)
                """,
                (ticket_number, counter_number),
            )


def get_waiting_count(counter_number=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            if counter_number is None:
                cursor.execute(
                    "SELECT COUNT(*) FROM queue_tickets WHERE served = FALSE"
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM queue_tickets
                    WHERE served = FALSE AND counter_number = %s
                    """,
                    (counter_number,),
                )
            return cursor.fetchone()[0]

def get_waiting_tickets(counter_number):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ticket_number
                FROM queue_tickets
                WHERE served = FALSE AND counter_number = %s
                ORDER BY created_at, id
                """,
                (counter_number,),
            )
            return [row[0] for row in cursor.fetchall()]


def clear_queue():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM queue_tickets")