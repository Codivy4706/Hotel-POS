from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import datetime
import os
import subprocess
import database as database

def num_to_words(num):
    """Converts a number to words (Simplified for common currency)."""
    d = { 0 : 'Zero', 1 : 'One', 2 : 'Two', 3 : 'Three', 4 : 'Four', 5 : 'Five',
          6 : 'Six', 7 : 'Seven', 8 : 'Eight', 9 : 'Nine', 10 : 'Ten',
          11 : 'Eleven', 12 : 'Twelve', 13 : 'Thirteen', 14 : 'Fourteen',
          15 : 'Fifteen', 16 : 'Sixteen', 17 : 'Seventeen', 18 : 'Eighteen',
          19 : 'Nineteen', 20 : 'Twenty', 30 : 'Thirty', 40 : 'Forty',
          50 : 'Fifty', 60 : 'Sixty', 70 : 'Seventy', 80 : 'Eighty',
          90 : 'Ninety' }
    k = 1000
    m = k * 1000
    
    if num < 20: return d[num]
    if num < 100:
        if num % 10 == 0: return d[num]
        else: return d[num // 10 * 10] + ' ' + d[num % 10]
    if num < k:
        if num % 100 == 0: return d[num // 100] + ' Hundred'
        else: return d[num // 100] + ' Hundred and ' + num_to_words(num % 100)
    if num < m:
        if num % k == 0: return num_to_words(num // k) + ' Thousand'
        else: return num_to_words(num // k) + ' Thousand, ' + num_to_words(num % k)
    return str(num)

def generate_room_bill(room_num, guest_data, food_items, room_price, payment_mode):
    # --- 1. FETCH DYNAMIC INFO (Replacing hardcoded strings) ---
    hotel_name = database.get_setting("hotel_name", "GRAND HOTEL & SUITES")
    hotel_addr = database.get_setting("hotel_address", "123, Hospitality Lane, City Center")
    gstin = database.get_setting("hotel_gst", "27AAAAA0000A1Z5")
    hotel_ph = database.get_setting("hotel_phone", "9876543210")

    # --- DATA PREP ---
    booking_id = f"{datetime.datetime.now().strftime('%y%m%d')}{room_num}"
    invoice_no = f"INV-{booking_id}"
    
    # guest_data structure: (name, phone, check_in_date)
    check_in_str = guest_data[2] if len(guest_data) > 2 and guest_data[2] else "N/A"
    guest_phone = guest_data[1] if len(guest_data) > 1 and guest_data[1] else "N/A"
    
    check_out_dt = datetime.datetime.now()
    check_out_str = check_out_dt.strftime("%Y-%m-%d %H:%M")
    
    # Calculate Days Stayed
    try:
        ci_dt = datetime.datetime.strptime(check_in_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        days = (check_out_dt - ci_dt).days
        if days == 0: days = 1 # Minimum 1 day charge
    except:
        days = 1
        
    # --- PDF SETUP ---
    filename = f"Invoice_{room_num}_{booking_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # --- HEADER (Now using get_setting) ---
    y = height - 20
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, y, hotel_name) # Dynamic
    y -= 20
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, y, hotel_addr) # Dynamic
    y -= 12
    c.drawCentredString(width/2, y, f"GSTIN: {gstin} | Phone: {hotel_ph}") # Dynamic
    y -= 20
    c.line(20, y, width-20, y)
    y -= 20
    
    # --- INVOICE INFO ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, y, "TAX INVOICE")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width-20, y, f"Invoice No: {invoice_no}")
    y -= 12
    c.setFont("Helvetica", 10)
    c.drawRightString(width-20, y, f"Date: {check_out_dt.strftime('%d-%b-%Y')}")
    y -= 12
    c.drawRightString(width-20, y, f"Payment Mode: {payment_mode}")
    
    # Guest Details
    y += 24
    c.drawString(20, y-15, f"Guest Name: {guest_data[0]}")
    c.drawString(20, y-27, f"Phone: {guest_phone}") # Fixed
    
    c.drawCentredString(width/2, y-15, f"Room No: {room_num}")
    c.drawCentredString(width/2, y-27, f"Check-In: {check_in_str}") # Fixed
    c.drawCentredString(width/2, y-39, f"Check-Out: {check_out_str}")
    
    y -= 60
    
    # --- ITEM TABLE HEADER ---
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(20, y-5, width-40, 20, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, "Description")
    c.drawString(250, y, "Rate")
    c.drawString(320, y, "Qty/Days")
    c.drawRightString(width-30, y, "Amount (INR)")
    y -= 20
    
    # --- TABLE CONTENT ---
    total_amount = 0
    c.setFont("Helvetica", 10)
    
    # A. Room Charges
    room_total = room_price * days
    c.drawString(30, y, f"Room Charges ({days} Nights)")
    c.drawString(250, y, f"{room_price:.2f}")
    c.drawString(330, y, str(days))
    c.drawRightString(width-30, y, f"{room_total:.2f}")
    y -= 15
    total_amount += room_total
    
    # B. Food Items
    if food_items:
        y -= 5
        c.setFont("Helvetica-Bold", 9)
        c.drawString(30, y, "Room Service / Minibar:")
        y -= 15
        c.setFont("Helvetica", 9)
        
        for item in food_items:
            name, qty, rate, line_tot = item[0], item[1], item[2], item[3]
            c.drawString(40, y, name[:35])
            c.drawString(250, y, f"{rate:.2f}")
            c.drawString(330, y, str(qty))
            c.drawRightString(width-30, y, f"{line_tot:.2f}")
            y -= 12
            total_amount += line_tot
            
            if y < 100:
                c.showPage()
                y = height - 50
    
    y -= 10
    c.line(20, y, width-20, y)
    y -= 20
    
    # --- TOTALS ---
    subtotal = total_amount
    cgst, sgst = subtotal * 0.09, subtotal * 0.09
    grand_total = subtotal + cgst + sgst
    
    c.setFont("Helvetica", 10)
    c.drawString(350, y, "Sub Total:")
    c.drawRightString(width-30, y, f"{subtotal:.2f}")
    y -= 15
    
    c.drawString(350, y, "CGST (9%):")
    c.drawRightString(width-30, y, f"{cgst:.2f}")
    y -= 15
    
    c.drawString(350, y, "SGST (9%):")
    c.drawRightString(width-30, y, f"{sgst:.2f}")
    y -= 20
    
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(340, y-5, width-370, 20, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(350, y, "GRAND TOTAL:")
    c.drawRightString(width-30, y, f"INR {grand_total:,.2f}")
    
    y -= 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20, y, "Amount in Words:")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(120, y, f"{num_to_words(int(grand_total))} Rupees Only")
    
    # --- FOOTER ---
    y = 60
    c.line(20, y+50, 150, y+50); c.drawString(40, y+35, "Guest Signature")
    c.line(width-170, y+50, width-20, y+50); c.drawString(width-140, y+35, "Authorized Signatory")
    
    c.setFont("Helvetica", 7)
    c.drawString(20, y+10, "TERMS & CONDITIONS:")
    c.drawString(20, y, "1. Subject to City Jurisdiction.  2. Goods once sold will not be taken back.")
    
    c.save()
    print_file(filename)
    
def generate_kot(table_num, cart_items):
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    # Clean label for the ID
    kot_id = f"KOT-{str(table_num).replace(' ', '')}-{timestamp[-4:]}"
    filename = f"KOT_{str(table_num).replace(' ', '_')}_{timestamp}.pdf"
    
    # --- 1. CALCULATE EXACT HEIGHT ---
    header_height = 42
    footer_height = 4 
    list_height = 0
    
    for item in cart_items:
        list_height += 5   
        if item.get('note'):
            list_height += 4
        list_height += 4   
        
    total_height = header_height + list_height + footer_height
    
    width = 80 * mm
    height = total_height * mm 
    
    c = canvas.Canvas(filename, pagesize=(width, height))
    
    # Start drawing from top
    y = height - 8 * mm
    mid_x = width / 2
    
    # --- 2. HEADER ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(mid_x, y, "KITCHEN TICKET")
    y -= 8 * mm
    
    c.setFont("Helvetica-Bold", 14)
    # Box around table name
    c.rect(5*mm, y-6*mm, width-10*mm, 10*mm)
    c.drawCentredString(mid_x, y-4*mm, f"{table_num}")
    y -= 12 * mm
    
    dt = datetime.datetime.now().strftime("%d-%b %H:%M")
    c.setFont("Helvetica", 9) # Smaller font to save height
    c.drawCentredString(mid_x, y, f"Time: {dt}")
    y -= 4 * mm
    c.drawCentredString(mid_x, y, f"ID: {kot_id}")
    y -= 5 * mm
    
    c.setLineWidth(1)
    c.line(0, y, width, y)
    y -= 5 * mm
    
    # --- 3. ITEMS ---
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*mm, y, "QTY")
    c.drawString(15*mm, y, "ITEM")
    y -= 5 * mm
    
    for item in cart_items:
        qty = item['qty']
        name = item['name']
        note = item.get('note', '')
        
        # Item Line
        c.setFont("Helvetica-Bold", 13)
        c.drawString(2*mm, y, str(qty))
        c.drawString(15*mm, y, name[:22])
        y -= 5 * mm
        
        # Note Line
        if note:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(15*mm, y, f"* {note}")
            y -= 4 * mm
            
        # Dashed Separator
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.line(2*mm, y, width-2*mm, y)
        c.setDash([]) 
        y -= 4 * mm 

    # --- 4. FOOTER (Final Cut Line) ---
    y = 2 * mm
    c.setLineWidth(1)
    c.line(0, y, width, y)
    
    c.save()
    try:
        os.startfile(filename)
    except:
        pass

def print_file(filename):
    """Opens the PDF explicitly using Microsoft Edge."""
    try:
        full_path = os.path.abspath(filename)
        # FORCE EDGE COMMAND
        subprocess.Popen(f'start msedge "{full_path}"', shell=True)
    except Exception as e:
        print(f"Error opening Edge: {e}")

def generate_bill(order_type, table_num, cart_items, total_amount, discount=0, customer=None):
    import os
    import datetime
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    timestamp = datetime.datetime.now().strftime("%H%M%S")
    safe_table = str(table_num).replace(' ', '_')
    filename = f"Bill_{safe_table}_{timestamp}.pdf"
    
    # --- DYNAMIC HEIGHT CALCULATION ---
    # base_height covers header, table headers, and final totals (~90mm)
    # item_height adds space for each product line and its tax note
    base_height = 90 
    item_height = len(cart_items) * 10 
    tax_summary_height = 15 if discount > 0 else 10
    
    width = 80 * mm 
    height = (base_height + item_height + tax_summary_height) * mm 
    
    c = canvas.Canvas(filename, pagesize=(width, height))
    
    # Start drawing from top
    y = height - 10 * mm
    mid_x = width / 2
    left_x = 5 * mm
    right_x = width - 5 * mm
    
    # --- HEADER ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(mid_x, y, "GRAND HOTEL")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawCentredString(mid_x, y, "123 Hospitality Lane")
    y -= 5 * mm
    c.drawCentredString(mid_x, y, "Rishikesh, Uttarakhand")
    y -= 5 * mm
    c.line(left_x, y, right_x, y)
    y -= 5 * mm
    
    # --- INFO ---
    c.setFont("Helvetica-Bold", 11)
    if order_type == "ROOM_SERVICE":
        label = f"ROOM: {table_num}"
    elif order_type == "DINE_IN":
        label = f"TABLE: {table_num}"
    else:
        label = f"TYPE: {order_type} ({table_num})"
        
    c.drawString(left_x, y, f"Order: {label}")
    
    c.setFont("Helvetica", 9)
    dt_str = datetime.datetime.now().strftime("%d-%b %H:%M")
    c.drawRightString(right_x, y, dt_str)
    y -= 6 * mm
    
    if customer:
        c.drawString(left_x, y, f"Guest: {customer['name'][:20]}")
        y -= 5 * mm
        if customer.get('address'):
            c.setFont("Helvetica-Oblique", 8)
            address_text = f"Addr: {customer['address']}"
            c.drawString(left_x, y, address_text[:45]) 
            y -= 5 * mm
            c.setFont("Helvetica", 9)

    c.line(left_x, y, right_x, y)
    y -= 5 * mm
    
    # --- COLUMN HEADERS ---
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left_x, y, "Item")
    c.drawString(left_x + 35*mm, y, "Qty")
    c.drawRightString(right_x, y, "Price")
    y -= 4 * mm
    c.line(left_x, y, right_x, y)
    y -= 5 * mm
    
    # --- ITEMS LOOP ---
    subtotal = 0.0
    total_tax = 0.0
    
    for item in cart_items:
        name = item['name']
        qty = item['qty']
        unit_price = float(item['price'])
        line_total = unit_price * qty
        tax_rate = item.get('tax_rate', 5.0) 
        line_tax = line_total * (tax_rate / 100)
        
        subtotal += line_total
        total_tax += line_tax
        
        c.setFont("Helvetica", 9)
        c.drawString(left_x, y, f"{name[:18]}")
        c.drawString(left_x + 38*mm, y, str(qty))
        c.drawRightString(right_x, y, f"{line_total:.2f}")
        y -= 4 * mm
        
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(left_x, y, f"(@ {tax_rate}%)")
        y -= 5 * mm

    c.line(left_x, y, right_x, y)
    y -= 5 * mm
    
    # --- CALCULATIONS ---
    final_total = subtotal + total_tax - discount
    c.setFont("Helvetica", 10)
    
    c.drawString(left_x + 20*mm, y, "Subtotal:")
    c.drawRightString(right_x, y, f"{subtotal:.2f}")
    y -= 5 * mm
    
    c.drawString(left_x + 20*mm, y, "Tax (Total):")
    c.drawRightString(right_x, y, f"{total_tax:.2f}")
    y -= 5 * mm
    
    if discount > 0:
        c.drawString(left_x + 20*mm, y, "Discount:")
        c.drawRightString(right_x, y, f"-{discount:.2f}")
        y -= 5 * mm
    
    y -= 2 * mm
    c.line(left_x, y, right_x, y)
    y -= 6 * mm
    
    # --- FINAL TOTAL ---
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_x, y, "TOTAL:")
    c.drawRightString(right_x, y, f"Rs. {final_total:.2f}")
    y -= 8 * mm 
    
    # --- FOOTER ---
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(mid_x, y, "Thank You for Visiting!")
    
    # "Generated by HotelApp" line has been removed
    
    c.save()
    
    try:
        os.startfile(filename)
    except:
        pass
