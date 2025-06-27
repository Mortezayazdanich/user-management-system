import sqlite3

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # SQL command to create a table named 'users'
    # The "IF NOT EXISTS" clause prevents an error if the table already exists.
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL
    );
    """
    cursor.execute(create_table_query)
    print("Database initialized and 'users' table created successfully.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    # This allows us to run `python backend/database.py` from the terminal
    # to initialize the database manually.
    init_db()