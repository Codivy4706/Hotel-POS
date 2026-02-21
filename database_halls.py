import sqlite3

DB_NAME = "hotel_restaurant.db"

def init_hall_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Halls Table (e.g., "Grand Ballroom", "Poolside")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            capacity INTEGER,
            price_per_day REAL
        )
    ''')
    
    # 2. Hall Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hall_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hall_id INTEGER,
            customer_name TEXT,
            phone TEXT,
            event_date TEXT, -- YYYY-MM-DD
            event_type TEXT, -- Wedding, Birthday, Conference
            services TEXT,   -- "DJ, Decoration, Food"
            total_price REAL,
            status TEXT DEFAULT 'CONFIRMED',
            FOREIGN KEY(hall_id) REFERENCES halls(id)
        )
    ''')
    
    # Add dummy halls if empty
    cursor.execute("SELECT count(*) FROM halls")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO halls (name, capacity, price_per_day) VALUES ('Grand Ballroom', 500, 20000)")
        cursor.execute("INSERT INTO halls (name, capacity, price_per_day) VALUES ('Poolside Area', 100, 10000)")
        cursor.execute("INSERT INTO halls (name, capacity, price_per_day) VALUES ('Conference Hall', 50, 5000)")
        
    conn.commit()
    conn.close()
    print("✅ Hall Database Ready.")

def get_all_halls():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM halls")
    data = cursor.fetchall()
    conn.close()
    return data

def book_hall(hall_id, name, phone, date, event_type, services, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if already booked
    cursor.execute("SELECT * FROM hall_bookings WHERE hall_id = ? AND event_date = ?", (hall_id, date))
    if cursor.fetchone():
        conn.close()
        return False # Already Booked
        
    cursor.execute("""
        INSERT INTO hall_bookings (hall_id, customer_name, phone, event_date, event_type, services, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (hall_id, name, phone, date, event_type, services, price))
    
    conn.commit()
    conn.close()
    return True

def get_bookings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, h.name, b.customer_name, b.event_date, b.event_type, b.total_price 
        FROM hall_bookings b 
        JOIN halls h ON b.hall_id = h.id
        ORDER BY b.event_date DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data