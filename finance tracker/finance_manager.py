import sqlite3
import tkinter as tk
from tkinter import messagebox

# Database setup
conn = sqlite3.connect('finance.db')
c = conn.cursor()

# Create tables if they do not exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category TEXT, amount REAL, date TEXT, type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS budgets
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category TEXT, amount REAL)''')
conn.commit()

# Check if 'type' column exists, if not, add it
try:
    c.execute("ALTER TABLE transactions ADD COLUMN type TEXT")
except sqlite3.OperationalError:
    pass  # Column already exists

# User functions
def register_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", "Registration successful!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")

def login_user(username, password):
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    return result[0] if result else None

# Transaction functions
def add_transaction(user_id, category, amount, date, trans_type):
    c.execute("INSERT INTO transactions (user_id, category, amount, date, type) VALUES (?, ?, ?, ?, ?)", 
              (user_id, category, amount, date, trans_type))
    conn.commit()
    messagebox.showinfo("Success", f"{trans_type} added successfully!")
    check_budget(user_id, category, amount)

def update_transaction(trans_id, category, amount, date):
    c.execute("UPDATE transactions SET category = ?, amount = ?, date = ? WHERE id = ?", 
              (category, amount, date, trans_id))
    conn.commit()
    messagebox.showinfo("Success", "Transaction updated successfully!")

def delete_transaction(trans_id):
    c.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    messagebox.showinfo("Success", "Transaction deleted successfully!")

def get_transactions(user_id):
    c.execute("SELECT id, category, amount, date, type FROM transactions WHERE user_id = ?", (user_id,))
    return c.fetchall()

def get_total_income(user_id):
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Income'", (user_id,))
    total_income = c.fetchone()[0] or 0
    return total_income

def get_total_expenses(user_id):
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'Expense'", (user_id,))
    total_expenses = c.fetchone()[0] or 0
    return total_expenses

def check_budget(user_id, category, amount):
    budget = get_budget(user_id, category)
    if budget is not None and amount > budget:
        messagebox.showwarning("Budget Alert", f"You have exceeded your budget for {category}!")

def get_budget(user_id, category):
    c.execute("SELECT amount FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
    result = c.fetchone()
    return result[0] if result else None

def set_budget(user_id, category, amount):
    c.execute("INSERT INTO budgets (user_id, category, amount) VALUES (?, ?, ?)", (user_id, category, amount))
    conn.commit()
    messagebox.showinfo("Success", f"Budget for {category} set to ${amount:.2f}")

def generate_monthly_report(user_id, month, year):
    total_income = get_total_income(user_id)
    total_expenses = get_total_expenses(user_id)
    savings = total_income - total_expenses
    return total_income, total_expenses, savings

def generate_yearly_report(user_id, year):
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND strftime('%Y', date) = ? AND type = 'Income'", (user_id, year))
    total_income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND strftime('%Y', date) = ? AND type = 'Expense'", (user_id, year))
    total_expenses = c.fetchone()[0] or 0

    savings = total_income - total_expenses
    return total_income, total_expenses, savings

def show_transactions(user_id):
    transactions_window = tk.Toplevel(root)
    transactions_window.title("Transactions")
    transactions_window.state('zoomed')  # Maximize the window

    transaction_frame = tk.Frame(transactions_window)
    transaction_frame.pack(fill=tk.BOTH, expand=True)

    transaction_list = tk.Listbox(transaction_frame, height=15, width=50)
    transaction_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(transaction_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    transaction_list.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=transaction_list.yview)

    def refresh_transactions():
        transaction_list.delete(0, tk.END)
        transactions = get_transactions(user_id)
        for transaction in transactions:
            trans_id, category, amount, date, trans_type = transaction
            transaction_list.insert(tk.END, f"{trans_type} - {category}: {amount:.2f} on {date} (ID: {trans_id})")

        # Clear the text fields
        category_entry.delete(0, tk.END)
        amount_entry.delete(0, tk.END)
        date_entry.delete(0, tk.END)
        type_entry.delete(0, tk.END)

    entry_frame = tk.Frame(transactions_window)
    entry_frame.pack(pady=10)

    tk.Label(entry_frame, text="Category:").grid(row=0, column=0)
    category_entry = tk.Entry(entry_frame)
    category_entry.grid(row=0, column=1)

    tk.Label(entry_frame, text="Amount:").grid(row=1, column=0)
    amount_entry = tk.Entry(entry_frame)
    amount_entry.grid(row=1, column=1)

    tk.Label(entry_frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0)
    date_entry = tk.Entry(entry_frame)
    date_entry.grid(row=2, column=1)

    tk.Label(entry_frame, text="Type (Income/Expense):").grid(row=3, column=0)
    type_entry = tk.Entry(entry_frame)
    type_entry.grid(row=3, column=1)

    tk.Button(transactions_window, text="Add Transaction", command=lambda: add_transaction(user_id, category_entry.get(), float(amount_entry.get()), date_entry.get(), type_entry.get()) or refresh_transactions()).pack(pady=5)
    tk.Button(transactions_window, text="Refresh", command=refresh_transactions).pack(pady=5)

    # Total Income and Expense Report
    report_frame = tk.Frame(transactions_window)
    report_frame.pack(pady=10)

    total_income = get_total_income(user_id)
    total_expenses = get_total_expenses(user_id)

    tk.Label(report_frame, text=f"Total Income: {total_income:.2f}").grid(row=0, column=0)
    tk.Label(report_frame, text=f"Total Expenses: {total_expenses:.2f}").grid(row=1, column=0)
    tk.Label(report_frame, text=f"Savings: {total_income - total_expenses:.2f}").grid(row=2, column=0)

    # Monthly and Yearly Report Section
    report_section = tk.Frame(transactions_window)
    report_section.pack(pady=10)

    tk.Label(report_section, text="Generate Monthly Report").grid(row=0, column=0, columnspan=2)
    tk.Label(report_section, text="Month (MM):").grid(row=1, column=0)
    month_entry = tk.Entry(report_section)
    month_entry.grid(row=1, column=1)

    tk.Label(report_section, text="Year (YYYY):").grid(row=2, column=0)
    year_entry = tk.Entry(report_section)
    year_entry.grid(row=2, column=1)

    def generate_monthly_report_action():
        month = month_entry.get()
        year = year_entry.get()
        total_income, total_expenses, savings = generate_monthly_report(user_id, month, year)
        messagebox.showinfo("Monthly Report", f"Total Income: {total_income:.2f}\nTotal Expenses: {total_expenses:.2f}\nSavings: {savings:.2f}")

    tk.Button(report_section, text="Generate Monthly Report", command=generate_monthly_report_action).grid(row=3, columnspan=2, pady=5)

    tk.Label(report_section, text="Generate Yearly Report").grid(row=4, column=0, columnspan=2)
    tk.Label(report_section, text="Year (YYYY):").grid(row=5, column=0)
    year_report_entry = tk.Entry(report_section)
    year_report_entry.grid(row=5, column=1)

    def generate_yearly_report_action():
        year = year_report_entry.get()
        total_income, total_expenses, savings = generate_yearly_report(user_id, year)
        messagebox.showinfo("Yearly Report", f"Total Income: {total_income:.2f}\nTotal Expenses: {total_expenses:.2f}\nSavings: {savings:.2f}")

    tk.Button(report_section, text="Generate Yearly Report", command=generate_yearly_report_action).grid(row=6, columnspan=2, pady=5)

    refresh_transactions()

def show_login():
    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.geometry("300x250")
    login_window.resizable(False, False)

    login_frame = tk.Frame(login_window, padx=10, pady=10)
    login_frame.pack(pady=20)

    tk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
    username_entry = tk.Entry(login_frame)
    username_entry.grid(row=0, column=1)

    tk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
    password_entry = tk.Entry(login_frame, show="*")
    password_entry.grid(row=1, column=1)

    tk.Button(login_frame, text="Login", command=lambda: login_and_show_transactions(username_entry.get(), password_entry.get(), login_window)).grid(row=2, columnspan=2, pady=10)
    tk.Button(login_frame, text="Register", command=show_registration).grid(row=3, columnspan=2)

def show_registration():
    registration_window = tk.Toplevel(root)
    registration_window.title("Register")
    registration_window.geometry("300x250")
    registration_window.resizable(False, False)

    registration_frame = tk.Frame(registration_window, padx=10, pady=10)
    registration_frame.pack(pady=20)

    tk.Label(registration_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
    username_entry = tk.Entry(registration_frame)
    username_entry.grid(row=0, column=1)

    tk.Label(registration_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
    password_entry = tk.Entry(registration_frame, show="*")
    password_entry.grid(row=1, column=1)

    tk.Button(registration_frame, text="Register", command=lambda: register_user(username_entry.get(), password_entry.get())).grid(row=2, columnspan=2, pady=10)

def login_and_show_transactions(username, password, login_window):
    user_id = login_user(username, password)
    if user_id:
        login_window.destroy()
        show_transactions(user_id)
    else:
        messagebox.showerror("Error", "Invalid username or password.")

# Main window
root = tk.Tk()
root.title("Personal Finance Manager")
root.geometry("400x200")
root.resizable(False, False)

login_button = tk.Button(root, text="Login", command=show_login)
login_button.pack(pady=20)

root.mainloop()

# Close the database connection when the application exits
conn.close()

#End of the program
