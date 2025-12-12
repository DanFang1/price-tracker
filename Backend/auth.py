from passlib.context import CryptContext
from database import get_connection
from psycopg2 import sql, IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    "Hashes a plain text password using bcrypt"
    return pwd_context.hash(password.encode('utf-8'))


def verify_password(plain_password: str, hashed_password:str) -> bool:
    "Verifies a plain text password against a hashed password"
    return pwd_context.verify(plain_password, hashed_password)


def register_user(username: str, email: str, password: str) -> int:
    "Registers a new user into the accounts table and returns the user ID"
    hashed_pwd = hash_password(password)

    query = sql.SQL(
        """
        INSERT INTO accounts (username, hash_password, email)
        VALUES (%s, %s, %s)
        RETURNING user_id;
        """
    )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (username, hashed_pwd, email))
                user_id = cur.fetchone()[0]
                conn.commit()
        return user_id 
    except IntegrityError as e:
        raise ValueError(f"Error registering user: {e}")


def login_user(username: str, password: str) -> bool:
    "Verifies user credentials for login"
    query = sql.SQL("""
        SELECT user_id, hash_password FROM accounts WHERE username = %s;
    """)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (username,))
            row = cur.fetchone()
    
    if not row:
        raise ValueError("Username not found.")
    
    user_id, hashed_password = row

    if not verify_password(password, hashed_password):
        raise ValueError("Password is incorrect.")

    return user_id
    
if __name__ == "__main__":
    from database import check_connection
    check_connection()

    try:
        uid = register_user("ashwini", "ashwini@example.com", "ashwinipass6769")
        print(f"Registered user {uid}")
    except ValueError as e:
        print(f"Registered failed: {e}")

    try:
        uid = login_user("ashwini", "ashwinipass6769")
        print(f"User {uid} logged in successfully.")
    except ValueError as e:
        print(f"Login failed: {e}")

        


