from PyQt6.QtCore import Qt, QSize, QTimer 
from PyQt6.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGridLayout, QMessageBox, QDialog, QWidget, QGroupBox,
    QScrollArea, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QHeaderView, QTabWidget, QFormLayout, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QCheckBox, QInputDialog, QListWidget, QStackedWidget, QToolButton, QAbstractItemView
)
import sys
import datetime
import os
import database
import printer
import database_halls
import shutil
import webbrowser

# ==========================================
# 1. HELPER CLASSES (TOP)
# ==========================================

class CustomerDialog(QDialog):
    """Popup to get customer details for Delivery."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delivery Details")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white; color: black;")
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        self.inp_name = QLineEdit()
        self.inp_phone = QLineEdit()
        self.inp_addr = QTextEdit()
        self.inp_addr.setFixedHeight(80)
        
        layout.addRow("Customer Name:", self.inp_name)
        layout.addRow("Phone Number:", self.inp_phone)
        layout.addRow("Address:", self.inp_addr)
        
        btn_ok = QPushButton("CONFIRM DELIVERY")
        btn_ok.setFixedHeight(50)
        btn_ok.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        layout.addRow(btn_ok)
        
    def get_data(self):
        return {
            'name': self.inp_name.text(),
            'phone': self.inp_phone.text(),
            'address': self.inp_addr.toPlainText()
        }

class OrderWindow(QDialog):
    """Wrapper for the POS Interface."""
    def __init__(self, target_id, is_room=False, parent=None):
        super().__init__(parent)
        label = f"Room {target_id}" if is_room else f"Table {target_id}"
        self.setWindowTitle(f"{label} - Order Management")
        self.resize(1200, 750)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Pass 'is_room' flag to POSInterface
        mode = "ROOM_SERVICE" if is_room else "DINE_IN"
        self.ui = POSInterface(mode, table_num=target_id, parent=self)
        layout.addWidget(self.ui)

# ==========================================
# 2. LOGIN SCREEN
# ==========================================
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        lbl = QLabel("ENTER PIN")
        lbl.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        self.pin_display = QLineEdit()
        self.pin_display.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_display.setStyleSheet("font-size: 30px; padding: 10px; color: black; background-color: white;")
        self.pin_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pin_display)

        grid = QGridLayout()
        buttons = [('1',0,0),('2',0,1),('3',0,2),('4',1,0),('5',1,1),('6',1,2),('7',2,0),('8',2,1),('9',2,2),('C',3,0),('0',3,1),('Login',3,2)]
        for btn_text, r, c in buttons:
            btn = QPushButton(btn_text)
            btn.setFixedSize(80, 80)
            btn.setStyleSheet("QPushButton { background-color: #34495e; font-size: 18px; border-radius: 10px; } QPushButton:hover { background-color: #1abc9c; }")
            if btn_text == 'Login':
                btn.setStyleSheet("background-color: #27ae60; border-radius: 10px; font-weight: bold;")
                btn.clicked.connect(self.check_login)
            elif btn_text == 'C':
                btn.setStyleSheet("background-color: #c0392b; border-radius: 10px;")
                btn.clicked.connect(self.clear_pin)
            else:
                btn.clicked.connect(lambda ch, t=btn_text: self.add_digit(t))
            grid.addWidget(btn, r, c)
        layout.addLayout(grid)
        self.user_role = None

    def add_digit(self, digit): self.pin_display.setText(self.pin_display.text() + digit)

    def clear_pin(self): self.pin_display.clear()

    def check_login(self):
        pin = self.pin_display.text()
        role = database.verify_pin(pin)
        if role:
            self.user_role = role
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid PIN!")
            self.pin_display.clear()

# ==========================================
# 3. SETTINGS & MENU MANAGER
# ==========================================
class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Settings")
        self.resize(900, 600) # Made wider for new columns
        self.setStyleSheet("background-color: #f0f0f0; color: black; font-size: 14px;")
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Restaurant Info
        self.tab_info = QWidget()
        self.setup_info_tab()
        self.tabs.addTab(self.tab_info, "🏢 Info")
        
        # Tab 2: Menu Manager
        self.tab_menu = QWidget()
        self.setup_menu_tab()
        self.tabs.addTab(self.tab_menu, "🍔 Menu Manager")
        
        # Tab 3: Security
        self.tab_sec = QWidget()
        self.setup_security_tab()
        self.tabs.addTab(self.tab_sec, "🔐 Security")

    def setup_info_tab(self):
        l = QFormLayout()
        self.tab_info.setLayout(l)
        self.inp_name = QLineEdit(database.get_setting("restaurant_name"))
        self.inp_addr = QLineEdit(database.get_setting("address"))
        self.inp_phone = QLineEdit(database.get_setting("phone"))
        
        l.addRow("Name:", self.inp_name)
        l.addRow("Address:", self.inp_addr)
        l.addRow("Phone:", self.inp_phone)
        
        btn = QPushButton("Save Info")
        btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        btn.clicked.connect(self.save_info)
        l.addRow(btn)

    def save_info(self):
        database.save_setting("restaurant_name", self.inp_name.text())
        database.save_setting("address", self.inp_addr.text())
        database.save_setting("phone", self.inp_phone.text())
        QMessageBox.information(self, "Saved", "Info Updated!")

    def setup_menu_tab(self):
        layout = QHBoxLayout()
        self.tab_menu.setLayout(layout)
        
        # Left: Categories
        left = QWidget()
        l_layout = QVBoxLayout()
        left.setLayout(l_layout)
        l_layout.addWidget(QLabel("<b>CATEGORIES</b>"))
        
        self.cat_list = QTableWidget()
        self.cat_list.setColumnCount(3)
        self.cat_list.setHorizontalHeaderLabels(["ID", "Name", "Tax%"])
        self.cat_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        l_layout.addWidget(self.cat_list)
        
        form_cat = QHBoxLayout()
        self.inp_cat_name = QLineEdit(); self.inp_cat_name.setPlaceholderText("New Category")
        self.inp_cat_tax = QLineEdit(); self.inp_cat_tax.setPlaceholderText("Tax %")
        self.inp_cat_tax.setFixedWidth(50)
        btn_add_cat = QPushButton("➕"); btn_add_cat.clicked.connect(self.add_cat)
        form_cat.addWidget(self.inp_cat_name); form_cat.addWidget(self.inp_cat_tax); form_cat.addWidget(btn_add_cat)
        l_layout.addLayout(form_cat)
        
        btn_del_cat = QPushButton("🗑️ Delete Category")
        btn_del_cat.setStyleSheet("color: red;")
        btn_del_cat.clicked.connect(self.del_cat)
        l_layout.addWidget(btn_del_cat)
        
        layout.addWidget(left, stretch=1)
        
        # Right: Items
        right = QWidget()
        r_layout = QVBoxLayout()
        right.setLayout(r_layout)
        r_layout.addWidget(QLabel("<b>MENU ITEMS</b>"))
        
        self.item_list = QTableWidget()
        self.item_list.setColumnCount(4) # ID, Name, Price, Category
        self.item_list.setHorizontalHeaderLabels(["ID", "Name", "Price (Dine)", "Category"])
        self.item_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        r_layout.addWidget(self.item_list)
        
        # Add Item Form
        form_item = QGridLayout()
        self.inp_item_name = QLineEdit(); self.inp_item_name.setPlaceholderText("Item Name")
        
        # NEW: Two Price Fields
        self.inp_price_dine = QLineEdit(); self.inp_price_dine.setPlaceholderText("Dine Price")
        self.inp_price_del = QLineEdit(); self.inp_price_del.setPlaceholderText("Del. Price")
        
        self.combo_cat = QComboBox()
        
        btn_add_item = QPushButton("➕ Add Item")
        btn_add_item.setStyleSheet("background-color: #27ae60; color: white;")
        btn_add_item.clicked.connect(self.add_item)
        
        form_item.addWidget(self.inp_item_name, 0, 0)
        form_item.addWidget(self.combo_cat, 0, 1)
        form_item.addWidget(self.inp_price_dine, 1, 0)
        form_item.addWidget(self.inp_price_del, 1, 1)
        form_item.addWidget(btn_add_item, 2, 0, 1, 2)
        r_layout.addLayout(form_item)
        
        btn_del_item = QPushButton("🗑️ Delete Selected Item")
        btn_del_item.setStyleSheet("color: red;")
        btn_del_item.clicked.connect(self.del_item)
        r_layout.addWidget(btn_del_item)
        
        layout.addWidget(right, stretch=2)
        self.load_menu_data()

    def load_menu_data(self):
        # 1. Load Categories
        cats = database.get_all_categories()
        self.cat_list.setRowCount(len(cats))
        self.combo_cat.clear()
        
        for r, (cid, name, tax) in enumerate(cats):
            self.cat_list.setItem(r, 0, QTableWidgetItem(str(cid)))
            self.cat_list.setItem(r, 1, QTableWidgetItem(name))
            self.cat_list.setItem(r, 2, QTableWidgetItem(str(tax)))
            self.combo_cat.addItem(f"{cid}: {name}", cid)
            
        # 2. Load Items (FIXED UNPACKING HERE)
        # We request DINE_IN prices to show in the list
        items = database.get_menu_items("DINE_IN") 
        self.item_list.setRowCount(len(items))
        
        for r, item in enumerate(items):
            # --- FIX: UNPACK 6 VALUES ---
            iid, name, cat_name, price, tax, img_path = item
            
            self.item_list.setItem(r, 0, QTableWidgetItem(str(iid)))
            self.item_list.setItem(r, 1, QTableWidgetItem(name))
            self.item_list.setItem(r, 2, QTableWidgetItem(str(price)))
            self.item_list.setItem(r, 3, QTableWidgetItem(cat_name))

    def add_cat(self):
        name = self.inp_cat_name.text()
        try: tax = float(self.inp_cat_tax.text())
        except: tax = 5.0
        if name:
            database.add_category(name, tax)
            self.inp_cat_name.clear()
            self.load_menu_data()

    def del_cat(self):
        row = self.cat_list.currentRow()
        if row >= 0:
            cid = int(self.cat_list.item(row, 0).text())
            database.delete_category(cid)
            self.load_menu_data()

    def add_item(self):
        """Adds item to DB and triggers a global refresh in all tabs."""
        name = self.inp_name.text() # Assumed variable name from your previous context
        
        # Logic to handle price input (cleaner)
        p_dine = self.inp_price_dine.text()
        p_del = self.inp_price_del.text()
        
        if not name or not p_dine: 
            return
        if not p_del: 
            p_del = p_dine 
        
        # Get Category ID safely
        cat_idx = self.inp_cat.currentIndex()
        if cat_idx == -1: return
        cat_id = self.inp_cat.itemData(cat_idx) # Ensure you set itemData when populating!
        
        try:
            # 1. Save to Database
            # We use 0.0 for tax if input is empty
            tax_val = float(self.inp_tax.text()) if self.inp_tax.text() else 5.0
            
            # Using the image path from the input field
            img_path = self.inp_image.text()
            
            database.add_item(name, cat_id, float(p_dine), float(p_del), img_path, tax_val)
            
            # 2. Clear Inputs
            self.inp_name.clear()
            self.inp_price_dine.clear()
            self.inp_price_del.clear()
            self.inp_image.clear()
            
            # 3. Refresh Admin Table
            self.refresh_all_data()
            
            # 4. GLOBAL SYNC: The missing link!
            # This finds the Main Window and tells it to update Takeaway/Delivery tabs
            if self.window() and hasattr(self.window(), 'sync_all_pos_menus'):
                self.window().sync_all_pos_menus()
                
            QMessageBox.information(self, "Success", f"{name} added and synced to all tabs!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            
    def del_item(self):
        row = self.item_list.currentRow()
        if row >= 0:
            iid = int(self.item_list.item(row, 0).text())
            database.delete_item(iid)
            self.load_menu_data()

    def setup_security_tab(self):
        l = QVBoxLayout()
        self.tab_sec.setLayout(l)
        l.addWidget(QLabel("Change PINs here (Logic same as before)"))

class ReportsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Business Analytics")
        self.resize(600, 400)
        self.setStyleSheet("background-color: white; font-size: 14px;")
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # --- Date Selection ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Select Date:"))
        
        self.inp_date = QLineEdit()
        self.inp_date.setText(datetime.date.today().strftime("%Y-%m-%d")) # Default Today
        top_layout.addWidget(self.inp_date)
        
        btn_refresh = QPushButton("🔄 Generate Report")
        btn_refresh.setStyleSheet("background-color: #3498db; color: white;")
        btn_refresh.clicked.connect(self.load_report)
        top_layout.addWidget(btn_refresh)
        
        layout.addLayout(top_layout)
        
        # --- Cards Layout ---
        self.card_layout = QGridLayout()
        layout.addLayout(self.card_layout)
        
        # Initial Load
        self.load_report()
        
    def create_card(self, title, amount, color, row, col):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px;")
        l = QVBoxLayout()
        frame.setLayout(l)
        
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Arial", 12))
        
        lbl_amt = QLabel(f"₹{amount:,.2f}")
        lbl_amt.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        l.addWidget(lbl_title)
        l.addWidget(lbl_amt)
        self.card_layout.addWidget(frame, row, col)

    def load_report(self):
        # Clear old cards
        for i in reversed(range(self.card_layout.count())): 
            self.card_layout.itemAt(i).widget().setParent(None)
            
        date_str = self.inp_date.text()
        data = database.get_daily_report(date_str)
        
        # 1. Total Revenue (Big Card)
        self.create_card("TOTAL REVENUE", data['total'], "#2c3e50", 0, 0) # Dark Blue
        
        # 2. Food Sales
        self.create_card("🍔 Food Sales", data['food'], "#e67e22", 1, 0) # Orange
        
        # 3. Room Revenue
        self.create_card("🛏️ Room Revenue", data['rooms'], "#27ae60", 1, 1) # Green
        
        # 4. Hall/Events
        self.create_card("🎉 Events", data['halls'], "#8e44ad", 2, 0) # Purple

# ==========================================
# 4. TABBED INTERFACE COMPONENTS
# ==========================================

class DineInTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # 1. Add Title & Refresh Button (Optional but helpful)
        top_row = QHBoxLayout()
        lbl = QLabel("DINING TABLES")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh_tables)
        top_row.addWidget(lbl)
        top_row.addWidget(btn_refresh)
        self.layout.addLayout(top_row)

        # 2. CREATE THE GRID LAYOUT (The part that was missing)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.container = QWidget()
        self.grid_layout = QGridLayout() # <--- Created here so refresh_tables finds it
        self.container.setLayout(self.grid_layout)
        
        scroll.setWidget(self.container)
        self.layout.addWidget(scroll)

        # 3. NOW it is safe to call this
        self.refresh_tables()

    def refresh_tables(self):
        # 1. Clear existing buttons safely
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            
        tables = database.get_all_tables() 
        
        row, col = 0, 0
        for table in tables:
            t_id = table[0]
            status = str(table[1]).upper().strip()
            total_due = table[2] if len(table) > 2 else 0.0
            
            # Base style for all table buttons
            base_style = """
                QPushButton {
                    border-radius: 12px;
                    color: white;
                    font-family: 'Segoe UI Semibold', sans-serif;
                    border: none;
                    text-align: center;
                }
            """
            
            if status == "OCCUPIED" or total_due > 0:
                btn_text = f"Table {t_id}\n₹ {int(total_due)}"
                # Material Red: Normal #EF5350, Hover #D32F2F (Solid dark red)
                theme_style = """
                    QPushButton { background-color: #EF5350; font-size: 16px; }
                    QPushButton:hover { background-color: #D32F2F; }
                """
                shadow_color = QColor(239, 83, 80, 80)
            else:
                btn_text = f"Table {t_id}"
                # Material Green: Normal #66BB6A, Hover #388E3C (Solid dark green)
                theme_style = """
                    QPushButton { background-color: #66BB6A; font-size: 20px; }
                    QPushButton:hover { background-color: #388E3C; }
                """
                shadow_color = QColor(102, 187, 106, 80)

            btn = QPushButton(btn_text)
            btn.setFixedSize(150, 100)
            btn.setStyleSheet(base_style + theme_style)
            
            # Subtle shadow to give it that floating feel
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(shadow_color)
            btn.setGraphicsEffect(shadow)
            
            # Connect the click event
            btn.clicked.connect(lambda checked, t=t_id: self.open_table(t))
            
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3: 
                col = 0
                row += 1
    
    def open_table(self, table_id):
        self.dlg = POSInterface("DINE_IN", table_num=table_id, tab_ref=self)
        self.dlg.setWindowTitle(f"Table {table_id} Order")
        self.dlg.resize(1250, 700) 
        self.dlg.setWindowFlags(Qt.WindowType.Window) 
        self.dlg.show()

class RoomsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 1. TOP HEADER (Matches DineInTab style)
        top_row = QHBoxLayout()
        lbl = QLabel("HOTEL ROOMS")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        btn_refresh = QPushButton("🔄 Refresh Rooms")
        btn_refresh.setFixedWidth(150)
        btn_refresh.clicked.connect(self.refresh_rooms)
        
        top_row.addWidget(lbl)
        top_row.addStretch()
        top_row.addWidget(btn_refresh)
        self.layout.addLayout(top_row)

        # 2. SCROLLABLE GRID (Matches DineInTab background)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #f5f6f7;") 
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #f5f6f7;")
        self.grid_layout = QGridLayout()
        self.container.setLayout(self.grid_layout)
        
        scroll.setWidget(self.container)
        self.layout.addWidget(scroll)

        # 3. INITIAL LOAD
        self.refresh_rooms()

    def refresh_rooms(self):
        """Clears and redraws the Room grid using Table Book styles."""
        # Clear existing buttons safely
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            
        # Data: (room_num, type, price, status, guest_name)
        rooms = database.get_all_rooms() 
        
        row, col = 0, 0
        for r_num, r_type, price, status, guest in rooms:
            
            # Formatting Text & Colors based on Table Tab Logic
            if status == "AVAILABLE":
                color = "#66BB6A" # Material Green
                hover_color = "#388E3C"
                shadow_color = QColor(102, 187, 106, 80)
                btn_text = f"Room {r_num}\n{r_type}\n₹{int(price)}/night\n\nAVAILABLE"
            else:
                color = "#EF5350" # Material Red
                hover_color = "#D32F2F"
                shadow_color = QColor(239, 83, 80, 80)
                # Show guest name on red buttons for better UX
                btn_text = f"Room {r_num}\n{guest}\n\nOCCUPIED"

            btn = QPushButton(btn_text)
            btn.setFixedSize(190, 140)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; color: white; border-radius: 12px;
                    font-weight: bold; font-size: 13px; border: none; text-align: center;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """)

            # Apply identical shadow effect from DineInTab
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(shadow_color)
            btn.setGraphicsEffect(shadow)

            # Click Handlers
            btn.clicked.connect(lambda ch, x=r_num, s=status: self.handle_room_click(x, s))
            
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3: # 4 columns like your table grid
                col = 0
                row += 1

    def handle_room_click(self, room_num, status):
        if status == "AVAILABLE":
            self.show_checkin_dialog(room_num)
        else:
            self.show_occupied_options(room_num)

    def show_checkin_dialog(self, room_num):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Check In - Room {room_num}")
        dlg.setFixedSize(300, 200)
        layout = QFormLayout(dlg)
        
        inp_name = QLineEdit()
        inp_phone = QLineEdit()
        layout.addRow("Guest Name:", inp_name)
        layout.addRow("Phone:", inp_phone)
        
        btn_checkin = QPushButton("✅ CHECK IN")
        btn_checkin.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_checkin.clicked.connect(lambda: self.process_checkin(dlg, room_num, inp_name.text(), inp_phone.text()))
        layout.addRow(btn_checkin)
        dlg.exec()

    def process_checkin(self, dlg, room_num, name, phone):
        if not name: return
        database.check_in_guest(room_num, name, phone)
        dlg.accept()
        self.refresh_rooms()
        QMessageBox.information(self, "Success", f"Room {room_num} Checked In!")

    def show_occupied_options(self, room_num):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Room {room_num} Management")
        msg.setText(f"Guest is in Room {room_num}.\nWhat would you like to do?")
        
        btn_food = msg.addButton("🍽️ Room Service", QMessageBox.ButtonRole.ActionRole)
        btn_checkout = msg.addButton("💰 Check Out & Bill", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        if msg.clickedButton() == btn_food:
            self.open_room_service(room_num)
        elif msg.clickedButton() == btn_checkout:
            self.process_checkout(room_num)

    def open_room_service(self, room_num):
        self.dlg = POSInterface("ROOM_SERVICE", table_num=room_num, tab_ref=self)
        self.dlg.setWindowTitle(f"Room Service - Room {room_num}")
        self.dlg.resize(1250, 700) 
        self.dlg.setWindowFlags(Qt.WindowType.Window) 
        self.dlg.show()

    def process_checkout(self, room_num):
        # 1. Gather Room Data for pricing
        room_data = database.get_all_rooms()
        price_per_night = 0
        for r in room_data:
            if str(r[0]) == str(room_num):
                price_per_night = r[2]
                break
        
        # 2. FIX: Fetch full Guest Details (Name, Phone, Check-in)
        guest_details = database.get_active_booking_details(room_num)
        if not guest_details:
            QMessageBox.warning(self, "Error", "No active booking found for this room!")
            return
            
        guest_name, guest_phone, check_in_date = guest_details
        
        # 3. Get Food Total
        food_items = database.get_room_order_items(room_num)
        food_total = sum(item[3] for item in food_items)
        
        # 4. Checkout Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Checkout & Payment")
        v_layout = QVBoxLayout(dlg)
        v_layout.addWidget(QLabel(f"<b>Guest:</b> {guest_name}"))
        v_layout.addWidget(QLabel(f"Room Charges: ₹{price_per_night}"))
        v_layout.addWidget(QLabel(f"Food Charges: ₹{food_total}"))
        v_layout.addWidget(QLabel(f"<b>Total: ₹{price_per_night + food_total}</b>"))
        
        combo_pay = QComboBox()
        combo_pay.addItems(["CASH", "UPI / QR", "CARD"])
        v_layout.addWidget(QLabel("Payment Mode:"))
        v_layout.addWidget(combo_pay)
        
        btn_pay = QPushButton("🖨️ Generate Invoice & Checkout")
        btn_pay.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_pay.clicked.connect(dlg.accept)
        v_layout.addWidget(btn_pay)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # 5. Finalize: Passing the full guest_details tuple now!
            printer.generate_room_bill(
                room_num, 
                guest_details, 
                food_items, 
                price_per_night, 
                combo_pay.currentText()
            )
            
            # Cleanup database
            database.checkout_room_orders(room_num)
            database.check_out_guest(room_num)
            self.refresh_rooms()

class PartyTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        # --- LEFT: Booking Form ---
        left_frame = QFrame()
        left_layout = QFormLayout()
        left_frame.setLayout(left_layout)
        
        self.combo_hall = QComboBox()
        self.load_halls()
        
        self.inp_name = QLineEdit()
        self.inp_phone = QLineEdit()
        self.inp_date = QLineEdit()
        self.inp_date.setPlaceholderText("YYYY-MM-DD")
        self.inp_type = QComboBox()
        self.inp_type.addItems(["Wedding", "Birthday", "Conference", "Party"])
        
        # Services (Checkboxes)
        self.chk_dj = QCheckBox("DJ Sound (₹5000)")
        self.chk_food = QCheckBox("Catering (Per Plate logic later)")
        self.chk_deco = QCheckBox("Decoration (₹2000)")
        
        btn_book = QPushButton("📅 Book Event")
        btn_book.setStyleSheet("background-color: #8e44ad; color: white; padding: 10px;")
        btn_book.clicked.connect(self.book_event)
        
        left_layout.addRow(QLabel("<b>NEW BOOKING</b>"))
        left_layout.addRow("Select Hall:", self.combo_hall)
        left_layout.addRow("Client Name:", self.inp_name)
        left_layout.addRow("Phone:", self.inp_phone)
        left_layout.addRow("Date:", self.inp_date)
        left_layout.addRow("Event Type:", self.inp_type)
        left_layout.addRow(self.chk_dj)
        left_layout.addRow(self.chk_deco)
        left_layout.addRow(self.chk_food)
        left_layout.addRow(btn_book)
        
        self.layout.addWidget(left_frame, stretch=1)
        
        # --- RIGHT: Upcoming Bookings List ---
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("<b>UPCOMING EVENTS</b>"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Hall", "Client", "Date", "Type", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.table)
        
        self.refresh_bookings()
        self.layout.addWidget(right_frame, stretch=2)

    def load_halls(self):
        halls = database_halls.get_all_halls()
        for h in halls:
            # h: (id, name, capacity, price)
            self.combo_hall.addItem(f"{h[1]} (Cap: {h[2]}) - ₹{h[3]}", h)

    def book_event(self):
        idx = self.combo_hall.currentIndex()
        if idx == -1: return
        hall_data = self.combo_hall.itemData(idx) # (id, name, cap, price)
        
        hall_id = hall_data[0]
        base_price = hall_data[3]
        
        # Calculate Total
        total = base_price
        services = []
        if self.chk_dj.isChecked(): 
            total += 5000
            services.append("DJ")
        if self.chk_deco.isChecked(): 
            total += 2000
            services.append("Deco")
            
        success = database_halls.book_hall(
            hall_id, 
            self.inp_name.text(), 
            self.inp_phone.text(), 
            self.inp_date.text(), 
            self.inp_type.currentText(), 
            ", ".join(services), 
            total
        )
        
        if success:
            QMessageBox.information(self, "Success", f"Hall Booked!\nTotal: ₹{total}")
            self.refresh_bookings()
        else:
            QMessageBox.warning(self, "Error", "Hall is already booked for this date!")

    def refresh_bookings(self):
        data = database_halls.get_bookings()
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            # row: (id, hall_name, client, date, type, price)
            self.table.setItem(r, 0, QTableWidgetItem(row[1]))
            self.table.setItem(r, 1, QTableWidgetItem(row[2]))
            self.table.setItem(r, 2, QTableWidgetItem(row[3]))
            self.table.setItem(r, 3, QTableWidgetItem(row[4]))
            self.table.setItem(r, 4, QTableWidgetItem(str(row[5])))

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        # LEFT: Menu (List Widget)
        self.list_menu = QListWidget()
        self.list_menu.addItems(["🏢 Business Info", "🍽️ Tables & Rooms", "💾 Data & Backup"])
        self.list_menu.setFixedWidth(200)
        self.list_menu.currentRowChanged.connect(self.change_page)
        self.layout.addWidget(self.list_menu)
        
        # RIGHT: Content Stack
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # -- PAGE 1: BUSINESS INFO --
        self.page_info = QWidget()
        p1_layout = QFormLayout()
        self.page_info.setLayout(p1_layout)
        
        self.inp_name = QLineEdit(database.get_setting("restaurant_name"))
        self.inp_addr = QLineEdit(database.get_setting("address"))
        self.inp_phone = QLineEdit(database.get_setting("phone"))
        self.inp_gst = QLineEdit(database.get_setting("gstin"))
        self.inp_tax = QLineEdit(database.get_setting("tax_rate"))
        
        btn_save_info = QPushButton("💾 Save Business Info")
        btn_save_info.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_save_info.clicked.connect(self.save_info)
        
        p1_layout.addRow(QLabel("<b>INVOICE DETAILS</b>"))
        p1_layout.addRow("Hotel Name:", self.inp_name)
        p1_layout.addRow("Address:", self.inp_addr)
        p1_layout.addRow("Phone:", self.inp_phone)
        p1_layout.addRow("GSTIN / Tax ID:", self.inp_gst)
        p1_layout.addRow("Default Tax %:", self.inp_tax)
        p1_layout.addRow(btn_save_info)
        
        self.stack.addWidget(self.page_info)
        
        # -- PAGE 2: TABLES & ROOMS --
        self.page_setup = QWidget()
        p2_layout = QHBoxLayout()
        self.page_setup.setLayout(p2_layout)
        
        # Tables Column
        col_table = QVBoxLayout()
        col_table.addWidget(QLabel("<b>MANAGE TABLES</b>"))
        self.list_tables = QListWidget()
        self.refresh_tables_list()
        col_table.addWidget(self.list_tables)
        
        self.inp_table_name = QLineEdit()
        self.inp_table_name.setPlaceholderText("Name (e.g. GF1, T5)")
        col_table.addWidget(self.inp_table_name)
        
        btn_add_table = QPushButton("➕ Add Table")
        btn_add_table.clicked.connect(self.add_table)
        col_table.addWidget(btn_add_table)
        
        btn_del_table = QPushButton("🗑️ Delete Selected")
        btn_del_table.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_del_table.clicked.connect(self.del_table)
        col_table.addWidget(btn_del_table)
        
        # Rooms Column
        col_room = QVBoxLayout()
        col_room.addWidget(QLabel("<b>MANAGE ROOMS</b>"))
        self.table_rooms = QTableWidget()
        self.table_rooms.setColumnCount(3)
        self.table_rooms.setHorizontalHeaderLabels(["Room", "Type", "Price"])
        self.refresh_rooms_list()
        col_room.addWidget(self.table_rooms)
        
        form_room = QFormLayout()
        self.inp_room_num = QLineEdit()
        self.inp_room_type = QComboBox()
        self.inp_room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        self.inp_room_price = QLineEdit()
        
        form_room.addRow("No:", self.inp_room_num)
        form_room.addRow("Type:", self.inp_room_type)
        form_room.addRow("Price:", self.inp_room_price)
        col_room.addLayout(form_room)
        
        btn_add_room = QPushButton("➕ Add Room")
        btn_add_room.clicked.connect(self.add_room)
        col_room.addWidget(btn_add_room)
        
        btn_del_room = QPushButton("🗑️ Delete Selected")
        btn_del_room.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_del_room.clicked.connect(self.del_room)
        col_room.addWidget(btn_del_room)
        
        p2_layout.addLayout(col_table)
        p2_layout.addLayout(col_room)
        self.stack.addWidget(self.page_setup)
        
        # -- PAGE 3: DATA MANAGEMENT --
        self.page_data = QWidget()
        p3_layout = QVBoxLayout()
        self.page_data.setLayout(p3_layout)
        
        lbl_d = QLabel("<b>DATA BACKUP & RESET</b>")
        lbl_d.setFont(QFont("Arial", 14))
        p3_layout.addWidget(lbl_d)
        
        btn_backup = QPushButton("📦 Export / Backup Data")
        btn_backup.setFixedHeight(50)
        btn_backup.clicked.connect(self.backup_data)
        p3_layout.addWidget(btn_backup)
        
        btn_reset = QPushButton("⚠️ FACTORY RESET SALES")
        btn_reset.setStyleSheet("background-color: darkred; color: white; font-weight: bold;")
        btn_reset.setFixedHeight(50)
        btn_reset.clicked.connect(self.reset_sales)
        p3_layout.addWidget(btn_reset)
        p3_layout.addStretch()
        
        self.stack.addWidget(self.page_data)

    def change_page(self, row):
        self.stack.setCurrentIndex(row)

    def save_info(self):
        database.save_setting("restaurant_name", self.inp_name.text())
        database.save_setting("address", self.inp_addr.text())
        database.save_setting("phone", self.inp_phone.text())
        database.save_setting("gstin", self.inp_gst.text())
        database.save_setting("tax_rate", self.inp_tax.text())
        QMessageBox.information(self, "Saved", "Business Info Updated!")

    def refresh_tables_list(self):
        self.list_tables.clear()
        tables = database.get_all_tables()
        for t in tables:
            self.list_tables.addItem(t[0]) # Name

    def add_table(self):
        name = self.inp_table_name.text()
        if name:
            if database.add_custom_table(name):
                self.refresh_tables_list()
                self.inp_table_name.clear()
            else:
                QMessageBox.warning(self, "Error", "Table ID already exists")

    def del_table(self):
        item = self.list_tables.currentItem()
        if item:
            database.delete_table(item.text())
            self.refresh_tables_list()

    def refresh_rooms_list(self):
        self.table_rooms.setRowCount(0)
        rooms = database.get_all_rooms()
        self.table_rooms.setRowCount(len(rooms))
        for r, room in enumerate(rooms):
            self.table_rooms.setItem(r, 0, QTableWidgetItem(str(room[0])))
            self.table_rooms.setItem(r, 1, QTableWidgetItem(room[1]))
            self.table_rooms.setItem(r, 2, QTableWidgetItem(str(room[2])))

    def add_room(self):
        num = self.inp_room_num.text()
        price = self.inp_room_price.text()
        if num and price:
            database.add_custom_room(num, self.inp_room_type.currentText(), price)
            self.refresh_rooms_list()
            self.inp_room_num.clear()

    def del_room(self):
        row = self.table_rooms.currentRow()
        if row >= 0:
            r_num = self.table_rooms.item(row, 0).text()
            database.delete_room(r_num)
            self.refresh_rooms_list()

    def backup_data(self):
        
        src = database.DB_NAME
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"Backup_Hotel_{timestamp}.db"
        
        dest, _ = QFileDialog.getSaveFileName(self, "Save Backup", default_name, "Database Files (*.db)")
        if dest:
            try:
                shutil.copy(src, dest)
                QMessageBox.information(self, "Success", "Backup Created Successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def reset_sales(self):
        pwd, ok = QInputDialog.getText(self, "Admin Security", "Enter Admin Password to WIPE SALES:", QLineEdit.EchoMode.Password)
        if ok and pwd == "admin123": # Change this to your real password logic
            confirm = QMessageBox.question(self, "FINAL WARNING", "This will delete ALL Order History.\nAre you sure?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                import sqlite3
                conn = sqlite3.connect(database.DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM orders")
                cursor.execute("DELETE FROM order_items")
                cursor.execute("DELETE FROM bookings")
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Reset", "All Sales Data Wiped.")
        elif ok:
             QMessageBox.warning(self, "Error", "Incorrect Password")

class MenuManager(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        # --- LEFT: Management Area ---
        left_container = QFrame()
        left_vbox = QVBoxLayout()
        left_container.setLayout(left_vbox)

        # A. CATEGORY MANAGER 
        cat_group = QGroupBox("Category Management")
        cat_vbox = QVBoxLayout()
        cat_group.setLayout(cat_vbox)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(3)
        self.cat_table.setHorizontalHeaderLabels(["ID", "Name", "Tax %"])
        self.cat_table.setFixedHeight(180) # Compact height
        self.cat_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # --- SELECTION STYLE FOR CATEGORY TABLE ---
        self.cat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cat_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.cat_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #bdc3c7; 
                color: black;
            }
        """)
        
        cat_vbox.addWidget(self.cat_table)

        cat_input_row = QHBoxLayout()
        self.inp_new_cat = QLineEdit(); self.inp_new_cat.setPlaceholderText("New Category Name")
        self.inp_new_tax = QLineEdit("5.0"); self.inp_new_tax.setFixedWidth(50)
        btn_add_cat = QPushButton("➕")
        btn_add_cat.clicked.connect(self.add_category_logic)
        
        cat_input_row.addWidget(self.inp_new_cat)
        cat_input_row.addWidget(self.inp_new_tax)
        cat_input_row.addWidget(btn_add_cat)
        cat_vbox.addLayout(cat_input_row)

        btn_del_cat = QPushButton("🗑️ Delete Category")
        btn_del_cat.setStyleSheet("color: #c0392b; font-weight: bold;")
        btn_del_cat.clicked.connect(self.delete_category_logic)
        cat_vbox.addWidget(btn_del_cat)
        left_vbox.addWidget(cat_group)

        # B. ITEM FORM (Your existing form)
        item_group = QGroupBox("Item Details")
        left_layout = QFormLayout()
        item_group.setLayout(left_layout)
        
        self.inp_name = QLineEdit()
        self.inp_cat = QComboBox() # Now dynamically populated from the DB
        self.inp_cat.currentTextChanged.connect(self.auto_set_tax)
        
        self.inp_tax = QLineEdit("5.0")
        self.inp_price_dine = QLineEdit()
        self.inp_price_del = QLineEdit()
        self.inp_image = QLineEdit()
        
        btn_browse = QPushButton("📂 Browse")
        btn_browse.clicked.connect(self.browse_image)
        btn_search = QPushButton("🌍 Search")
        btn_search.clicked.connect(self.search_image_online)
        
        img_row = QHBoxLayout()
        img_row.addWidget(self.inp_image); img_row.addWidget(btn_browse); img_row.addWidget(btn_search)
        
        btn_add = QPushButton("➕ Add Item")
        btn_add.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        btn_add.clicked.connect(self.add_item)
        
        left_layout.addRow("Item Name:", self.inp_name)
        left_layout.addRow("Category:", self.inp_cat)
        left_layout.addRow("Tax Rate (%):", self.inp_tax)
        left_layout.addRow("Dine-In Price:", self.inp_price_dine)
        left_layout.addRow("Delivery Price:", self.inp_price_del)
        left_layout.addRow("Image:", img_row)
        left_layout.addRow(btn_add)
        left_vbox.addWidget(item_group)

        self.layout.addWidget(left_container, stretch=1)
        
        # --- RIGHT: Current Menu Table ---
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6) 
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Dine ₹", "Del. ₹", "Category", "Tax %"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # --- SELECTION STYLE FOR MAIN ITEM TABLE ---
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #bdc3c7; 
                color: black;
            }
        """)
        
        right_layout.addWidget(self.table)
        
        btn_box = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refresh All")
        btn_refresh.clicked.connect(self.refresh_all_data)
        btn_box.addWidget(btn_refresh)
        
        btn_delete = QPushButton("🗑️ Delete Item")
        btn_delete.setStyleSheet("background-color: #c0392b; color: white;")
        btn_delete.clicked.connect(self.delete_item)
        btn_box.addWidget(btn_delete)
        
        right_layout.addLayout(btn_box)
        self.layout.addWidget(right_frame, stretch=2)
        
        self.refresh_all_data()

    def refresh_all_data(self):
        """Bug-Free Sync: Refreshes Categories and Items together."""
        # 1. Load Categories
        self.cat_table.setRowCount(0)
        self.inp_cat.clear()
        cats = database.get_all_categories()
        for r, (cid, name, tax) in enumerate(cats):
            self.cat_table.insertRow(r)
            self.cat_table.setItem(r, 0, QTableWidgetItem(str(cid)))
            self.cat_table.setItem(r, 1, QTableWidgetItem(name))
            self.cat_table.setItem(r, 2, QTableWidgetItem(str(tax)))
            self.inp_cat.addItem(name) # Adds current categories to dropdown

        # 2. Refresh main table
        self.refresh_table()

    def add_category_logic(self):
        name = self.inp_new_cat.text().upper().strip()
        try: tax = float(self.inp_new_tax.text())
        except: tax = 5.0
        if name and database.add_category(name, tax):
            self.inp_new_cat.clear()
            self.refresh_all_data()

    def delete_category_logic(self):
        row = self.cat_table.currentRow()
        if row >= 0:
            cid = int(self.cat_table.item(row, 0).text())
            name = self.cat_table.item(row, 1).text()
            if QMessageBox.question(self, "Confirm", f"Delete category '{name}'?") == QMessageBox.StandardButton.Yes:
                database.delete_category(cid)
                self.refresh_all_data()

    def auto_set_tax(self, category_name):
        # 1. Get the list of categories from the database
        cats = database.get_all_categories()
        
        # 2. Find the matching category and update the tax field
        for _, name, tax in cats:
            if name == category_name:
                self.inp_tax.setText(str(tax))
                break
        
    def delete_item(self):
        row = self.table.currentRow()
        if row >= 0:
            item_id = self.table.item(row, 0).text()
            confirm = QMessageBox.question(self, "Confirm", f"Delete Item ID {item_id}?", 
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                # Assuming you have a delete function in database.py
                import sqlite3
                conn = sqlite3.connect(database.DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
                conn.commit()
                conn.close()
                self.refresh_table()
        else:
            QMessageBox.warning(self, "Selection", "Select an item to delete.")

    def browse_image(self):
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getOpenFileName(self, 'Select', '', "Images (*.jpg *.png)")
        if fname: self.inp_image.setText(fname)

    def search_image_online(self):
        """Searches Google for the item name. No longer shows annoying popups."""
        term = self.inp_name.text().strip()
        if term:
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?tbm=isch&q={term}")

    def add_item(self):
        """Captures all 6 inputs and sends them to the database."""
        name = self.inp_name.text()
        p_dine = self.inp_price_dine.text()
        p_del = self.inp_price_del.text()
        cat = self.inp_cat.currentText()
        img = self.inp_image.text()
        tax = self.inp_tax.text()
        
        if name and p_dine and p_del and tax:
            # Pass all 6 arguments to database.py
            database.add_item(name, p_dine, p_del, cat, img, tax)
            
            self.refresh_table()
            # Clear inputs
            self.inp_name.clear()
            self.inp_price_dine.clear()
            self.inp_price_del.clear()
            self.inp_image.clear()
            self.auto_set_tax(cat) 
        else:
            QMessageBox.warning(self, "Error", "Name, Both Prices, and Tax are required!")

    def refresh_table(self):
        """Refreshes the table and explicitly fills the 6th Tax column."""
        self.table.setRowCount(0)
        # Fetch data: (id[0], name[1], p_dine[2], p_del[3], cat[4], img[5], tax[6])
        items = database.get_all_items() 
        self.table.setRowCount(len(items))
        
        for r, item in enumerate(items):
            # Columns 0 to 4: ID, Name, Dine, Del, Category
            self.table.setItem(r, 0, QTableWidgetItem(str(item[0])))
            self.table.setItem(r, 1, QTableWidgetItem(str(item[1])))
            self.table.setItem(r, 2, QTableWidgetItem(str(item[2])))
            self.table.setItem(r, 3, QTableWidgetItem(str(item[3])))
            self.table.setItem(r, 4, QTableWidgetItem(str(item[4])))
            
            # --- THE FIX: FILL THE 6th COLUMN (Index 5) ---
            # Data is at index 6 in the database row
            tax_val = item[6] if len(item) > 6 and item[6] is not None else "5.0"
            self.table.setItem(r, 5, QTableWidgetItem(f"{tax_val}%"))

# ==========================================
# 5.POS INTERFACE
# ==========================================
class POSInterface(QWidget):
    def __init__(self, mode, table_num=None, parent=None, tab_ref=None):
        super().__init__(parent)
        self.tab_ref = tab_ref
        self.mode = mode 
        self.table_num = table_num 
        self.is_room = (mode == "ROOM_SERVICE")
        self.cart = []
        self.customer_info = None 
        
        # --- TRACKING STATE ---
        self.current_category = "ALL ITEMS" # Tracks active sidebar selection
        self.all_items = [] # Stores full database menu
        
        self.db_price_mode = "DELIVERY" if mode == "DELIVERY" else "DINE_IN"
        
        if self.table_num:
            self.cart = database.get_active_order(self.table_num, is_room=self.is_room)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0,0,0,0)
        
        # --- COL 1: CATEGORIES ---
        self.cat_frame = QFrame()
        self.cat_frame.setFixedWidth(160)
        self.cat_frame.setStyleSheet("background-color: #2c3e50; border-right: 1px solid gray;")
        self.cat_layout = QVBoxLayout()
        self.cat_frame.setLayout(self.cat_layout)
        self.refresh_categories() # Populates and connects buttons
        self.layout.addWidget(self.cat_frame)
        
        # --- COL 2: MENU GRID ---
        self.menu_frame = QWidget()
        menu_layout = QVBoxLayout()
        self.menu_frame.setLayout(menu_layout)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search Item...")
        self.search_bar.setFixedHeight(40)
        # Connects search bar to the filter logic
        self.search_bar.textChanged.connect(self.filter_menu)
        menu_layout.addWidget(self.search_bar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.menu_grid = QGridLayout()
        self.grid_container.setLayout(self.menu_grid)
        scroll.setWidget(self.grid_container)
        menu_layout.addWidget(scroll)
        self.layout.addWidget(self.menu_frame, stretch=2)
        
        # --- COL 3: CART & ACTIONS ---
        self.cart_frame = QFrame()
        self.cart_frame.setFixedWidth(400)
        self.cart_frame.setStyleSheet("background-color: white; border-left: 2px solid #ccc;")
        cart_layout = QVBoxLayout()
        self.cart_frame.setLayout(cart_layout)
        
        # Header
        if self.is_room:
            title_text = f"ROOM {self.table_num}"
        elif self.table_num:
            title_text = f"TABLE {self.table_num}"
        else:
            title_text = f"🛍️ {self.mode}"
            
        lbl_h = QLabel(title_text)
        lbl_h.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h.setStyleSheet("background: #ecf0f1; padding: 15px; color: #2c3e50; border-bottom: 1px solid #ccc;")
        cart_layout.addWidget(lbl_h)
        
        # Alert Label
        self.lbl_alert = QLabel("✅ KOT Sent Successfully!")
        self.lbl_alert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_alert.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.lbl_alert.hide() 
        cart_layout.addWidget(self.lbl_alert)

        # If this is NOT a table (meaning it is Takeout/Delivery), show the Customer Button
        if not self.table_num:
            self.btn_customer = QPushButton("👤 Guest (Click to Set)")
            self.btn_customer.setStyleSheet("background-color: #34495e; color: white; padding: 10px; border-radius: 5px; margin: 5px;")
            self.btn_customer.clicked.connect(self.set_customer)
            cart_layout.addWidget(self.btn_customer)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item", "Price", "Qty", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("border: 1px solid #ddd;")

        # 1. Select the entire row, not just one cell
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # 2. Allow only one row to be selected at a time
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # 3. Make the selected row GREY with Black text
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #bdc3c7;  /* Slightly Grey */
                color: black;               /* Text stays black */
            }
        """)

        cart_layout.addWidget(self.table)

        
        
        # Totals Area
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #f9f9f9;")
        form_layout = QFormLayout()
        form_frame.setLayout(form_layout)
        
        self.lbl_subtotal = QLabel("$0.00")
        self.lbl_tax = QLabel("$0.00")
        self.inp_discount = QLineEdit("0")
        self.inp_discount.setFixedWidth(60)
        self.inp_discount.textChanged.connect(self.update_totals)
        self.lbl_final = QLabel("$0.00")
        self.lbl_final.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_final.setStyleSheet("color: #27ae60;")
        
        form_layout.addRow("Subtotal:", self.lbl_subtotal)
        form_layout.addRow("Tax:", self.lbl_tax)
        form_layout.addRow("Discount (%):", self.inp_discount)
        form_layout.addRow("TOTAL:", self.lbl_final)
        cart_layout.addWidget(form_frame)
        
        # Buttons
        btn_box = QHBoxLayout()
        
        # Note Button
        btn_note = QPushButton("📝 NOTE")
        btn_note.setFixedHeight(50)
        btn_note.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_note.clicked.connect(self.add_note_to_item)
        btn_box.addWidget(btn_note)

        if self.table_num:
            btn_kot = QPushButton("👨‍🍳 SEND KOT")
            btn_kot.setFixedHeight(50)
            btn_kot.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
            btn_kot.clicked.connect(self.send_kot_only)
            btn_box.addWidget(btn_kot)
            
            btn_bill = QPushButton("💰 BILL & CLOSE")
            btn_bill.setFixedHeight(50)
            btn_bill.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
            btn_bill.clicked.connect(self.print_bill_and_close)
            btn_box.addWidget(btn_bill)
        else:
            btn_checkout = QPushButton("✅ CHECKOUT")
            btn_checkout.setFixedHeight(50)
            btn_checkout.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
            btn_checkout.clicked.connect(self.checkout_takeout)
            btn_box.addWidget(btn_checkout)
            
        cart_layout.addLayout(btn_box)
        self.layout.addWidget(self.cart_frame)
        
        self.all_items = []
        self.refresh_menu()
        if self.cart: self.update_cart_ui()
    
    def refresh_categories(self):
        # 1. Clear existing widgets in cat_layout
        while self.cat_layout.count():
            child = self.cat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Rebuild Title and "All" button
        lbl_cat = QLabel("CATEGORIES")
        lbl_cat.setStyleSheet("color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        self.cat_layout.addWidget(lbl_cat)
        
        btn_all = QPushButton("ALL ITEMS")
        btn_all.setFixedHeight(50)
        btn_all.setStyleSheet("text-align: left; padding: 10px; color: white; background: #34495e; border-bottom: 1px solid #4e6070;")
        btn_all.clicked.connect(lambda: self.filter_category("ALL"))
        self.cat_layout.addWidget(btn_all)
        
        # 3. Fetch Fresh Categories from DB
        cats = database.get_all_categories()
        for c_id, c_name, c_tax in cats:
            btn = QPushButton(c_name)
            btn.setFixedHeight(50)
            btn.setStyleSheet("text-align: left; padding: 10px; color: white; background: #34495e; border-bottom: 1px solid #4e6070;")
            btn.clicked.connect(lambda ch, x=c_name: self.filter_category(x))
            self.cat_layout.addWidget(btn)
            
        self.cat_layout.addStretch()

    def refresh_menu(self):
        self.all_items = database.get_menu_items(self.db_price_mode)
        self.apply_filter()

    def render_menu_items(self, items):
        # 1. Clear existing grid
        for i in reversed(range(self.menu_grid.count())): 
            widget = self.menu_grid.itemAt(i).widget()
            if widget: widget.setParent(None)

        row, col = 0, 0
        for item in items:
            name = item.get('name', 'Unknown').strip()
            try:
                price = float(item.get('price', 0))
            except:
                price = 0.0
            db_img = item.get('image', "") 

            # --- THE CARD CONTAINER ---
            card = QFrame()
            card.setFixedSize(160, 200) # Uniform card size
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #dcdde1;
                    border-radius: 12px;
                }
                QFrame:hover {
                    border: 2px solid #2ecc71; /* Professional Green highlight */
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 8) # No margin at top for image
            card_layout.setSpacing(5)

            # --- IMAGE SECTION (TOP) ---
            img_label = QLabel()
            img_label.setFixedSize(160, 110) # Fixed image header
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Style to round only top corners
            img_label.setStyleSheet("border-top-left-radius: 12px; border-top-right-radius: 12px; border: none; background: #f8f9fa;")

            final_img_path = None
            if db_img and os.path.exists(str(db_img)):
                final_img_path = str(db_img)
            else:
                for ext in [".png", ".jpg", ".jpeg"]:
                    test_path = os.path.join("images", f"{name}{ext}")
                    if os.path.exists(test_path):
                        final_img_path = test_path
                        break

            if final_img_path:
                pixmap = QPixmap(final_img_path)
                # Smooth scaling to fill the header width
                img_label.setPixmap(pixmap.scaled(160, 110, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                img_label.setScaledContents(True)
            else:
                img_label.setText("🍽️")
                img_label.setStyleSheet("font-size: 30px; color: #bdc3c7; border: none;")

            card_layout.addWidget(img_label)

            # --- TEXT SECTION (BOTTOM) ---
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(10, 0, 10, 0)
            
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px; border: none;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setWordWrap(True)
            
            price_lbl = QLabel(f"₹{price:.0f}")
            price_lbl.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px; border: none;")
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            info_layout.addWidget(name_lbl)
            info_layout.addWidget(price_lbl)
            card_layout.addLayout(info_layout)

            # --- THE CLICKABLE OVERLAY ---
            # We put a transparent button over the entire card
            btn = QPushButton(card)
            btn.setFixedSize(160, 200)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.clicked.connect(lambda ch, i=item: self.add_to_cart(i))
            
            self.menu_grid.addWidget(card, row, col)
            
            col += 1
            if col > 3: 
                col = 0
                row += 1

        self.menu_grid.setRowStretch(row + 1, 1)

    def filter_category(self, category_name):
        self.current_category = "ALL ITEMS" if category_name == "ALL" else category_name
        self.apply_filter()

    def filter_menu(self):
        self.apply_filter()

    def apply_filter(self):
        search_text = self.search_bar.text().lower()
        filtered = [
            i for i in self.all_items 
            if (self.current_category == "ALL ITEMS" or i['category'] == self.current_category)
            and (search_text in i['name'].lower())
        ]
        self.render_menu_items(filtered)

    def add_to_cart(self, item_data):
        """Adds item. separates items if they have notes."""
        
        # 1. Check for existing item WITHOUT a note
        for existing_item in self.cart:
            # FIX: Only increment if names match AND the note is empty
            if existing_item['name'] == item_data['name'] and existing_item['note'] == "":
                existing_item['qty'] += 1
                self.update_cart_ui()
                return

        # 2. If new (or only modified versions exist), create fresh entry
        new_item = {
            'id': item_data['id'],
            'name': item_data['name'],
            'price': float(item_data['price']), 
            'qty': 1,
            'tax_rate': float(item_data.get('tax_rate', 5.0)), # Ensure tax key matches
            'printed': 0,
            'note': ''   
        }
        
        self.cart.append(new_item)
        self.update_cart_ui()

    def update_cart_ui(self):
        self.table.setRowCount(len(self.cart))
        subtotal = 0
        total_tax = 0
        
        for r, item in enumerate(self.cart):
            # Item Name + Note Indicator
            display_name = item['name']
            if item.get('note'):
                display_name += f" 📝" # Add icon if note exists
            
            self.table.setItem(r, 0, QTableWidgetItem(display_name))
            self.table.setItem(r, 1, QTableWidgetItem(f"{item['price']:.0f}"))
            
            # --- QTY WIDGET WITH LOCK LOGIC ---
            qty_w = QWidget()
            hl = QHBoxLayout()
            hl.setContentsMargins(0,0,0,0)
            hl.setSpacing(2)
            
            printed_qty = item.get('printed', 0)
            current_qty = item['qty']
            
            # MINUS BUTTON
            bm = QPushButton("-")
            bm.setFixedSize(25,25)
            
            # LOCK LOGIC: If current qty is equal/less than what's printed, DISABLE minus
            if current_qty <= printed_qty:
                bm.setEnabled(False) 
                bm.setStyleSheet("background:#95a5a6; color:white; border-radius:3px;") # Greyed out
                bm.setToolTip("Cannot remove item sent to Kitchen")
            else:
                bm.setEnabled(True)
                bm.setStyleSheet("background:#e74c3c; color:white; font-weight:bold; border-radius:3px;") # Red
                
            # Connect using lambda with correct index capture
            bm.clicked.connect(lambda ch, x=r: self.change_qty(x, -1))
            
            lq = QLabel(str(current_qty))
            lq.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lq.setFixedWidth(20)
            
            # PLUS BUTTON (Always enabled)
            bp = QPushButton("+")
            bp.setFixedSize(25,25)
            bp.setStyleSheet("background:#27ae60; color:white; font-weight:bold; border-radius:3px;")
            bp.clicked.connect(lambda ch, x=r: self.change_qty(x, 1))
            
            hl.addWidget(bm)
            hl.addWidget(lq)
            hl.addWidget(bp)
            qty_w.setLayout(hl)
            # ----------------------------------
            
            self.table.setCellWidget(r, 2, qty_w)
            
            # Total
            line_total = item['qty'] * item['price']
            self.table.setItem(r, 3, QTableWidgetItem(f"{line_total:.0f}"))
            
            subtotal += line_total
            
            # --- THE FIX IS HERE ---
            # Use .get('tax_rate', 5.0) instead of item['tax']
            tax_rate = item.get('tax_rate', 5.0) 
            total_tax += line_total * (tax_rate / 100)
            
        self.current_subtotal = subtotal
        self.current_tax = total_tax
        self.lbl_subtotal.setText(f"₹{subtotal:.2f}")
        self.lbl_tax.setText(f"₹{total_tax:.2f}")
        self.update_totals()

    def change_qty(self, idx, delta):
        if 0 <= idx < len(self.cart):
            self.cart[idx]['qty'] += delta
            if self.cart[idx]['qty'] <= 0: del self.cart[idx]
            self.update_cart_ui()

    def update_totals(self):
        subtotal = 0.0
        total_tax_amount = 0.0
        
        for item in self.cart:
            qty = item['qty']
            price = item['price']
            
            # Use the item's SPECIFIC tax rate (e.g., 5.0 or 18.0)
            # We ensure it defaults to 5.0 if missing
            tax_rate = item.get('tax_rate', 5.0) 
            
            item_total = price * qty
            item_tax = item_total * (tax_rate / 100)
            
            subtotal += item_total
            total_tax_amount += item_tax

        # Discount Logic
        try:
            disc_percent = float(self.inp_discount.text())
        except:
            disc_percent = 0.0
            
        discount_amount = (subtotal + total_tax_amount) * (disc_percent / 100)
        final_total = (subtotal + total_tax_amount) - discount_amount
        
        # Update Labels
        self.lbl_subtotal.setText(f"₹ {subtotal:.2f}")
        self.lbl_tax.setText(f"₹ {total_tax_amount:.2f}") # Shows total mixed tax
        self.lbl_final.setText(f"₹ {final_total:.2f}")

    def set_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.customer_info = dlg.get_data()
            self.btn_customer.setText(f"👤 {self.customer_info['name']}")

    def send_kot_only(self):
        # 1. Check if empty
        if not self.cart:
            QMessageBox.warning(self, "Empty Order", "Please add items before sending to Kitchen.")
            return

        # 2. Calculate New Items
        items_to_print = []
        for item in self.cart:
            current_qty = item['qty']
            printed_qty = item.get('printed', 0)
            if current_qty > printed_qty:
                new_qty = current_qty - printed_qty
                print_item = item.copy()
                print_item['qty'] = new_qty
                items_to_print.append(print_item)
        
        if not items_to_print:
            self.lbl_alert.setText("⚠️ No new items to print")
            self.lbl_alert.show()
            QTimer.singleShot(1500, lambda: self.lbl_alert.hide())
            return

        # 3. Save Order
        order_type = "ROOM_SERVICE" if self.mode == "ROOM_SERVICE" else "DINE_IN"
        database.save_order(self.table_num, self.cart, order_type)
        
        if self.tab_ref and hasattr(self.tab_ref, 'refresh_tables'):
            self.tab_ref.refresh_tables()

        # 4. Print KOT Logic
        if self.is_room:
            label = f"ROOM {self.table_num}"
        elif self.mode == "TAKEOUT":
            label = "TAKEOUT"
        elif self.mode == "DELIVERY":
            label = "DELIVERY"
        else:
            label = f"TABLE {self.table_num}"
            
        printer.generate_kot(label, items_to_print)
        database.mark_kot_printed(self.table_num, is_room=self.is_room)
        
        # 5. Update Local Cart
        for item in self.cart:
            item['printed'] = item['qty']
        self.update_cart_ui() 
            
        self.lbl_alert.setText("✅ KOT Sent!")
        self.lbl_alert.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; border-radius: 5px;")
        self.lbl_alert.show()
        QTimer.singleShot(1500, lambda: self.lbl_alert.hide())
    
    def print_bill_and_close(self):
        if not self.cart: 
            return

        # 1. Math
        subtotal = sum(item['price'] * item['qty'] for item in self.cart)
        total_tax = sum((item['price'] * item['qty']) * (item.get('tax_rate', 5.0) / 100) for item in self.cart)
        gross_total = subtotal + total_tax

        try:
            disc_percent = float(self.inp_discount.text())
        except ValueError: 
            disc_percent = 0.0
            
        discount_amount = gross_total * (disc_percent / 100)
        final_total = gross_total - discount_amount

        # 2. Print
        printer.generate_bill(
            order_type=self.mode, 
            table_num=self.table_num, 
            cart_items=self.cart, 
            total_amount=final_total, 
            discount=discount_amount, 
            customer=self.customer_info
        )
        
        # 3. Checkout Logic
        if self.mode == "ROOM_SERVICE":
            database.checkout_room_orders(self.table_num) 
        else:
            database.checkout_table(self.table_num) 
        
        # --- UNIVERSAL REFRESH ---
        if self.tab_ref:
            if self.mode == "ROOM_SERVICE" and hasattr(self.tab_ref, 'refresh_rooms'):
                self.tab_ref.refresh_rooms()
            elif hasattr(self.tab_ref, 'refresh_tables'):
                self.tab_ref.refresh_tables()
        # ----------------------------------------------------
            
        QMessageBox.information(self, "Closed", f"Bill Generated for {self.mode}!")
        self.close()

    def checkout_takeout(self):
        if not self.cart: return
        try: 
            disc = float(self.inp_discount.text())
        except: 
            disc = 0
            
        total = self.current_subtotal + self.current_tax
        final = total * (1 - (disc/100))
        discount_amt = total - final
        
        if self.mode == "DELIVERY":
            if not self.customer_info: 
                self.set_customer()
            if not self.customer_info: 
                return
            
            database.save_delivery_order(self.cart, self.customer_info['name'], self.customer_info['phone'], self.customer_info['address'])
            printer.generate_kot("DELIVERY", self.cart)
            
            printer.generate_bill(
                order_type="DELIVERY", 
                table_num="", 
                cart_items=self.cart, 
                total_amount=final, 
                discount=discount_amt, 
                customer=self.customer_info
            )
            
        elif self.mode == "TAKEOUT":
            database.save_takeout_order(self.cart)
            printer.generate_kot("TAKEOUT", self.cart)
            
            printer.generate_bill(
                order_type="TAKEOUT", 
                table_num="", 
                cart_items=self.cart, 
                total_amount=final, 
                discount=discount_amt
            )
            
        QMessageBox.information(self, "Done", "Order Processed!")
        self.cart = []
        self.update_cart_ui()

    def add_note_to_item(self):
        # 1. Get the selected row from the visual table
        current_row = self.table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Select Item", "Please click on an item in the cart list first!")
            return
            
        # 2. Get the corresponding item from the cart list
        # (The cart list matches the table rows 1-to-1)
        item = self.cart[current_row]
        
        # 3. Ask for Note
        note, ok = QInputDialog.getText(self, "Add Note", f"Note for {item['name']}:")
        if ok and note:
            item['note'] = note  # Save note to that specific item
            self.update_cart_ui() # Refresh to show the note

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotel POS - ADMIN DASHBOARD")
        self.resize(1000, 700)
        
        # Create Tab Container
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 1. Reports Tab (Using the class you already have)
        self.tab_reports = ReportsWindow() 
        self.tabs.addTab(self.tab_reports, "📊 Sales Reports")
        
        # 2. Menu Manager Tab (The class we just added above)
        self.tab_menu = MenuManager()
        self.tabs.addTab(self.tab_menu, "🍔 Menu Manager")
        
        # 3. Settings Tab (The NEW class from the previous step)
        self.tab_settings = SettingsTab() 
        self.tabs.addTab(self.tab_settings, "⚙️ Settings & Setup")
        
        # Style the tabs for a professional look
        self.tabs.setStyleSheet("""
            QTabBar::tab { height: 40px; width: 150px; font-weight: bold; }
            QTabBar::tab:selected { background: #3498db; color: white; }
        """)

# ==========================================
# 6. MAIN DASHBOARD
# ==========================================
class HotelApp(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.user_role = role
        self.setWindowTitle(f"Hotel POS - {role} Mode")
        self.setGeometry(0, 0, 1400, 900)
        
        self.setup_menu_bar()

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 15px 30px; font-size: 16px; font-weight: bold; }")
        self.setCentralWidget(self.tabs)

        # 1. Dine In
        self.tab_dine_in = DineInTab(self)
        self.tabs.addTab(self.tab_dine_in, "🍽️ Table Book")
        
        # 2. Takeaway
        self.tab_takeaway = POSInterface("TAKEOUT", parent=self)
        self.tabs.addTab(self.tab_takeaway, "🛍️ Take Away")
        
        # 3. Delivery
        self.tab_delivery = POSInterface("DELIVERY", parent=self)
        self.tabs.addTab(self.tab_delivery, "🚚 Home Delivery")

        # 4. Rooms
        self.tab_rooms = RoomsTab(self)
        self.tabs.addTab(self.tab_rooms, "🛏️ Rooms")

        # 5. Party
        self.tab_party = PartyTab(self)
        self.tabs.addTab(self.tab_party, "🎉 Party & Events")

    def setup_menu_bar(self):
        menu = self.menuBar()

        # --- Admin Menu (Restricted) ---
        if self.user_role == "ADMIN":
            admin_menu = menu.addMenu("🛠️ Admin Controls")
            
            # This opens the BIG Dashboard (Reports + Menu + Settings)
            action_dashboard = admin_menu.addAction("📊 Open Admin Dashboard")
            action_dashboard.triggered.connect(self.open_admin_dashboard)

    def open_admin_dashboard(self):
        # We save it to 'self' so it doesn't vanish immediately
        self.admin_window = AdminWindow()
        self.admin_window.show()

    def open_settings(self):
        # Open Settings
        dlg = SettingsWindow(self)
        dlg.exec()
        
        # --- REFRESH EVERYTHING AFTER SETTINGS CLOSE ---
        # This fixes the issue of missing categories!
        self.tab_takeaway.refresh_categories()
        self.tab_takeaway.refresh_menu()
        
        self.tab_delivery.refresh_categories()
        self.tab_delivery.refresh_menu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("Initializing Database...")
    database.init_db()
    database.seed_data()
    database.init_room_db()
    database_halls.init_hall_db()
    print("Database Ready.")
    
    login = LoginWindow()
    if login.exec():
        window = HotelApp(login.user_role)
        window.showMaximized()
        sys.exit(app.exec())

