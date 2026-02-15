import sqlite3
import datetime
import database
from PyQt6.QtWidgets import QMessageBox
today = datetime.date.today().strftime("%Y-%m-%d")

DB_NAME = 'hotel_restaurant.db'

# ==========================================
# HOTEL MANAGEMENT DATABASE FUNCTIONS
# ==========================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. SETTINGS & USERS
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', '1234', 'ADMIN')")

    # 2. CATEGORIES (Added this here so get_all_categories() works)
    cursor.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE, tax_rate REAL)')
    
    # Optional: Seed default categories so categories list isn't empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO categories (name, tax_rate) VALUES (?, ?)", 
                           [('FOOD', 5.0), ('DRINKS', 12.0), ('SNACKS', 5.0), ('DESSERT', 18.0)])

    # 3. ITEMS
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY, 
        name TEXT, 
        category TEXT, 
        category_id INTEGER, 
        price REAL, 
        price_dinein REAL, 
        price_delivery REAL, 
        image_path TEXT,
        tax_rate REAL,
        FOREIGN KEY(category_id) REFERENCES categories(id))''')

    # 4. ROOMS
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
        room_number TEXT PRIMARY KEY,
        room_type TEXT, 
        price_per_night REAL,
        status TEXT DEFAULT 'AVAILABLE')''')

    # 5. TABLES
    cursor.execute('''CREATE TABLE IF NOT EXISTS dining_tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        table_number TEXT UNIQUE, 
        status TEXT DEFAULT "AVAILABLE")''')

    # 6. ORDERS
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        table_id INTEGER, 
        room_number TEXT,
        order_type TEXT, 
        status TEXT DEFAULT "OPEN", 
        order_date TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # 7. ORDER ITEMS 
    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        order_id INTEGER, 
        item_name TEXT, 
        quantity INTEGER, 
        unit_price REAL, 
        tax_rate REAL, 
        total_price REAL,
        printed_qty INTEGER DEFAULT 0, 
        notes TEXT,                     
        FOREIGN KEY(order_id) REFERENCES orders(id))''')

    conn.commit()
    conn.close()

def seed_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Check if items already exist
    try:
        cursor.execute("SELECT count(*) FROM items")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return # Data already exists, skip seeding
    except:
        pass # Table might not exist yet, allow continuation

    print("🌱 Seeding default menu...")
    
    # 2. Insert Items (Matching the new schema: Name, Category, Price)
    # Note: The new DB uses 'category' as text (e.g., 'FOOD') instead of IDs
    items = [
        ("Classic Burger", "FOOD", 150, 150, 160, 0.0),
        ("Cheese Pizza", "FOOD", 280, 280, 300, 5.0),
        ("Red Sauce Pasta", "FOOD", 220, 220, 240, 5.0),
        ("French Fries", "SNACKS", 90, 90, 100, 5.0),
        ("Coca Cola", "DRINKS", 60, 60, 65, 0.0),
        ("Cold Coffee", "DRINKS", 120, 120, 130, 12.0),
        ("Vanilla Scoop", "DESSERT", 80, 80, 90, 18.0),
        ("Brownie", "DESSERT", 150, 150, 165, 18.0),
    ]
    
    try:
        cursor.executemany("INSERT INTO items (name, category, price, price_dinein, price_delivery, tax_rate) VALUES (?, ?, ?, ?, ?, ?)", items)
        conn.commit()
        print("✅ Data Seeded Successfully.")
    except Exception as e:
        print(f"⚠️ Seeding Skipped/Error: {e}")
        
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def get_menu_items(price_mode="DINE_IN"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = """
        SELECT i.id, i.name, i.price_dinein, i.price_delivery, 
               c.name as category_name, i.image_path, i.tax_rate
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
    """
    
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    
    menu_list = []
    for row in data:
        final_price = row[3] if price_mode == "DELIVERY" else row[2]

        menu_list.append({
            "id": row[0],
            "name": row[1],
            "price": final_price,
            "category": row[4],
            "image": row[5] if row[5] else "",
            # This now pulls the specific item tax you set in Menu Manager
            "tax_rate": row[6] if row[6] is not None else 0.0 
        })
        
    return menu_list

def save_order(target_id, cart_items, order_type="DINE_IN"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    is_room = (order_type == "ROOM_SERVICE")
    
    # 1. Get or Create Order ID
    if is_room:
        cursor.execute("SELECT id FROM orders WHERE room_number = ? AND status = 'OPEN'", (target_id,))
    else:
        cursor.execute("SELECT id FROM orders WHERE table_id = ? AND status = 'OPEN'", (target_id,))
        
    row = cursor.fetchone()
    
    if row:
        order_id = row[0]
        # We clear old items to re-save the full current cart state
        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    else:
        # Create New Order
        if is_room:
            cursor.execute("INSERT INTO orders (room_number, status, order_type, order_date) VALUES (?, 'OPEN', ?, ?)", (target_id, order_type, today))
        else:
            cursor.execute("INSERT INTO orders (table_id, status, order_type, order_date) VALUES (?, 'OPEN', ?, ?)", (target_id, order_type, today))
        order_id = cursor.lastrowid

    # 2. Insert Items (With Notes & Correct Tax)
    for item in cart_items:
        printed = item.get('printed', 0) 
        total = item['price'] * item['qty']
        note = item.get('note', '') 
        
        # --- THE FIX IS HERE ---
        # Use .get('tax_rate', 5.0) instead of item['tax']
        tax_rate = item.get('tax_rate', 5.0)
        
        cursor.execute("""
            INSERT INTO order_items (order_id, item_name, quantity, unit_price, tax_rate, total_price, printed_qty, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, item['name'], item['qty'], item['price'], tax_rate, total, printed, note))
        
    if not is_room:
        print(f"DEBUG: Updating Table {target_id} to OCCUPIED") # VERIFICATION LINE
        cursor.execute("UPDATE dining_tables SET status = 'OCCUPIED' WHERE id = ?", (target_id,))

    conn.commit()
    conn.close()
    return order_id

def get_all_tables():
    """
    Fetches all tables with their status and current Total Due amount.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # This smart query joins Tables with active Orders and sums the price
    # COALESCE(SUM(...), 0) means "If no items, Total is ₹0"
    query = """
        SELECT 
            t.id, 
            t.status, 
            COALESCE(SUM(oi.total_price), 0) as total_due
        FROM dining_tables t
        LEFT JOIN orders o ON t.id = o.table_id AND o.status = 'OPEN'
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY t.id
    """
    
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data 
    # Returns list of tuples: [(1, 'OCCUPIED', 500.0), (2, 'AVAILABLE', 0.0), ...]

# --- SETTINGS & CONFIGURATION HELPERS ---

def get_setting(key, default=""):
    """Fetch a specific setting (e.g., 'restaurant_name')."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else default

def save_setting(key, value):
    """Save or update a setting."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_all_categories():
    """Get categories and their tax rates."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, tax_rate FROM categories")
    data = cursor.fetchall()
    conn.close()
    return data

def update_category_tax(cat_id, new_rate):
    """Update tax percentage for a category."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET tax_rate = ? WHERE id = ?", (new_rate, cat_id))
    conn.commit()
    conn.close()

def update_pin(role, new_pin):
    """Update the login PIN for Admin or Cashier."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # We store the PIN in the 'password' column of the users table
    cursor.execute("UPDATE users SET password = ? WHERE role = ?", (new_pin, role))
    conn.commit()
    conn.close()

def verify_pin(pin):
    """Check if a PIN exists and return the role."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE password = ?", (pin,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def get_active_order(target_id, is_room=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Select 'notes' (column index 7 now roughly, but we fetch explicitly)
    if is_room:
        query = """
            SELECT oi.id, oi.item_name, oi.quantity, oi.unit_price, oi.tax_rate, oi.printed_qty, MAX(i.id), oi.notes
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN items i ON oi.item_name = i.name
            WHERE o.room_number = ? AND o.status = 'OPEN'
            GROUP BY oi.id
        """
    else:
        query = """
            SELECT oi.id, oi.item_name, oi.quantity, oi.unit_price, oi.tax_rate, oi.printed_qty, MAX(i.id), oi.notes
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN items i ON oi.item_name = i.name
            WHERE o.table_id = ? AND o.status = 'OPEN'
            GROUP BY oi.id
        """
        
    cursor.execute(query, (target_id,))
    data = cursor.fetchall()
    conn.close()
    
    cart = []
    for row in data:
        cart.append({
            'id': row[6] if row[6] else 0, 
            'name': row[1], 
            'price': row[3], 
            'qty': row[2], 
            'tax': row[4],
            'printed': row[5],
            'note': row[7] if row[7] else "" # <--- Load Note
        })
    return cart

def checkout_table(table_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        t_id = int(table_id) # Ensure it's an integer for the query
        cursor.execute("UPDATE orders SET status='COMPLETED' WHERE table_id=? AND status='OPEN'", (t_id,))
        cursor.execute("UPDATE dining_tables SET status='AVAILABLE' WHERE id=?", (t_id,))
        conn.commit()
        print(f"✅ Table {t_id} Checked Out & Order Closed.")
    except Exception as e:
        print(f"❌ Error checking out: {e}")
    finally:
        conn.close()

def get_sales_history():
    """
    Fetches detailed sales history including Type, Table, and Item Summary.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # This query joins Orders, Tables, and Items to get a full picture
    # COALESCE(t.table_number, 'N/A') -> If table is missing (Takeout), show 'N/A'
    # GROUP_CONCAT(...) -> Combines "Burger" and "Coke" into "2x Burger, 1x Coke"
    query = """
        SELECT 
            o.id, 
            o.created_at, 
            o.order_type,
            COALESCE(t.table_number, '-'), 
            GROUP_CONCAT(oi.quantity || 'x ' || oi.item_name, ', '),
            SUM(oi.total_price)
        FROM orders o 
        LEFT JOIN dining_tables t ON o.table_id = t.id
        JOIN order_items oi ON o.id = oi.order_id 
        WHERE o.status = 'CLOSED' 
        GROUP BY o.id 
        ORDER BY o.created_at DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data 
    # Returns: [(ID, Date, Type, Table, "2x Burger, 1x Coke", TotalPrice), ...]

def save_takeout_order(cart_items):
    """Saves a Takeout order directly to history (Closed status)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Create Order (Type=TAKEOUT, Status=CLOSED)
    cursor.execute("INSERT INTO orders (order_type, status) VALUES ('TAKEOUT', 'CLOSED')")
    order_id = cursor.lastrowid
    
    # 2. Insert Items
    for item in cart_items:
        total = item['price'] * item['qty']
        
        # --- THE FIX: Use .get('tax_rate', 5.0) instead of item['tax'] ---
        tax_val = item.get('tax_rate', 5.0)
        
        cursor.execute("""
            INSERT INTO order_items (order_id, item_name, quantity, unit_price, tax_rate, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, item['name'], item['qty'], item['price'], tax_val, total))
        
    conn.commit()
    conn.close()
    return order_id

def save_delivery_order(cart_items, name, phone, address):
    """Saves a Delivery order with customer details."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Create Order
    cursor.execute("""
        INSERT INTO orders (order_type, status, customer_name, customer_phone, customer_address) 
        VALUES ('DELIVERY', 'CLOSED', ?, ?, ?)
    """, (name, phone, address))
    
    order_id = cursor.lastrowid
    
    # 2. Insert Items
    for item in cart_items:
        total = item['price'] * item['qty']
        
        tax_rate = item.get('tax_rate', 5.0) 
        
        cursor.execute("""
            INSERT INTO order_items (order_id, item_name, quantity, unit_price, tax_rate, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, item['name'], item['qty'], item['price'], tax_rate, total))
        
    conn.commit()
    conn.close()
    return order_id

def add_category(name, tax_rate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, tax_rate) VALUES (?, ?)", (name, tax_rate))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def delete_category(cat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()

# Added =5.0 to tax_rate to make it optional
def add_item(name, p_dine, p_del, category_name, img_path, tax_rate=5.0):
    """Inserts a new item into the items table based on GUI input."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Get the category_id from the category_name
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    row = cursor.fetchone()
    cat_id = row[0] if row else None
    
    # 2. Insert into items table matching your schema
    query = """
        INSERT INTO items (name, category, category_id, price, price_dinein, price_delivery, image_path, tax_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Values tuple now matches the 8 columns in your items table
    cursor.execute(query, (name, category_name, cat_id, p_dine, p_dine, p_del, img_path, tax_rate))
    
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def mark_kot_printed(target_id, is_room=False):
    """
    Updates the printed_qty to match the actual quantity.
    target_id: Table ID or Room Number
    is_room: Boolean flag to check if it's a room
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Find the Order ID (Check Room or Table)
    if is_room:
        cursor.execute("SELECT id FROM orders WHERE room_number = ? AND status = 'OPEN'", (target_id,))
    else:
        cursor.execute("SELECT id FROM orders WHERE table_id = ? AND status = 'OPEN'", (target_id,))
        
    row = cursor.fetchone()
    
    if row:
        order_id = row[0]
        # 2. Set printed_qty = quantity (Syncs them so they don't print again)
        cursor.execute("UPDATE order_items SET printed_qty = quantity WHERE order_id = ?", (order_id,))
        conn.commit()
        
    conn.close()

# ==========================================
# ROOM MANAGEMENT DATABASE FUNCTIONS
# ==========================================

def init_room_db():
    """Creates tables for Rooms and Bookings."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Rooms Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT, -- e.g. Single, Double, Suite
            price_per_night REAL,
            status TEXT DEFAULT 'AVAILABLE' -- AVAILABLE, OCCUPIED, DIRTY
        )
    ''')
    
    # 2. Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT,
            guest_name TEXT,
            guest_phone TEXT,
            check_in_date TEXT,
            check_out_date TEXT, -- Null until they leave
            status TEXT DEFAULT 'ACTIVE', -- ACTIVE, CHECKED_OUT
            FOREIGN KEY(room_number) REFERENCES rooms(room_number)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_room(room_num, r_type, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms (room_number, room_type, price_per_night) VALUES (?, ?, ?)", 
                       (room_num, r_type, price))
        conn.commit()
        return True
    except:
        return False # Room probably exists
    finally:
        conn.close()

def get_all_rooms():
    """Returns [(room_num, type, price, status, guest_name), ...]"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # We join with bookings to see WHO is in the room if it is occupied
    query = """
        SELECT r.room_number, r.room_type, r.price_per_night, r.status, b.guest_name
        FROM rooms r
        LEFT JOIN bookings b ON r.room_number = b.room_number AND b.status = 'ACTIVE'
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def get_all_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
        SELECT 
            t.table_number,               -- index 0 (String for GUI list/buttons)
            t.status,                     -- index 1
            COALESCE(SUM(oi.total_price), 0), -- index 2
            t.id                          -- index 3 (Integer for save_order logic)
        FROM dining_tables t
        LEFT JOIN orders o ON t.id = o.table_id AND o.status = 'OPEN'
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY t.id
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def check_in_guest(room_num, name, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Create Booking
    cursor.execute("INSERT INTO bookings (room_number, guest_name, guest_phone, check_in_date) VALUES (?, ?, ?, ?)",
                   (room_num, name, phone, now))
    
    # 2. Update Room Status
    cursor.execute("UPDATE rooms SET status = 'OCCUPIED' WHERE room_number = ?", (room_num,))
    
    conn.commit()
    conn.close()

def check_out_guest(room_num):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Close Booking
    cursor.execute("UPDATE bookings SET status = 'CHECKED_OUT', check_out_date = ? WHERE room_number = ? AND status = 'ACTIVE'", (now, room_num))
    
    # 2. Free Room
    cursor.execute("UPDATE rooms SET status = 'AVAILABLE' WHERE room_number = ?", (room_num,))
    
    conn.commit()
    conn.close()

def get_room_food_total(room_num):
    """Returns total cost of pending food orders for a room."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(oi.total_price), 0)
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.room_number = ? AND o.status = 'OPEN'
    """, (room_num,))
    
    total = cursor.fetchone()[0]
    conn.close()
    return total

def checkout_room_orders(room_num):
    """Marks all open food orders for this room as CLOSED."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'CLOSED' WHERE room_number = ? AND status = 'OPEN'", (room_num,))
    conn.commit()
    conn.close()

def get_room_order_items(room_num):
    """Fetches the list of all food items ordered by this room."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT oi.item_name, SUM(oi.quantity), oi.unit_price, SUM(oi.total_price)
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.room_number = ? AND o.status = 'OPEN'
        GROUP BY oi.item_name
    """, (room_num,))
    
    # Returns list of tuples: [('Burger', 2, 100, 200), ('Coke', 1, 40, 40)]
    data = cursor.fetchall()
    conn.close()
    return data

# --- SETTINGS MANAGEMENT ---
def get_setting(key, default=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def save_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# --- TABLE MANAGEMENT ---
def add_custom_table(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # We insert into 'table_number' (the string column) 
        # and let 'id' auto-increment itself.
        cursor.execute("INSERT INTO dining_tables (table_number, status) VALUES (?, 'AVAILABLE')", (name,))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error adding table: {e}")
        success = False
    finally:
        conn.close()
    return success

def delete_table(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dining_tables WHERE id=?", (name,))
    conn.commit()
    conn.close()

# --- ROOM MANAGEMENT ---
def add_custom_room(r_num, r_type, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms (room_number, room_type, price_per_night, status) VALUES (?, ?, ?, 'AVAILABLE')", (r_num, r_type, price))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success

def delete_room(r_num):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE room_number=?", (r_num,))
    conn.commit()
    conn.close()

# --- ADMIN HELPERS ---

def get_all_items():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_dinein, price_delivery, category, image_path, tax_rate FROM items")
    data = cursor.fetchall()
    conn.close()
    return data

def get_daily_report(date_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    report = {'food': 0.0, 'rooms': 0.0, 'halls': 0.0, 'total': 0.0}
    
    # Matches your orders table column 'order_date'
    cursor.execute("""
        SELECT COALESCE(SUM(oi.total_price), 0)
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.order_date = ?
    """, (date_str,))
    report['food'] = cursor.fetchone()[0]
    
    # Matches your rooms table column 'price_per_night'
    cursor.execute("""
        SELECT COALESCE(SUM(r.price_per_night), 0)
        FROM bookings b
        JOIN rooms r ON b.room_number = r.room_number
        WHERE b.check_in_date LIKE ?
    """, (f"{date_str}%",))
    report['rooms'] = cursor.fetchone()[0]
    
    report['total'] = report['food'] + report['rooms']
    conn.close()
    return report

