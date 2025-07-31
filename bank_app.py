import sqlite3
import random
import re
import time
import getpass
import hashlib

BANKING_FILES = "BIF.db"

def set_up():
    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                balance  REAL NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                sender TEXT,
                reciever TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) 
            );
        """)

def generate_unique_account_number():
    while True:
        acc_no = str(random.randint(10000000, 99999999))
        with sqlite3.connect(BANKING_FILES) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE account_number = ?", (acc_no,))
            if not cursor.fetchone():
                return acc_no

def is_valid_password(password):
    return (
        8 <= len(password) <= 30 and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*()_+{}:;,.<>?]", password)
    )

def is_valid_username(username):
    return re.fullmatch(r"\w{3,20}", username)

def sign_up():
    while True:
        first_name = input("Enter your first name: ").strip()
        if not first_name.isalpha():
            print("First name is required")
            continue
        break

    while True:
        last_name = input("Enter your last name: ").strip()
        if not last_name.isalpha():
            print("Last name is required")
            continue
        break

    full_name = f"{first_name} {last_name}".title()

    while True:
        username = input("Enter your username: ").strip()
        if not is_valid_username(username):
            print("Username is required")
            continue
        break

    while True:
        password = getpass.getpass("Enter your password: ").strip()
        if not is_valid_password(password):
            print("Password must be 8-30 characters, and include upper/lowercase, number, and special character.")
            continue

        confirm_password = getpass.getpass("Confirm your password: ").strip()
        if not is_valid_password(confirm_password):
            print("Confirm Password is required")
            continue

        if password != confirm_password:
            print("Passwords don't match")
            continue
        break

    while True:
        try:
            initial_deposit = float(input("Enter your initial initial_deposit (min ₦2000): "))
            if initial_deposit < 2000:
                print("Minimum initial_deposit is ₦2000")
                continue
            break
        except ValueError:
            print("Please enter a valid number")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    account_number = generate_unique_account_number()

    balance = initial_deposit

    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (full_name, username, password, account_number, balance)
                VALUES (?, ?, ?, ?, ?)
            """, (full_name, username, hashed_password, account_number, balance))
            conn.commit()
            print("Sign up successful!")
            print(f"Your account number is {account_number}")
        except sqlite3.IntegrityError as e:
            error_message = str(e)
            if "username" in error_message:
                print("Username already exists")
            elif "account_number" in error_message:
                print("Generated account number already exists, please try again")

def log_in():
    while True:
        while True:
            username = input("Enter your username: ").strip()
            if not is_valid_username(username):
                print("Username is required")
                continue
            break

        while True:
            password = getpass.getpass("\nEnter your password: ").strip()
            if not password:
                print("Password is required")
                continue
            break

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        with sqlite3.connect(BANKING_FILES) as conn:
            cursor = conn.cursor()
            user = cursor.execute("""
                SELECT id, full_name FROM users WHERE username = ? AND password = ?
            """, (username, hashed_password)).fetchone()

            if user is None:
                print("Invalid username or password")
                continue
            else:
                print("\nLogged in successfully")
                bank_app(user)

def bank_app(user):
    user_id, full_name = user
    print(f"Hello, {full_name}")

    while True:
        print(
            """
            
1. Deposit
2. Withdraw
3. Check Balance
4. Transaction History
5. Transfer
6. Account Details
7. Log out
""")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            deposit(user_id)
        elif choice == "2":
            withdraw(user_id)
        elif choice == "3":
            check_balance(user_id)
        elif choice == "4":
            transaction_history(user_id)
        elif choice == "5":
            transfer(user_id)
        elif choice == "6":
            account_details(user_id)
        elif choice == "7":
            print("Logged out.\n")
            break
        else:
            print("Invalid option")

def deposit(user_id):
    while True:
        amount = input("Enter deposit amount: ").strip()
        if not amount or not amount.replace('.', '', 1).isdigit():
            print("Invalid amount.")
            continue
        amount = float(amount)
        if amount <= 0:
            print("Amount must be greater than zero.")
            continue
        break

    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, details) VALUES (?, 'deposit', ?, ?)", (user_id, amount, 'Deposited funds'))
        conn.commit()
        loading("Deposit successful.")

def withdraw(user_id):
    while True:
        amount = input("Enter withdrawal amount: ").strip()
        if not amount or not amount.replace('.', '', 1).isdigit():
            print("Invalid amount.")
            continue
        amount = float(amount)
        if amount <= 0:
            print("Amount must be greater than zero.")
            continue

        with sqlite3.connect(BANKING_FILES) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            
            balance = cursor.fetchone()[0]
            
            if amount > balance:
                print("Insufficient funds.")
                continue
            cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
            cursor.execute("INSERT INTO transactions (user_id, type, amount, details) VALUES (?, 'withdrawal', ?, ?)", (user_id, amount, 'Withdrawal'))
            conn.commit()
            loading("processing withdrawal....")
            time.sleep(1)
            print("Withdrawal successful.")
            break

def loading(text):
    print(text, end='')
    for _ in range(10):
        time.sleep(0.3)
        print(".", end='', flush=True)

def check_balance(user_id):
    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        balance = cursor.fetchone()[0]
        time.sleep(2)
        print(f"Your current balance is ₦{balance:,.2f}")

def transaction_history(user_id):
    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT type, amount, timestamp, details, sender FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        rows = cursor.fetchall()
        if not rows:
            print("No transactions yet.")
        else:
            time.sleep(1)
            print("Your Transaction History:")
            for tx in rows:
                sender_display = f"from {tx[4]}" if tx[4] else ""
                print(f"{tx[2]} | {tx[0].title()} | ₦{tx[1]:,.2f} | {sender_display}")

def account_details(user_id):
    with sqlite3.connect(BANKING_FILES) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, username, account_number FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        time.sleep(1)
        print(f"Full Name: {user[0]}")
        print(f"Username: {user[1]}")
        print(f"Account Number: {user[2]}")

def transfer(user_id):
    try:
        with sqlite3.connect(BANKING_FILES) as conn:
            cursor = conn.cursor()

            while True:
                recipient_acct = input("Enter recipient account number: ").strip()
                if not recipient_acct.isdigit():
                    print("Account number must be numeric.")
                    continue

                cursor.execute("SELECT id, full_name FROM users WHERE account_number = ?", (recipient_acct,))
                result = cursor.fetchone()
                if not result:
                    print("Account number not found.")
                    continue

                recipient_id, receiver_name = result
                if recipient_id == user_id:
                    print("You can't transfer to yourself.")
                    continue

                print(f"\nRecipient Name: {receiver_name}")
                confirm = input("Do you want to continue with the transfer? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("Transfer cancelled. Returning to menu...")
                    break

                amount_input = input("Enter transfer amount: ").strip()
                if not amount_input or not amount_input.replace('.', '', 1).isdigit():
                    print("Invalid amount. Use only numbers.")
                    continue

                amount = float(amount_input)
                if amount <= 0:
                    print("Amount must be greater than zero.")
                    continue

                cursor.execute("SELECT balance, full_name FROM users WHERE id = ?", (user_id,))
                sender_balance, sender_name = cursor.fetchone()
                if amount > sender_balance:
                    print(f"Insufficient funds. You can only transfer up to {sender_balance}")
                    continue

                cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, recipient_id))

                cursor.execute("""
                    INSERT INTO transactions (user_id, reciever, type, amount, details)
                    VALUES (?, ?, 'transfer out', ?, ?)
                """, (user_id, receiver_name, amount, f"Transfer to {recipient_acct}"))

                cursor.execute("""
                    INSERT INTO transactions (user_id, sender, type, amount, details)
                    VALUES (?, ?, 'transfer in', ?, ?)
                """, (recipient_id, sender_name, amount, f"Received from {sender_name}"))

                conn.commit()
                time.sleep(1)
                loading(f"₦{amount:,.2f} sent to {recipient_acct}, {receiver_name} successfully.")
                break
    except ValueError:
        print("Please enter a valid number.")

set_up()

menu = """
✨ Welcome to My Bank App! ✨

What would you like to do today?

1. Sign Up
2. Log In
3. Quit
"""

while True:
    print(menu)
    choice = input("Choose an option from the menu above: ").strip()

    if choice == "1":
        sign_up()
    elif choice == "2":
        log_in()
    elif choice == "3":
        print("Goodbye")
        break
    else:
        print("Invalid choice")
