from langchain_core.tools import tool
import sqlite3

@tool
def get_balance(account_id: str):
    """
    Use this tool to fetch the current account balance for a given account ID.
    Always use this when the user asks about their financial balance.
    """
    conn = sqlite3.connect("banking.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    
    # Close connection for safety
    conn.close()
    
    return f"Balance is ${result[0]}" if result else "Account not found."