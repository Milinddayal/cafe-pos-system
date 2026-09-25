import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
from datetime import datetime
from PIL import Image
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Cafe POS System", page_icon="☕", layout="wide")

# --- INITIALIZE SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# --- INITIALIZE SESSION STATE ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'custom_menu' not in st.session_state:
    st.session_state.custom_menu = {
        "Special Burger": {"category": "Burgers", "price": 199.00, "stock": 25, "icon": "🍔"},
        "Crispy Fries": {"category": "Sides", "price": 99.00, "stock": 50, "icon": "🍟"},
        "Cafe Latte": {"category": "Beverages", "price": 150.00, "stock": 40, "icon": "☕"},
        "Chocolate Shake": {"category": "Beverages", "price": 180.00, "stock": 30, "icon": "🥤"},
        "Butter Croissant": {"category": "Snacks", "price": 120.00, "stock": 20, "icon": "🥐"},
        "Ice Cream Sundae": {"category": "Desserts", "price": 140.00, "stock": 15, "icon": "🍦"}
    }

# --- DATABASE LOGGING & LOADING FUNCTIONS ---
def log_sale(total_amount, payment_mode, cart_items, counter_id):
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. Log main sale
    sales_res = supabase.table("sales").insert({
        "date": order_date,
        "total": float(total_amount),
        "payment_mode": payment_mode
    }).execute()
    
    # 2. Log order items & KOT queue
    items_to_insert = []
    for item in cart_items:
        items_to_insert.append({
            "date": order_date,
            "item_name": item['Item'],
            "unit_price": float(item['Price']),
            "quantity": int(item['Qty']),
            "subtotal": float(item['Total']),
            "counter": counter_id,
            "status": "Pending"
        })
        # Deduct local session stock
        if item['Item'] in st.session_state.custom_menu:
            st.session_state.custom_menu[item['Item']]['stock'] = max(0, st.session_state.custom_menu[item['Item']]['stock'] - item['Qty'])

    supabase.table("order_items").insert(items_to_insert).execute()

def load_sales_data():
    response = supabase.table("sales").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['date'])
    return df

def load_item_sales_data():
    response = supabase.table("order_items").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['date'])
        df['Day'] = df['Date'].dt.date
    return df

def convert_dfs_to_excel(df_sales, df_items):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sales.to_excel(writer, index=False, sheet_name='Revenue Summary')
        df_items.to_excel(writer, index=False, sheet_name='Item Wise Sales')
    return output.getvalue()

# --- SIDEBAR: SYSTEM PORTAL SELECTION ---
st.sidebar.title("🔐 System Login Portal")
portal_mode = st.sidebar.selectbox("Choose Login Gateway", [
    "Select Portal...", 
    "🛒 Counter Staff Login", 
    "👨‍🍳 Kitchen Display (KDS)", 
    "🔑 Admin Management Login"
])

cafe_name = st.sidebar.text_input("Cafe Name", "Green Fusion")
logo_file = st.sidebar.file_uploader("Upload Cafe Logo", type=["png", "jpg", "jpeg"])

logo_base64 = ""
logo_img_obj = None
if logo_file is not None:
    logo_img_obj = Image.open(logo_file)
    st.sidebar.image(logo_img_obj, use_container_width=True)
    buffered = BytesIO()
    logo_img_obj.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

st.sidebar.divider()
upi_id = st.sidebar.text_input("UPI ID / Paytm ID", "greenfusion@paytm")
qr_image_file = st.sidebar.file_uploader("Upload QR Code", type=["png", "jpg", "jpeg"])

# --- DASHBOARD THEME CSS ---
if logo_base64:
    bg_watermark_css = f"""
    .stApp {{
        background-image: linear-gradient(rgba(247, 245, 240, 0.40), rgba(247, 245, 240, 0.40)), url("data:image/png;base64,{logo_base64}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: 45% auto;
        background-attachment: fixed;
        background-color: #f7f5f0;
    }}
    """
else:
    bg_watermark_css = """
    .stApp {
        background-color: #f7f5f0;
    }
    """

st.markdown(f"""
    <style>
    {bg_watermark_css}
    
    h1, h2, h3, h4, h5, h6, p, label, span {{
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    
    .pos-card {{
        background-color: rgba(255, 255, 255, 0.96);
        padding: 18px 12px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #d5ded0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }}
    
    .cart-box {{
        background-color: #ffffff !important;
        padding: 22px;
        border-radius: 16px;
        border: 2px solid #556B2F;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }}
    .cart-box h1, .cart-box h2, .cart-box h3, .cart-box h4, .cart-box h5, .cart-box h6, .cart-box p, .cart-box span, .cart-box label {{
        color: #000000 !important;
    }}
    
    div.stButton > button {{
        background-color: #556B2F !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: 2px solid #556B2F !important;
        box-shadow: 0 4px 10px rgba(85, 107, 47, 0.2);
        transition: all 0.2s ease-in-out;
    }}
    div.stButton > button:hover {{
        background-color: #ffffff !important;
        color: #556B2F !important;
        border: 2px solid #556B2F !important;
    }}
    
    .receipt-box {{
        background-color: #ffffff;
        padding: 20px;
        border: 2px dashed #556B2F;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        color: #1a1a1a !important;
        margin-bottom: 15px;
    }}
    
    .chef-token {{
        background-color: #fffef0;
        padding: 15px;
        border: 2px solid #333;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        color: #000 !important;
    }}
    
    .menu-directory-item {{
        color: #000000 !important;
        font-weight: 500;
        font-size: 16px;
        margin-bottom: 6px;
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: #e9ede6 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GATEWAY 1: COUNTER STAFF LOGIN & BILLING
# ==========================================
if portal_mode == "🛒 Counter Staff Login":
    st.title(f"☕ {cafe_name} - Counter Staff Portal")
    
    col_login1, col_login2 = st.columns(2)
    with col_login1:
        counter_id = st.text_input("Enter Counter Number / Staff ID", "Counter 1")
    with col_login2:
        counter_pin = st.text_input("Counter Passcode (Optional)", type="password")
        
    st.divider()
    
    if counter_id:
        st.success(f"Logged in successfully as **{counter_id}**. Ready for billing operations.")
        
        col_menu, col_cart = st.columns([1.6, 1], gap="large")
        
        with col_menu:
            categories = ["All Items", "Burgers", "Sides", "Snacks", "Beverages", "Desserts"]
            selected_cat = st.selectbox("Filter Category", categories)
            
            st.write("")
            
            filtered_menu = {}
            for item_name, data in st.session_state.custom_menu.items():
                if selected_cat == "All Items" or data["category"] == selected_cat:
                    filtered_menu[item_name] = data
                    
            if not filtered_menu:
                st.info("No items found in this category.")
            else:
                menu_items_list = list(filtered_menu.items())
                for i in range(0, len(menu_items_list), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(menu_items_list):
                            item_name, item_info = menu_items_list[i + j]
                            with cols[j]:
                                st.markdown('<div class="pos-card">', unsafe_allow_html=True)
                                
                                icon = item_info.get("icon", "☕")
                                st.markdown(f"<div style='font-size: 38px; margin-bottom: 5px;'>{icon}</div>", unsafe_allow_html=True)
                                st.markdown(f"<h4 style='margin: 4px 0 2px 0; font-size: 14px; color: #000 !important;'>{item_name}</h4>", unsafe_allow_html=True)
                                st.markdown(f"<p style='margin: 0 0 4px 0; color: #556B2F !important; font-weight: bold; font-size: 14px;'>₹{item_info['price']:.2f}</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='margin: 0 0 8px 0; color: #666 !important; font-size: 12px;'>Stock Left: <b>{item_info['stock']}</b></p>", unsafe_allow_html=True)
                                
                                if item_info['stock'] > 0:
                                    if st.button("Add to Order", key=f"counter_add_{item_name}", use_container_width=True):
                                        found = False
                                        for cart_item in st.session_state.cart:
                                            if cart_item["Item"] == item_name:
                                                cart_item["Qty"] += 1
                                                cart_item["Total"] = cart_item["Qty"] * cart_item["Price"]
                                                found = True
                                                break
                                        if not found:
                                            st.session_state.cart.append({
                                                "Item": item_name, 
                                                "Qty": 1, 
                                                "Price": item_info['price'], 
                                                "Total": item_info['price']
                                            })
                                        st.rerun()
                                else:
                                    st.error("Out of Stock")
                                    
                                st.markdown('</div>', unsafe_allow_html=True)

        with col_cart:
            st.subheader("🛒 Current Order")
            st.markdown('<div class="cart-box">', unsafe_allow_html=True)
            
            if not st.session_state.cart:
                st.info("Your cart is empty. Tap items from the menu.")
            else:
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df[['Item', 'Qty', 'Total']], hide_index=True, use_container_width=True)
                
                subtotal = sum(item['Total'] for item in st.session_state.cart)
                tax = subtotal * 0.05  # 5% GST
                grand_total = subtotal + tax
                
                st.divider()
                st.markdown(f"**Subtotal:** ₹{subtotal:.2f}")
                st.markdown(f"**GST (5%):** ₹{tax:.2f}")
                st.markdown(f"### **Grand Total:** ₹{grand_total:.2f}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🗑️ Clear", use_container_width=True):
                        st.session_state.cart = []
                        st.rerun()
                with col_b:
                    if st.button("❌ Remove", use_container_width=True):
                        if st.session_state.cart:
                            st.session_state.cart.pop()
                            st.rerun()
                
                st.divider()
                st.subheader("💳 Payment Mode")
                payment_mode = st.radio("Mode", ["Cash", "UPI QR", "Card"], horizontal=True)
                
                if payment_mode == "UPI QR":
                    st.markdown(f"""
                    <div style="background-color: #fdfbf7; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #d5ded0;">
                        <p style="margin: 0; font-weight: bold; color: #000 !important;">Scan to Pay</p>
                        <p style="margin: 3px 0; font-size: 12px; color: #444 !important;">ID: <b>{upi_id}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if qr_image_file is not None:
                        st.image(Image.open(qr_image_file), width=120)

                cash_given = 0.0
                if payment_mode == "Cash":
                    cash_given = st.number_input("Cash Tendered (₹)", min_value=0.0, value=float(grand_total), step=10.0)
                    change_due = cash_given - grand_total
                    if change_due >= 0:
                        st.success(f"**Change:** ₹{change_due:.2f}")
                    else:
                        st.error(f"**Shortage:** ₹{abs(change_due):.2f}")

                st.write("")
                if st.button("✅ Complete Order & Print", type="primary", use_container_width=True):
                    if payment_mode == "Cash" and cash_given < grand_total:
                        st.error("Insufficient cash given!")
                    else:
                        log_sale(grand_total, payment_mode, st.session_state.cart, counter_id)
                        order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        st.markdown("---")
                        st.markdown(f"### 🧾 Customer Bill Receipt ({counter_id})")
                        
                        receipt_html = f"""
                        <div class="receipt-box">
                            <h2 style="text-align: center; margin: 0; color: #556B2F !important;">{cafe_name}</h2>
                            <p style="text-align: center; font-size: 11px; color: #555;">Terminal: {counter_id} | Date: {order_time}</p>
                            <p style="text-align: center; font-size: 11px; color: #555;">Payment Mode: <b>{payment_mode}</b></p>
                            <hr style="border: 0.5px dashed #556B2F;">
                        """
                        for item in st.session_state.cart:
                            receipt_html += f"<p>{item['Qty']}x {item['Item']} - ₹{item['Total']:.2f}</p>"
                        
                        receipt_html += f"""
                            <hr style="border: 0.5px dashed #556B2F;">
                            <p>Subtotal - ₹{subtotal:.2f}</p>
                            <p>GST (5%) - ₹{tax:.2f}</p>
                            <h3 style="color: #1a1a1a !important;">Total: ₹{grand_total:.2f}</h3>
                        """
                        if payment_mode == "Cash":
                            receipt_html += f"""
                            <p>Cash Given - ₹{cash_given:.2f}</p>
                            <p>Change Returned - ₹{cash_given - grand_total:.2f}</p>
                            """
                        receipt_html += f"""
                            <p style="text-align: center; margin-top: 15px; font-size: 11px;">*** THANK YOU! VISIT AGAIN ***</p>
                        </div>
                        """
                        st.markdown(receipt_html, unsafe_allow_html=True)
                        st.session_state.cart = []
                        st.rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# GATEWAY 2: KITCHEN DISPLAY SCREEN (KDS)
# ==========================================
elif portal_mode == "👨‍🍳 Kitchen Display (KDS)":
    st.title("👨‍🍳 Live Kitchen Display Screen (KDS)")
    st.write("Real-time order ticket monitoring for kitchen staff.")
    
    if st.button("🔄 Refresh Kitchen Queue"):
        st.rerun()
        
    df_items = load_item_sales_data()
    if df_items.empty:
        st.info("No active orders in the kitchen queue.")
    else:
        # Show recent orders for today
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_orders = df_items[df_items['Day'].astype(str) == today_str]
        
        if today_orders.empty:
            st.info("No orders placed yet for today.")
        else:
            st.markdown("### 🔥 Live Order Tickets")
            # Group by order timestamp & counter
            grouped_orders = today_orders.groupby(['date', 'counter'])
            
            for (order_time, counter), group in grouped_orders:
                with st.expander(f"📦 Order from {counter} at {order_time}", expanded=True):
                    col_k1, col_k2 = st.columns([2, 1])
                    with col_k1:
                        for idx, row in group.iterrows():
                            st.markdown(f"<p style='font-size: 18px; font-weight: bold; margin: 2px 0;'>▪ {row['quantity']}x {row['item_name']}</p>", unsafe_allow_html=True)
                    with col_k2:
                        st.markdown(f"<span style='background-color: #fffef0; padding: 6px 12px; border-radius: 6px; border: 1px solid #333; font-weight: bold;'>Status: Preparing</span>", unsafe_allow_html=True)

# ==========================================
# GATEWAY 3: ADMIN MANAGEMENT LOGIN
# ==========================================
elif portal_mode == "🔑 Admin Management Login":
    st.title("🔑 Admin Management Login Gateway")
    st.write("Secure login required to access business analytics, live inventory, and reports.")
    
    admin_password = st.text_input("Enter Master Admin Password", type="password")
    
    if admin_password == "admin123":
        st.success("Master Admin Authentication Successful.")
        st.divider()
        
        admin_action = st.selectbox("Select Admin Control Module", [
            "➕ Manage Menu & Stock", 
            "📊 Business Revenue & Daily Item Reports"
        ])
        
        if admin_action == "➕ Manage Menu & Stock":
            st.subheader("Manage Menu Directory & Live Stock Quantities")
            
            with st.form("admin_menu_form"):
                new_item_name = st.text_input("Item Name (e.g., Cold Brew Coffee)")
                new_item_cat = st.selectbox("Category", ["Burgers", "Sides", "Snacks", "Beverages", "Desserts"])
                new_item_price = st.number_input("Price (₹)", min_value=1.0, value=150.0)
                initial_stock = st.number_input("Initial Stock Quantity", min_value=1, value=50)
                
                submit_btn = st.form_submit_button("➕ Add Item to POS Menu")
                
                if submit_btn:
                    if new_item_name:
                        st.session_state.custom_menu[new_item_name] = {
                            "category": new_item_cat,
                            "price": new_item_price,
                            "stock": initial_stock,
                            "icon": "🍽️"
                        }
                        st.success(f"Successfully added '{new_item_name}' to the live POS menu!")
                    else:
                        st.error("Please enter a valid item name.")

            st.divider()
            st.subheader("Active Menu Directory & Stock Status")
            for name, data in st.session_state.custom_menu.items():
                st.markdown(f"<div class='menu-directory-item'>• <b>{name}</b> ({data['category']}) - ₹{data['price']:.2f} | Stock: <span style='color: #556B2F; font-weight: bold;'>{data['stock']} units</span></div>", unsafe_allow_html=True)

        elif admin_action == "📊 Business Revenue & Daily Item Reports":
            st.subheader("📊 Detailed Item Sales & Daily Revenue Report")
            df_sales = load_sales_data()
            df_items = load_item_sales_data()
            
            if df_sales.empty:
                st.warning("No sales recorded yet across cloud counters.")
            else:
                payment_summary = df_sales.groupby('payment_mode')['total'].sum().to_dict()
                cash_total = payment_summary.get('Cash', 0.0)
                upi_total = payment_summary.get('UPI QR', 0.0)
                card_total = payment_summary.get('Card', 0.0)
                overall_total = df_sales['total'].sum()

                st.markdown("### 💰 Revenue Breakdown by Payment Mode")
                pm1, pm2, pm3, pm4 = st.columns(4)
                pm1.metric("💵 Cash Collection", f"₹{cash_total:,.2f}")
                pm2.metric("📱 UPI / Online", f"₹{upi_total:,.2f}")
                pm3.metric("💳 Card Payments", f"₹{card_total:,.2f}")
                pm4.metric("🌟 Overall Total", f"₹{overall_total:,.2f}")
                
                st.divider()

                st.markdown("### 📋 Daily Itemized Sales Report")
                if not df_items.empty:
                    available_days = sorted(df_items['Day'].astype(str).unique(), reverse=True)
                    selected_day = st.selectbox("Select Date for Item Breakdown", available_days)
                    
                    day_filtered_items = df_items[df_items['Day'].astype(str) == selected_day]
                    
                    daily_item_summary = day_filtered_items.groupby(['item_name', 'unit_price']).agg({'quantity': 'sum', 'subtotal': 'sum'}).reset_index()
                    daily_item_summary = daily_item_summary.rename(columns={
                        'item_name': 'Item Name',
                        'unit_price': 'Unit Price (₹)',
                        'quantity': 'Total Quantity Sold',
                        'subtotal': 'Total Daily Revenue (₹)'
                    })
                    
                    st.dataframe(daily_item_summary, hide_index=True, use_container_width=True)
                    
                    fig_daily_items = px.bar(
                        daily_item_summary, 
                        x='Item Name', 
                        y='Total Quantity Sold', 
                        title=f"Units Sold Per Item on {selected_day}", 
                        text='Total Quantity Sold', 
                        color_discrete_sequence=['#556B2F']
                    )
                    fig_daily_items.update_layout(xaxis_title="", yaxis_title="Units Sold", template="plotly_white")
                    st.plotly_chart(fig_daily_items, use_container_width=True)
                else:
                    st.info("No item details available yet.")

                st.divider()

                st.markdown("### 📥 Download System Reports")
                excel_file = convert_dfs_to_excel(df_sales, df_items)
                st.download_button(
                    label="📥 Download Comprehensive Sales & Items Report (Excel)",
                    data=excel_file,
                    file_name=f"cafe_complete_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.divider()

                df_sales_indexed = df_sales.set_index('Date')
                stat_view = st.selectbox("Select Timeframe Revenue Report", ["Daily", "Weekly", "Monthly", "Yearly"])
                
                if stat_view == "Daily":
                    data = df_sales_indexed.resample('D').sum().reset_index()
                    fig = px.bar(data, x='Date', y='total', title="Daily Revenue Breakdown (₹)", text='total', color_discrete_sequence=['#556B2F'])
                elif stat_view == "Weekly":
                    data = df_sales_indexed.resample('W').sum().reset_index()
                    fig = px.line(data, x='Date', y='total', title="Weekly Revenue Trends (₹)", markers=True, color_discrete_sequence=['#556B2F'])
                elif stat_view == "Monthly":
                    data = df_sales_indexed.resample('M').sum().reset_index()
                    fig = px.bar(data, x='Date', y='total', title="Monthly Revenue Summary (₹)", color_discrete_sequence=['#6B8E23'])
                elif stat_view == "Yearly":
                    data = df_sales_indexed.resample('Y').sum().reset_index()
                    data['Date'] = data['Date'].dt.year
                    fig = px.bar(data, x='Date', y='total', title="Yearly Revenue Performance (₹)", color_discrete_sequence=['#3b4e1e'])
                
                fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                st.subheader("⚡ Quick Performance Metrics")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Lifetime Revenue", f"₹{overall_total:,.2f}")
                m2.metric("Average Daily Sales", f"₹{df_sales_indexed.resample('D').sum()['total'].mean():,.2f}")
                m3.metric("Highest Single Bill", f"₹{df_sales['total'].max():,.2f}")
    else:
        if admin_password != "":
            st.error("Incorrect Admin Password.")
        else:
            st.info("🔒 Please enter the master password to unlock admin privileges. (Default: `admin123`)")

else:
    st.info("👉 Please select a login portal from the sidebar (`Counter Staff Login`, `Kitchen Display (KDS)`, or `Admin Management Login`) to begin.")