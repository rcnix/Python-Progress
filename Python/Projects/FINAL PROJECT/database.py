# This file handles database connection, password security, and queue system
import os # It is used to get secret info from.env file
import hashlib # It is used to encrypt passwords
import hmac  # It is used for secure password checking
import psycopg2 # The tool to connect to postgreSQL database
from dotenv import load_dotenv # Used to load secret data

# Loads the secret info like username and password of database
load_dotenv()


def get_connection():
# Opens a connection to the configured PostgreSQL database
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"), # Gets database name
        user=os.getenv("DB_USER"), # Gets database username
        password=os.getenv("DB_PASSWORD"), # Gets database password
        host=os.getenv("DB_HOST"), # Gets database location
        port=os.getenv("DB_PORT"), # Gets database port
    )


# Creates and updates the required database tables
def ensure_schema():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS queue_tickets (
                    id SERIAL PRIMARY KEY,
                    ticket_number VARCHAR(30) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    served BOOLEAN DEFAULT FALSE
                )
                """
            )
            cursor.execute(
                """
                ALTER TABLE queue_tickets
                ADD COLUMN IF NOT EXISTS counter_number INTEGER
                """
            )
            cursor.execute(
                """
                UPDATE queue_tickets
                SET counter_number = 1
                WHERE counter_number IS NULL
                """
            )
            cursor.execute(
                """
                ALTER TABLE queue_tickets
                ALTER COLUMN counter_number SET DEFAULT 1
                """
            )
            cursor.execute(
                """
                ALTER TABLE queue_tickets
                ALTER COLUMN counter_number SET NOT NULL
                """
            )
            cursor.execute(
                """
                ALTER TABLE queue_tickets
                DROP CONSTRAINT IF EXISTS queue_tickets_counter_number_check
                """
            )
            cursor.execute(
                """
                ALTER TABLE queue_tickets
                ADD CONSTRAINT queue_tickets_counter_number_check
                CHECK (counter_number BETWEEN 1 AND 6)
                """
            )


# Creates a salted password hash
def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000,
    )
    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash): # Check if login password is correct
    salt_hex, hash_hex = stored_hash.split(":") # Separate salt and hash
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt_hex),
        100000,
    )
    return hmac.compare_digest(new_hash.hex(), hash_hex)


# Checks whether the supplied login credentials are valid
def authenticate(username, password):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,),
            )
            result = cursor.fetchone()

    return result is not None and verify_password(password, result[0])


# Deletes a user after verifying the supplied password
def delete_user(username, password):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,),
            )
            result = cursor.fetchone()

            if result is None or not verify_password(password, result[0]):
                return False

            cursor.execute(
                "DELETE FROM users WHERE username = %s",
                (username,),
            )

    return True


# Adds a ticket to a counter queue in the database
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


# Counts tickets that are still waiting
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

# Gets the waiting tickets for one counter
def get_waiting_tickets(counter_number):
    ensure_schema()
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


# Serves the oldest waiting ticket for one counter
def serve_next(counter_number):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, ticket_number
                FROM queue_tickets
                WHERE served = FALSE AND counter_number = %s
                ORDER BY created_at, id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """,
                (counter_number,),
            )
            ticket = cursor.fetchone()
            if ticket is None:
                return None

            cursor.execute(
                """
                UPDATE queue_tickets
                SET served = TRUE
                WHERE id = %s
                """,
                (ticket[0],),
            )
            return ticket[1]


# Deletes every ticket from the queue table
def clear_queue():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM queue_tickets")
