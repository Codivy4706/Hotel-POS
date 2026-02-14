import database
import sys

def main():
    # Setup
    database.init_db()
    database.seed_data()
    
    menu_options = {
        '1': ("New Table Order",  restaurant_menu),
        '2': ("View Table Bill",  view_bill_menu),
        '3': ("Checkout Table",   checkout_table_menu),
        '4': ("Check-In Guest",   check_in_menu),
        '5': ("Room Service",     room_service_menu),
        '6': ("Checkout Guest",   checkout_guest_menu),
        '7': ("ADMIN: Add Item",  add_item_menu),
        '8': ("SYNC: Download Bookings", sync_menu), 
        '9': ("Exit",             sys.exit)    
    }

    while True:
        print("\n=== HOTEL POS SYSTEM ===")
        for key, value in menu_options.items():
            print(f"{key}. {value[0]}")
        
        choice = input("Select Option: ")
        
        if choice in menu_options:
            if choice == '9': break
            try:
                menu_options[choice][1]() 
            except Exception as e:
                print(f"[ERROR] {e}")
        else:
            print("Invalid selection.")

# --- SUB MENUS ---

def restaurant_menu():
    t = input("Table No: ")
    
    # FETCH REAL MENU FROM DB
    import sqlite3
    conn = sqlite3.connect('hotel_restaurant.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM items")
    items = cursor.fetchall()
    
    print("\n--- CURRENT MENU ---")
    for item in items:
        print(f"{item[0]}. {item[1]} (Rs.{item[2]})")
    conn.close()
    
    i = int(input("Item ID: "))
    q = int(input("Qty: "))
    database.create_table_order(t, i, q)

def view_bill_menu():
    database.get_table_bill(input("Table No: "))

def checkout_table_menu():
    database.checkout_table(input("Table No: "))

def check_in_menu():
    database.check_in_guest(input("Name: "), input("Phone: "), input("Room No: "))

def room_service_menu():
    r = input("Room No: ")
    print("1. Burger (Rs.10) | 2. Pasta (Rs.12) | 3. Coke (Rs.3)")
    database.order_to_room(r, int(input("Item ID: ")), int(input("Qty: ")))

def checkout_guest_menu():
    database.checkout_guest(input("Room No: "))

def add_item_menu():
    print("\n--- ADD NEW MENU ITEM ---")
    name = input("Item Name : ")
    cat = input("Category (FOOD/BEVERAGE): ").upper()
    price = input("Price: ")
    database.add_new_item(name, cat, price)

def sync_menu():
    database.sync_online_bookings()

if __name__ == "__main__":
    main()