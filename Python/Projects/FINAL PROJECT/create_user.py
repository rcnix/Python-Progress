from database import get_connection, hash_password

username = input("Username: ")
password = input("Password: ")

with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, hash_password(password)),
        )

print("User created successfully.")