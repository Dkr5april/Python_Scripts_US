import sqlite3

# Define a tool to fetch balance
def get_balance(account_id: str):
    conn = sqlite3.connect("banking.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    return f"Balance is ${result[0]}" if result else "Account not found."