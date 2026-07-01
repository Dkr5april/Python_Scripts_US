import sqlite3

def initialize_database():
    # This creates the file 'banking.db' in your current folder
    conn = sqlite3.connect("banking.db")
    cursor = conn.cursor()

    # Create the accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            owner_name TEXT,
            balance REAL
        )
    ''')

    # Add some dummy data
    sample_data = [
        ("101", "Alice Smith", 5000.50),
        ("102", "Bob Jones", 1250.75),
        ("103", "Charlie Brown", 75.00)
    ]

    cursor.executemany("INSERT OR REPLACE INTO accounts VALUES (?, ?, ?)", sample_data)

    conn.commit()
    conn.close()
    print("Database 'banking.db' initialized with sample data.")

if __name__ == "__main__":
    initialize_database()