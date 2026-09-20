import getpass

import psycopg2

from database import ensure_schema, get_connection, hash_password

username = input("Username: ")
password = getpass.getpass("Password: ")

if not username.strip() or not password:
    raise SystemExit("Username and password are required.")

try:
    ensure_schema()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                """,
                (username.strip(), hash_password(password)),
            )
except psycopg2.errors.UniqueViolation:
    raise SystemExit("That username already exists in this database.")
except psycopg2.Error as error:
    raise SystemExit(
        "Could not create the user. Check PostgreSQL and the .env settings.\n"
        f"{error}"
    )

print("User created successfully.")
