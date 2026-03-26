import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import GROOVE, LabelFrame, messagebox, StringVar, Label, Entry, Button, Frame, Radiobutton, Toplevel
import mysql.connector
from mysql.connector import Error

def create_database_and_tables():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='P16@2007'  # Replace with your MySQL root password
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Create the database
            cursor.execute("CREATE DATABASE IF NOT EXISTS bakery;")
            print("Database 'bakery' created successfully.")

            # Use the newly created database
            cursor.execute("USE bakery;")

            # Create bakery_user table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bakery_user (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) NOT NULL
            );
            """)
            print("Table 'bakery_user' created successfully.")

            # Create bakery_items table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bakery_items (
                item_id INT PRIMARY KEY,
                item_name VARCHAR(100) NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            );
            """)
            print("Table 'bakery_items' created successfully.")

            # Create orders table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL,
                total_price DECIMAL(10, 2) NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES bakery_user(username)
            );
            """)
            print("Table 'orders' created successfully.")


    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

def main(): 
    win = tk.Tk()
    app = LoginPage(win)
    win.mainloop()

class LoginPage:
    def __init__(self, win):
        self.win = win
        win.geometry("1350x750")
        win.title('BAKERY Management System')
        win.configure(bg="#E1F5FE")

        self.title_label = Label(win, text="The Doughy Delight", font=("Arial", 35, "bold"), bg="#E1F5FE", bd=8, relief=tk.GROOVE)
        self.title_label.pack(side=tk.TOP, fill=tk.X)

        self.main_frame = Frame(win, bg="#E1F5FE", bd=6, relief=tk.GROOVE)
        self.main_frame.place(x=300, y=150, width=800, height=400)

        self.login_lbl = Label(self.main_frame, text="Login", bd=6, relief=tk.GROOVE, anchor='center', bg='#E1F5FE', font=('sans-serif', 25, 'bold'))
        self.login_lbl.pack(side=tk.TOP, fill=tk.X)

        self.role_var = StringVar(value="customer")
        role_frame = Frame(self.main_frame, bg="#E1F5FE")
        role_frame.pack(pady=10)

        customer_radio = Radiobutton(role_frame, text="Customer", variable=self.role_var, value="customer", bg="#E1F5FE", font=('sans-serif', 15))
        customer_radio.pack(side=tk.LEFT, padx=10)

        staff_radio = Radiobutton(role_frame, text="Staff", variable=self.role_var, value="staff", bg="#E1F5E9", font=('sans-serif', 15))
        staff_radio.pack(side=tk.LEFT, padx=10)

        entry_frame = Frame(self.main_frame, bd=6, relief=tk.GROOVE, bg='#E1F5FE')
        entry_frame.pack(fill="both", expand=True)

        entus_lbl = Label(entry_frame, text="Enter Username:", bg="#E1F5FE", font=('sans-serif', 15))
        entus_lbl.grid(row=0, column=0, padx=2, pady=2)

        self.username = StringVar()
        self.password = StringVar()

        entus_ent = Entry(entry_frame, textvariable=self.username, font=('sans-serif', 15), bd=6)
        entus_ent.grid(row=0, column=1, padx=2, pady=2)

        entuspass_lbl = Label(entry_frame, text="Enter Password:", bg="#E1F5FE", font=('sans-serif', 15))
        entuspass_lbl.grid(row=1, column=0, padx=2, pady=2)

        entuspass_ent = Entry(entry_frame, textvariable=self.password, show='*', font=('sans-serif', 15), bd=6)
        entuspass_ent.grid(row=1, column=1, padx=2, pady=2)

        # Existing code...

        button_frame = LabelFrame(entry_frame, text="Options", font=("Arial", 12), bg="#E1F5FE", bd=7, relief=GROOVE)
        button_frame.grid(row=2, columnspan=2, pady=10)

        Button(button_frame, text="Login", font=('Arial', 12), bd=5, command=self.login, bg="#4CAF50").pack(side=tk.LEFT, padx=10, pady=10)
        Button(button_frame, text="Register", font=('Arial', 12), bd=5, command=self.register_user, bg="#FFC107").pack(side=tk.LEFT, padx=10, pady=10)
        Button(button_frame, text="Reset", font=('Arial', 12), bd=5, command=self.reset, bg="#F44336").pack(side=tk.LEFT, padx=10, pady=10)

        back_button = Button(entry_frame, text="Back", command=self.go_back, bg="#FF6347", font=("Arial", 16))
        back_button.grid(row=3, columnspan=2, pady=10)  

    def go_back(self):
        self.win.destroy()

    def register_user(self):
        RegistrationPage(self.win)

    def reset(self):
        self.username.set("")  
        self.password.set("")

    def login(self):
        username = self.username.get()
        password = self.password.get()
        role = self.role_var.get()

        try:
            if role == "staff":
                if username == "BAKERY" and password == "90030":
                    messagebox.showinfo("Success", "Welcome Staff!")
                    Window3(self.win)  
                else:
                    messagebox.showerror("Login Error", "Invalid staff username or password.")
            else:
                with mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='P16@2007',  # Replace with your MySQL password
                    database='bakery'
                ) as connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT * FROM bakery_user WHERE username = %s AND password = %s", (username, password))
                    result = cursor.fetchone()

                    if result:
                        messagebox.showinfo("Success", f"Welcome Customer {username}!")
                        Window2(self.win, username)  
                    else:
                        messagebox.showerror("Login Error", "Invalid customer username or password or you are not registered.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

class RegistrationPage:
    def __init__(self, win):
        self.win = win    
        self.reg_win = Toplevel(self.win)
        self.reg_win.title("User Registration")
        self.reg_win.geometry("600x400")
        self.reg_win.configure(bg="#E1F5FE")

        self.label = Label(self.reg_win, text="Register", font=("Arial", 24, "bold"), bg="#E1F5FE")
        self.label.pack(pady=20)

        self.username = StringVar()
        self.password = StringVar()
        self.email = StringVar()

        Label(self.reg_win, text="Username:", font=("Arial", 14), bg="#E1F5FE").pack(pady=5)
        self.username_entry = Entry(self.reg_win, textvariable=self.username, font=("Arial", 14), bd=5)
        self.username_entry.pack(pady=5)

        Label(self.reg_win, text="Password:", font=("Arial", 14), bg="#E1F5FE").pack(pady=5)
        self.password_entry = Entry(self.reg_win, textvariable=self.password, font=("Arial", 14), bd=5, show='*')
        self.password_entry.pack(pady=5)

        Label(self.reg_win, text="Gmail:", font=("Arial", 14), bg="#E1F5FE").pack(pady=5)
        self.email_entry = Entry(self.reg_win, textvariable=self.email, font=("Arial", 14), bd=5)
        self.email_entry.pack(pady=5)

        self.register_button = Button(self.reg_win, text="Register", command=self.register_user, bg="#4CAF50", font=("Arial", 14))
        self.register_button.pack(pady=20)
        
    def register_user(self):
        username = self.username.get()
        password = self.password.get()
        email = self.email.get()

        if not username or not password or not email:
            messagebox.showerror("Input Error", "All fields are required!")
            return

        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'  
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO bakery_user (username, password, email) VALUES (%s, %s, %s)", 
                               (username, password, email))
                connection.commit()
                messagebox.showinfo("Success", "User registered successfully!")
                self.reg_win.destroy() 
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

class Window2:
    def __init__(self, parent, username):
        self.win = Toplevel(parent) 
        self.win.title("Menu")
        self.win.geometry("1350x750")  
        self.win.configure(bg="#E8F5E9")

        self.username = username  

        label = Label(self.win, text="Welcome to the Bakery!\nMenu", font=("Arial", 24, "bold"), bg="#E8F5E9")
        label.pack(pady=20)

        self.bakery_items = self.show_bakery_items()

        history_button = Button(self.win, text="View Order History", command=self.view_order_history, bg="#FFC107", font=("Arial", 16))
        history_button.pack(side=tk.LEFT, padx=30, pady=20)

        bill_button = Button(self.win, text="Open Billing", command=self.open_billing, bg="#FFC107", font=("Arial", 16))
        bill_button.pack(side=tk.LEFT, padx=30, pady=20)

        back_button = Button(self.win, text="Back", command=self.go_back, bg="#FF6347", font=("Arial", 16))
        back_button.pack(side=tk.LEFT, padx=30, pady=20)

    def go_back(self):
        self.win.destroy()

    def show_bakery_items(self):
        items = {}
        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT item_id, item_name, price FROM bakery_items")
                bakery_items = cursor.fetchall()

                bakery_frame = Frame(self.win, bg="#E8F5E9")
                bakery_frame.pack(pady=20, fill=tk.BOTH, expand=True)  

                for idx, item in enumerate(bakery_items, start=1):
                    item_id, item_name, price = item
                    items[item_id] = (item_name, price) 

                    item_label = Label(bakery_frame, text=f"{idx}. {item_name} - ₹{price:.2f}", font=("Arial", 16), bg="#E8F5E9")
                    item_label.pack(anchor='w')

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

        return items

    def view_order_history(self):
        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT order_id, item_name, quantity, total_price, order_date FROM orders WHERE username = %s", (self.username,))
                orders = cursor.fetchall()

                if not orders:
                    messagebox.showinfo("Order History", "No orders found.")
                    return

                history_window = Toplevel(self.win)
                history_window.title("Order History")
                history_window.geometry("800x400")
                history_window.configure(bg="#E8F5E9")

                label = Label(history_window, text="Order History", font=("Arial", 24, "bold"), bg="#E8F5E9")
                label.pack(pady=20)

                tree = ttk.Treeview(history_window, columns=("Order ID", "Item Name", "Quantity", "Total Price", "Order Date"), show='headings')
                tree.pack(pady=10, fill=tk.BOTH, expand=True)
          
                tree.heading("Order ID", text="Order ID")
                tree.heading("Item Name", text="Item Name")
                tree.heading("Quantity", text="Quantity")
                tree.heading("Total Price", text="Total Price (₹)")
                tree.heading("Order Date", text="Order Date")

                tree.column("Order ID", width=100)
                tree.column("Item Name", width=200)
                tree.column("Quantity", width=100)
                tree.column("Total Price", width=150)
                tree.column("Order Date", width=150)
 
                for order in orders:
                    order_id, item_name, quantity, total_price, order_date = order
                    tree.insert("", tk.END, values=(order_id, item_name, quantity, f"₹{total_price:.2f}", order_date))

                scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
                tree.configure(yscroll=scrollbar.set)
                scrollbar.pack(side='right', fill='y')

                close_button = Button(history_window, text="Close", command=history_window.destroy, bg="#FF6347", font=("Arial", 12))
                close_button.pack(pady=10)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    
    def open_billing(self):
        billing_window = BillingWindow(self.win, self.bakery_items, self.username)  

class BillingWindow:
    def __init__(self, parent, bakery_items, username):
        self.win = Toplevel(parent)
        self.win.title("Billing")
        self.win.geometry("1350x750")
        self.win.configure(bg="#E8F5E9")

        self.bakery_items = bakery_items
        self.selected_items = {}
        self.entries = {}
        self.username = username  

        label = Label(self.win, text="Select Items to Bill", font=("Arial", 24, "bold"), bg="#E8F5E9")
        label.pack(pady=20)

        item_frame = Frame(self.win, bg="#E8F5E9")
        item_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        for item_id, (item_name, price) in self.bakery_items.items():
            frame = Frame(item_frame, bg="#E8F5E9")
            frame.pack(fill=tk.X)

            item_label = Label(frame, text=f"{item_name} - ₹{price:.2f}", font=("Arial", 16), bg="#E8F5E9")
            item_label.pack(side=tk.LEFT, padx=5)

            quantity_entry = Entry(frame, width=5, font=("Arial", 14))
            quantity_entry.pack(side=tk.LEFT, padx=5)
            quantity_entry.insert(0, "1")

            self.entries[item_id] = quantity_entry

            add_button = Button(frame, text="Add", command=lambda id=item_id: self.add_to_bill(id), bg="#FFC107", font=("Arial", 12))
            add_button.pack(side=tk.LEFT, padx=5)

        self.total_label = Label(self.win, text="Total: ₹0.00", font=("Arial", 18), bg="#E8F5E9")
        self.total_label.pack(pady=10)

        generate_bill_button = Button(self.win, text="Generate Bill", command=self.generate_bill, bg="#4CAF50", font=("Arial", 12))
        generate_bill_button.place(x=500, y=450)

        clear_button = Button(self.win, text="Clear Selection", command=self.clear_selection, bg="#F44336", font=("Arial", 12))
        clear_button.pack(pady=10)

        back_button = Button(self.win, text="Back", command=self.go_back, bg="#FF6347", font=("Arial", 12))
        back_button.pack(pady=10)

    def go_back(self):
        self.win.destroy()

    def add_to_bill(self, item_id):
        quantity = self.entries[item_id].get()
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid quantity.")
            return

        item_name, price = self.bakery_items[item_id]
        total_price = price * quantity

        if item_id in self.selected_items:
            self.selected_items[item_id][2] += quantity
            self.selected_items[item_id][3] = self.selected_items[item_id][1] * self.selected_items[item_id][2]
        else:
            self.selected_items[item_id] = [item_name, price, quantity, total_price]

        self.update_total()

    def update_total(self):
        total = sum(item[3] for item in self.selected_items.values())
        self.total_label.config(text=f"Total: ₹{total:.2f}")

    def generate_bill(self):
        if not self.selected_items:
            messagebox.showwarning("No Selection", "Please select items to bill.")
            return

        bill_details = "=========================\n"
        bill_details += "         BAKERY BILL\n"
        bill_details += "=========================\n"
        bill_details += f"{'Item':<25} {'Qty':<5} {'Price (₹)':>10}\n"
        bill_details += "-------------------------\n"

        total = 0
        for item in self.selected_items.values():
            item_name, _, quantity, total_price = item
            bill_details += f"{item_name:<25} {quantity:<5} {total_price:>10.2f}\n"
            total += total_price

        bill_details += "-------------------------\n"
        bill_details += f"{'Total Amount:':<25} {total:>10.2f}\n"
        bill_details += "=========================\n"
        bill_details += " Thank you for your purchase!\n"
        bill_details += "=========================\n"

        self.save_order_to_db(total)

        bill_window = Toplevel(self.win)
        bill_window.title("Bill")
        bill_window.geometry("600x400")  
        bill_window.configure(bg="#FFF8DC")

        text_widget = tk.Text(bill_window, font=("Courier", 14), wrap="word", bg="#FFFACD", fg="black")
        text_widget.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        text_widget.insert("1.0", bill_details)
        text_widget.config(state=tk.DISABLED)

        close_button = Button(bill_window, text="Close", command=bill_window.destroy, bg="#FF6347", font=("Arial", 12))
        close_button.place(x=250, y=250)

    def save_order_to_db(self, total):
        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                for item in self.selected_items.values():
                    item_name, _, quantity, total_price = item
                    cursor.execute("INSERT INTO orders (username, item_name, quantity, total_price) VALUES (%s, %s, %s, %s)",
                                   (self.username, item_name, quantity, total_price))
                connection.commit()
                messagebox.showinfo("Success", "Order saved successfully!")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def clear_selection(self):
        self.selected_items.clear()
        self.update_total()
        for entry in self.entries.values():
            entry.delete(0, 'end')
            entry.insert(0, "1")

class Window3:
    def __init__(self, parent):
        self.win = Toplevel(parent)  
        self.win.title("Staff Menu")
        self.win.geometry("1350x750")
        self.win.configure(bg="#FFE5B4") 

        label = Label(self.win, text="Staff Menu", font=("Arial", 20), bg="#FFE5B4")
        label.pack(pady=20)

        self.bakery_items = self.staff_menu()
        self.create_buttons()

        back_button = Button(self.win, text="Back", command=self.go_back, bg="#FF6347", font=("Arial", 12))
        back_button.pack(pady=10)

    def go_back(self):
        self.win.destroy()

    def staff_menu(self):
        items = {}
        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT item_id, item_name, price FROM bakery_items")
                bakery_items = cursor.fetchall()

                bakery_frame = Frame(self.win, bg="#FFE5B4")
                bakery_frame.pack(pady=20)

                for item in bakery_items:
                    items[item[0]] = (item[1], item[2])
                    item_label = Label(bakery_frame, text=f"{item[0]} {item[1]} - ₹{item[2]:.2f}", font=("Arial", 16), bg="#FFE5B4")
                    item_label.pack(anchor='w')

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

        return items

    def create_buttons(self):
        button_frame = LabelFrame(self.win, text="Options", font=("Arial", 12), bg="#E1F5FE", bd=7, relief=GROOVE)
        button_frame.pack(pady=10)

        add_btn = Button(button_frame, text="Add", font=('Arial', 12), bd=5, bg="#4CAF50", command=self.add_item)
        add_btn.pack(side=tk.LEFT, padx=10, pady=10)

        delete_btn = Button(button_frame, text="Delete", font=('Arial', 12), bd=5, bg="#F44336", command=self.delete_item)
        delete_btn.pack(side=tk.LEFT, padx=10, pady=10)

        update_btn = Button(button_frame, text="Update", font=('Arial', 12), bd=5, bg="#FFC107", command=self.update_item)
        update_btn.pack(side=tk.LEFT, padx=10, pady=10)

    def add_item(self):
        item_win = Toplevel(self.win)
        item_win.title("Add Item")
       
        Label(item_win, text="Item ID:").pack()
        item_id_entry = Entry(item_win)
        item_id_entry.pack()
        
        Label(item_win, text="Item Name:").pack()
        item_name_entry = Entry(item_win)
        item_name_entry.pack()
        
        Label(item_win, text="Price:").pack()
        price_entry = Entry(item_win)
        price_entry.pack()

        Button(item_win, text="Submit", command=lambda: self.add_item_to_db(item_id_entry.get(), item_name_entry.get(), price_entry.get(), item_win)).pack(pady=10)

    def add_item_to_db(self, item_id, item_name, price, item_win):
        if not item_id or not item_name or not price:
            messagebox.showerror("Input Error", "Please enter Item ID, Item Name, and Price.")
            return

        try:
            item_id = int(item_id)
            price = float(price)

            if price <= 0:
                raise ValueError("Price must be positive.")

            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO bakery_items (item_id, item_name, price) VALUES (%s, %s, %s)", (item_id, item_name, price))
                connection.commit()
                messagebox.showinfo("Success", "Item added successfully!")
                item_win.destroy()            
                self.show_bakery_items()  

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def update_item(self):
        self.item_window("Update Item", self.update_item_in_db)

    def item_window(self, title, action):
        item_win = Toplevel(self.win)
        item_win.title(title)

        Label(item_win, text="Item Name:").pack()
        item_name = Entry(item_win)
        item_name.pack()

        Label(item_win, text="Price:").pack()
        price = Entry(item_win)
        price.pack()

        if title == "Update Item":
            Label(item_win, text="Item ID:").pack()
            item_id = Entry(item_win)
            item_id.pack()

        Button(item_win, text="Submit", command=lambda: action(item_name, price, item_id if title == "Update Item" else None)).pack(pady=10)

    def delete_item(self):
        item_win = Toplevel(self.win)
        item_win.title("Delete Item")
       
        Label(item_win, text="Item ID:").pack()
        item_id_entry = Entry(item_win)
        item_id_entry.pack()

        Button(
            item_win, 
            text="Submit", 
            command=lambda: self.delete_item_in_db(item_id_entry.get(), item_win)
        ).pack(pady=10)

    def delete_item_in_db(self, item_id, item_win):
        if not item_id:
            messagebox.showerror("Input Error", "Please enter the item ID to delete.")
            return

        try:
            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM bakery_items WHERE item_id = %s", (item_id,))
                connection.commit()

                if cursor.rowcount > 0:
                    messagebox.showinfo("Success", "Item deleted successfully!")
                else:
                    messagebox.showerror("Error", "No item found with that ID.")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

        finally:
            item_win.destroy()

    def update_item_in_db(self, item_name, price, item_id):
        item_id_value = item_id.get()
        name = item_name.get()
        price = price.get()

        if not item_id_value or not name or not price:
            messagebox.showerror("Input Error", "Please enter Item ID, Name, and Price.")
            return

        try:
            item_id_value = int(item_id_value)
            price = float(price)
            if price <= 0:
                raise ValueError("Price must be positive.")

            with mysql.connector.connect(
                host='localhost',
                user='root',
                password='P16@2007',  # Replace with your MySQL password
                database='bakery'
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("UPDATE bakery_items SET item_name = %s, price = %s WHERE item_id = %s", (name, price, item_id_value))
                connection.commit()
                if cursor.rowcount == 0:
                    messagebox.showerror("Input Error", "No item found with that ID.")
                else:
                    messagebox.showinfo("Success", "Item updated successfully!")

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

if __name__ == "__main__":
    main()