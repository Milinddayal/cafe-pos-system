import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
from datetime import datetime
from PIL import Image
from supabase import create_client, Client
import os
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Green Fusion - POS System", page_icon="☕", layout="wide")

# --- LIVE AUTO-REFRESH (Every 5 seconds for real-time cloud sync) ---
st_autorefresh(interval=5000, key="greenfusion_live_sync")

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

if 'last_receipt' not in st.session_state:
    st.session_state.last_receipt = None

if 'target_mod_time' not in st.session_state:
    st.session_state.target_mod_time = None

if 'active_portal' not in st.session_state:
    st.session_state.active_portal = "🛒 Counter Staff Billing"

if 'custom_menu' not in st.session_state:
    st.session_state.custom_menu = {
        "Special Burger": {"category": "Burgers", "price": 199.00, "stock": 25, "icon": "🍔", "image": None},
        "Crispy Fries": {"category": "Sides", "price": 99.00, "stock": 50, "icon": "🍟", "image": None},
        "Cafe Latte": {"category": "Beverages", "price": 150.00, "stock": 40, "icon": "☕", "image": None},
        "Chocolate Shake": {"category": "Beverages", "price": 180.00, "stock": 30, "icon": "🥤", "image": None},
        "Butter Croissant": {"category": "Snacks", "price": 120.00, "stock": 20, "icon": "🥐", "image": None},
        "Ice Cream Sundae": {"category": "Desserts", "price": 140.00, "stock": 15, "icon": "🍦", "image": None}
    }

# --- LOAD BRAND LOGO AUTOMATICALLY ---
LOGO_PATH = "logo.jpeg"
logo_base64 = ""
logo_img_obj = None

if os.path.exists(LOGO_PATH):
    logo_img_obj = Image.open(LOGO_PATH)
    buffered = BytesIO()
    logo_img_obj.save(buffered, format="JPEG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

# --- DATABASE LOGGING & LOADING FUNCTIONS ---
def log_sale(total_amount, payment_mode, cart_items, counter_id):
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    supabase.table("sales").insert({
        "date": order_date,
        "total": float(total_amount),
        "payment_mode": payment_mode
    }).execute()
    
    items_to_insert = []
    for item in cart_items:
        items_to_insert.append({
            "date": order_date,
            "item_name": item['Item'],
            "unit_price": float(item['Price']),
            "quantity": int(item['Qty']),
            "subtotal": float(item['Total']),
            "counter": counter_id,
            "status": "Completed",
            "modification_reason": ""
        })
        if item['Item'] in st.session_state.custom_menu:
            st.session_state.custom_menu[item['Item']]['stock'] = max(0, st.session_state.custom_menu[item['Item']]['stock'] - item['Qty'])

    supabase.table("order_items").insert(items_to_insert).execute()
    return order_date

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

# --- SIDEBAR: SYSTEM PORTAL SELECTION & BRANDING ---
st.sidebar.title("🔐 System Login Portal")

portals_list = [
    "🛒 Counter Staff Billing", 
    "🛠️ Order Modification & Cancellation",
    "🍽️ Menu Display Screen",
    "👨‍🍳 Kitchen Display (KDS)", 
    "🔑 Admin Management Login"
]

# Ensure active portal is valid
if st.session_state.active_portal not in portals_list:
    st.session_state.active_portal = "🛒 Counter Staff Billing"

current_portal_index = portals_list.index(st.session_state.active_portal)
portal_mode = st.sidebar.selectbox("Choose Login Gateway", portals_list, index=current_portal_index)

# Update session state when user manually changes sidebar selection
if portal_mode != st.session_state.active_portal:
    st.session_state.active_portal = portal_mode

st.sidebar.divider()
if logo_img_obj is not None:
    st.sidebar.image(logo_img_obj, use_container_width=True, caption="Green Fusion - Bite & Sip by Dayals")

st.sidebar.divider()
upi_id = st.sidebar.text_input("UPI ID / Paytm ID", "greenfusion@paytm")
qr_image_file = st.sidebar.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

# --- WATERMARK BACKGROUND & STYLING CSS ---
if logo_base64:
    bg_watermark_css = f"""
    .stApp {{
        background-image: linear-gradient(rgba(250, 249, 246, 0.90), rgba(250, 249, 246, 0.90)), url("data:image/jpeg;base64,{logo_base64}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: 45% auto;
        background-attachment: fixed;
        background-color: #faf9f6;
    }}
    """
else:
    bg_watermark_css = """
    .stApp {
        background-color: #faf9f6;
    }
    """

st.markdown(f"""
    <style>
    {bg_watermark_css}
    
    h1, h2, h3, h4, h5, h6 {{
        color: #2b3a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-style: italic !important;
        font-weight: bold !important;
    }}
    
    p, label, span {{
        color: #1a1a1a !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    
    .pos-card {{
        background-color: rgba(255, 255, 255, 0.88);
        padding: 16px 10px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #d5ded0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }}
    
    .cart-box {{
        background-color: rgba(255, 255, 255, 0.92) !important;
        padding: 18px;
        border-radius: 16px;
        border: 2px solid #556B2F;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }}
    .cart-box h1, .cart-box h2, .cart-box h3, .cart-box h4, .cart-box h5, .cart-box h6, .cart-box p, .cart-box span, .cart-box label {{
        color: #000000 !important;
    }}
    
    .mod-container {{
        background: linear-gradient(135deg, rgba(245, 247, 240, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
        padding: 25px;
        border-radius: 16px;
        border: 2px solid #556B2F;
        box-shadow: 0 6px 20px rgba(85, 107, 47, 0.12);
        margin-bottom: 20px;
    }}
    
    div.stButton > button {{
        background-color: #556B2F !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
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
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    .chef-token {{
        background-color: #fffef0;
        padding: 15px;
        border: 2px solid #333;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        color: #000 !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: rgba(238, 242, 235, 0.92) !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GATEWAY 1: COUNTER STAFF BILLING
# ==========================================
if st.session_state.active_portal == "🛒 Counter Staff Billing":
    st.title("☕ *Green Fusion - Counter Staff Portal*")
    st.markdown("*Bite & Sip by Dayals*")
    
    col_login1, col_login2 = st.columns(2)
    with col_login1:
        counter_id = st.text_input("Enter Counter Number / Staff ID", "Counter 1")
    with col_login2:
        counter_pin = st.text_input("Counter Passcode (Optional)", type="password")
        
    st.divider()
    
    if counter_id:
        st.success(f"Logged in successfully as **{counter_id}**. Ready for billing operations.")

        if st.session_state.get('last_receipt'):
            st.markdown("---")
            st.success("🎉 Order Completed Successfully! Below is your live printable receipt and kitchen token.")
            
            col_rc1, col_rc2 = st.columns(2)
            with col_rc1:
                st.markdown("### *🧾 Customer Bill Receipt*")
                st.markdown(st.session_state.last_receipt['receipt_html'], unsafe_allow_html=True)
                
                st.markdown("---")
                if st.button("🛠️ [ MODIFY / CANCEL THIS ORDER ]", key="btn_jump_mod_highlighted", use_container_width=True):
                    st.session_state.target_mod_time = st.session_state.last_receipt['order_time']
                    st.session_state.target_counter = counter_id
                    st.session_state.active_portal = "🛠️ Order Modification & Cancellation"
                    st.rerun()

            with col_rc2:
                st.markdown("### *👨‍🍳 Chef Kitchen Ticket (KOT)*")
                st.markdown(st.session_state.last_receipt['token_html'], unsafe_allow_html=True)
            
            if st.button("✖ Close Receipt & Start New Order"):
                st.session_state.last_receipt = None
                st.rerun()
            st.markdown("---")

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
                                
                                if item_info.get("image") is not None:
                                    st.image(item_info["image"], use_container_width=True, height=75)
                                else:
                                    icon = item_info.get("icon", "☕")
                                    st.markdown(f"<div style='font-size: 32px; margin-bottom: 4px;'>{icon}</div>", unsafe_allow_html=True)
                                    
                                st.markdown(f"<h4 style='margin: 2px 0; font-size: 13px; color: #000 !important;'>{item_name}</h4>", unsafe_allow_html=True)
                                st.markdown(f"<p style='margin: 0 0 2px 0; color: #556B2F !important; font-weight: bold; font-size: 13px;'>₹{item_info['price']:.2f}</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='margin: 0 0 6px 0; color: #666 !important; font-size: 11px;'>Stock: <b>{item_info['stock']}</b></p>", unsafe_allow_html=True)
                                
                                if item_info['stock'] > 0:
                                    if st.button("Add", key=f"counter_add_{item_name}", use_container_width=True):
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
                                    st.error("Out")
                                    
                                st.markdown('</div>', unsafe_allow_html=True)

        with col_cart:
            st.subheader("🛒 *Checkout*")
            st.markdown('<div class="cart-box">', unsafe_allow_html=True)
            
            if not st.session_state.cart:
                st.info("Your cart is empty. Tap menu items.")
            else:
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df[['Item', 'Qty', 'Total']], hide_index=True, use_container_width=True)
                
                subtotal = sum(item['Total'] for item in st.session_state.cart)
                tax = subtotal * 0.05  # 5% GST
                grand_total = subtotal + tax
                
                st.divider()
                st.markdown(f"**Subtotal:** ₹{subtotal:.2f}")
                st.markdown(f"**GST (5%):** ₹{tax:.2f}")
                st.markdown(f"### *Grand Total:* ₹{grand_total:.2f}")
                
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
                st.subheader("💳 *Payment Mode*")
                payment_mode = st.radio("Choose Mode", ["💵 Cash", "📱 UPI QR", "💳 Card"], horizontal=True)
                
                cash_given = 0.0
                if payment_mode == "📱 UPI QR":
                    st.markdown(f"""
                    <div style="background-color: #fdfbf7; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #d5ded0; margin-bottom: 8px;">
                        <p style="margin: 0; font-weight: bold; color: #000 !important; font-size: 14px;">Scan QR to Pay</p>
                        <p style="margin: 2px 0; font-size: 12px; color: #444 !important;">UPI ID: <b>{upi_id}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if qr_image_file is not None:
                        st.image(Image.open(qr_image_file), width=110)
                
                elif payment_mode == "💳 Card":
                    st.markdown(f"""
                    <div style="background-color: #fdfbf7; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #d5ded0; margin-bottom: 8px;">
                        <p style="margin: 0; font-weight: bold; color: #000 !important; font-size: 14px;">Swipe / Tap Card</p>
                        <p style="margin: 2px 0; font-size: 11px; color: #555 !important;">Connected billing card machine terminal.</p>
                    </div>
                    """, unsafe_allow_html=True)

                elif payment_mode == "💵 Cash":
                    cash_given = st.number_input("Cash Tendered (₹)", min_value=0.0, value=float(grand_total), step=10.0)
                    change_due = cash_given - grand_total
                    if change_due >= 0:
                        st.success(f"**Change:** ₹{change_due:.2f}")
                    else:
                        st.error(f"**Shortage:** ₹{abs(change_due):.2f}")

                st.write("")
                clean_payment_mode = "Cash" if "Cash" in payment_mode else ("UPI QR" if "UPI" in payment_mode else "Card")

                if st.button("✅ Complete Order & Print", type="primary", use_container_width=True):
                    if clean_payment_mode == "Cash" and cash_given < grand_total:
                        st.error("Insufficient cash given!")
                    else:
                        current_cart_snapshot = list(st.session_state.cart)
                        order_time = log_sale(grand_total, clean_payment_mode, current_cart_snapshot, counter_id)
                        
                        receipt_html = f"""
                        <div class="receipt-box">
                            <h2 style="text-align: center; margin: 0; color: #556B2F !important;">GREEN FUSION</h2>
                            <p style="text-align: center; font-size: 11px; margin: 2px 0; font-style: italic;">Bite & Sip by Dayals</p>
                            <p style="text-align: center; font-size: 11px; color: #555;">Terminal: {counter_id} | Date: {order_time}</p>
                            <p style="text-align: center; font-size: 11px; color: #555;">Payment Mode: <b>{clean_payment_mode}</b></p>
                            <hr style="border: 0.5px dashed #556B2F;">
                        """
                        for item in current_cart_snapshot:
                            receipt_html += f"<p>{item['Qty']}x {item['Item']} - ₹{item['Total']:.2f}</p>"
                        
                        receipt_html += f"""
                            <hr style="border: 0.5px dashed #556B2F;">
                            <p>Subtotal - ₹{subtotal:.2f}</p>
                            <p>GST (5%) - ₹{tax:.2f}</p>
                            <h3 style="color: #1a1a1a !important;">Total: ₹{grand_total:.2f}</h3>
                        """
                        if clean_payment_mode == "Cash":
                            receipt_html += f"""
                            <p>Cash Given - ₹{cash_given:.2f}</p>
                            <p>Change Returned - ₹{cash_given - grand_total:.2f}</p>
                            """
                        receipt_html += f"""
                            <p style="text-align: center; margin-top: 15px; font-size: 11px;">*** THANK YOU! VISIT AGAIN ***</p>
                        </div>
                        """

                        token_html = f"""
                        <div class="chef-token">
                            <h3 style="text-align: center; margin: 0; color: #000 !important;">KITCHEN ORDER TICKET</h3>
                            <p style="text-align: center; font-size: 12px; margin: 5px 0;">Terminal: {counter_id} | Time: {order_time}</p>
                            <hr style="border: 1px solid #333;">
                            <ul style="list-style-type: none; padding: 0;">
                        """
                        for item in current_cart_snapshot:
                            token_html += f"<li style='font-size: 15px; font-weight: bold; margin-bottom: 4px;'>▪ {item['Qty']}x {item['Item']}</li>"
                        token_html += """
                            </ul>
                            <hr style="border: 1px solid #333;">
                            <p style="text-align: center; font-size: 11px; font-weight: bold; margin: 0;">--- PREPARE IMMEDIATELY ---</p>
                        </div>
                        """

                        st.session_state.last_receipt = {
                            "receipt_html": receipt_html,
                            "token_html": token_html,
                            "order_time": order_time
                        }
                        st.session_state.cart = []
                        st.rerun()
                        
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# GATEWAY 2: ORDER MODIFICATION & CANCELLATION
# ==========================================
elif st.session_state.active_portal == "🛠️ Order Modification & Cancellation":
    st.title("🛠️ *Order Item Modification & Partial Refund Center*")
    st.markdown("*Green Fusion - Bite & Sip by Dayals*")
    
    col_mod_login, col_mod_empty = st.columns([1, 1])
    with col_mod_login:
        default_counter = st.session_state.get('target_counter', 'Counter 1')
        counter_id = st.text_input("Enter Counter Number / Staff ID", default_counter, key="mod_counter_id")
        
    st.divider()
    
    if counter_id:
        st.markdown('<div class="mod-container">', unsafe_allow_html=True)
        st.markdown("### *🔄 Item-Level Cancellation & Refund Manager*")
        st.write("Select a specific order, choose the exact item to cancel or modify, and request admin authorization.")
        
        df_all_items = load_item_sales_data()
        if not df_all_items.empty:
            counter_orders = df_all_items[df_all_items['counter'] == counter_id]
            if not counter_orders.empty:
                st.markdown("#### *📋 Recent Orders & Status Tracker*")
                summary_df = counter_orders[['date', 'item_name', 'quantity', 'unit_price', 'subtotal', 'status']]
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
                
                approved_orders = counter_orders[counter_orders['status'] == "Approved & Modified"]
                if not approved_orders.empty:
                    st.markdown("---")
                    st.warning("⚠️ **Admin Approved Item Modifications Ready for Partial Refund:**")
                    
                    for idx, row in approved_orders.iterrows():
                        st.markdown(f"**Order:** {row['date']} | **Item:** {row['quantity']}x {row['item_name']} | **Refund Due:** ₹{row['subtotal']:.2f}")
                        if st.button(f"✅ Process Refund for {row['item_name']} ({row['date']})", key=f"proc_ref_{row['date']}_{row['item_name']}"):
                            supabase.table("order_items").update({"status": "Refunded & Closed"}).eq("date", row['date']).eq("counter", counter_id).eq("item_name", row['item_name']).execute()
                            
                            item_name = row['item_name']
                            qty = row['quantity']
                            if item_name in st.session_state.custom_menu:
                                st.session_state.custom_menu[item_name]['stock'] += qty
                                
                            sales_res = supabase.table("sales").select("*").eq("date", row['date']).execute()
                            if sales_res.data:
                                old_total = float(sales_res.data[0]['total'])
                                new_total = max(0.0, old_total - float(row['subtotal']))
                                supabase.table("sales").update({"total": new_total}).eq("date", row['date']).execute()

                            st.success(f"Successfully refunded ₹{row['subtotal']:.2f} for {item_name} and adjusted true sales & inventory!")
                            st.rerun()

                st.markdown("---")
                st.markdown("#### *📤 Request Item-Level Change or Cancellation*")
                active_orders = counter_orders[counter_orders['status'] == "Completed"]
                if not active_orders.empty:
                    active_order_times = sorted(active_orders['date'].astype(str).unique(), reverse=True)
                    
                    target_time = st.session_state.get('target_mod_time')
                    default_time_index = 0
                    if target_time in active_order_times:
                        default_time_index = active_order_times.index(target_time)
                        st.session_state.target_mod_time = None

                    selected_order_time = st.selectbox("Select Order Timestamp", active_order_times, index=default_time_index, key="sel_ord_time")
                    
                    order_items_subset = active_orders[active_orders['date'].astype(str) == selected_order_time]
                    item_choices = order_items_subset['item_name'].tolist()
                    
                    selected_item_to_mod = st.selectbox("Select Exact Item to Cancel / Modify", item_choices, key="sel_item_mod")
                    mod_reason = st.text_area("Reason for Item Cancellation/Change", placeholder="e.g., Customer canceled this burger / wanted fries instead...")
                    
                    if st.button("📤 Submit Item Modification Request"):
                        if mod_reason.strip() != "":
                            supabase.table("order_items").update({
                                "status": "Modification Requested",
                                "modification_reason": mod_reason
                            }).eq("date", selected_order_time).eq("counter", counter_id).eq("item_name", selected_item_to_mod).execute()
                            st.success(f"Modification request for '{selected_item_to_mod}' sent to Admin successfully!")
                            st.rerun()
                        else:
                            st.error("Please provide a reason for the modification.")
                else:
                    st.info("No active completed orders available for modification.")
            else:
                st.info("No orders found for this counter yet.")
        else:
            st.info("No orders recorded in the system yet.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# GATEWAY 3: MENU DISPLAY SCREEN (CUSTOMER VIEW)
# ==========================================
elif st.session_state.active_portal == "🍽️ Menu Display Screen":
    if logo_img_obj is not None:
        col_m_logo, col_m_title = st.columns([1, 4])
        with col_m_logo:
            st.image(logo_img_obj, width=110)
        with col_m_title:
            st.title("*Green Fusion - Live Digital Menu*")
            st.markdown("*Bite & Sip by Dayals*")
    else:
        st.title("*Green Fusion - Live Digital Menu*")
    
    categories = ["All Items", "Burgers", "Sides", "Snacks", "Beverages", "Desserts"]
    selected_cat = st.selectbox("Filter Category", categories)
    
    st.divider()
    
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
                        if item_info.get("image") is not None:
                            st.image(item_info["image"], use_container_width=True, height=85)
                        else:
                            icon = item_info.get("icon", "☕")
                            st.markdown(f"<div style='font-size: 40px; margin-bottom: 6px;'>{icon}</div>", unsafe_allow_html=True)
                        st.markdown(f"<h3 style='margin: 4px 0; color: #000 !important; font-size: 16px;'>{item_name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin: 0; color: #556B2F !important; font-weight: bold; font-size: 16px;'>₹{item_info['price']:.2f}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin: 4px 0 0 0; color: #666; font-size: 11px;'>Category: {item_info['category']}</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# GATEWAY 4: KITCHEN DISPLAY SCREEN (KDS)
# ==========================================
elif st.session_state.active_portal == "👨‍🍳 Kitchen Display (KDS)":
    st.title("*👨‍🍳 Live Kitchen Display Screen (KDS)*")
    st.markdown("*Green Fusion - Bite & Sip by Dayals*")
    
    df_items = load_item_sales_data()
    if df_items.empty:
        st.info("No active orders in the kitchen queue.")
    else:
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_orders = df_items[df_items['Day'].astype(str) == today_str]
        
        if today_orders.empty:
            st.info("No orders placed yet for today.")
        else:
            st.markdown("### *🔥 Live Order Tickets*")
            grouped_orders = today_orders.groupby(['date', 'counter'])
            
            for (order_time, counter), group in grouped_orders:
                active_group = group[group['status'] != "Refunded & Closed"]
                if active_group.empty:
                    continue
                    
                with st.expander(f"📦 Order from {counter} at {order_time}", expanded=True):
                    col_k1, col_k2 = st.columns([2, 1])
                    with col_k1:
                        for idx, row in active_group.iterrows():
                            status_badge = "🔴 ITEM MOD REQUEST" if row['status'] == "Modification Requested" else ("🟡 APPROVED (REFUND PENDING)" if row['status'] == "Approved & Modified" else "🟢 Active")
                            st.markdown(f"<p style='font-size: 16px; font-weight: bold; margin: 2px 0;'>▪ {row['quantity']}x {row['item_name']} | <span style='color:red;'>{status_badge}</span></p>", unsafe_allow_html=True)
                    with col_k2:
                        st.markdown(f"<span style='background-color: #fffef0; padding: 6px 12px; border-radius: 6px; border: 1px solid #333; font-weight: bold; font-size: 12px;'>Status: Active Order</span>", unsafe_allow_html=True)

# ==========================================
# GATEWAY 5: ADMIN MANAGEMENT LOGIN
# ==========================================
elif st.session_state.active_portal == "🔑 Admin Management Login":
    st.title("*🔑 Admin Management Login Gateway*")
    st.markdown("*Green Fusion - Bite & Sip by Dayals*")
    
    admin_password = st.text_input("Enter Master Admin Password", type="password")
    actual_admin_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
    if admin_password == actual_admin_password:
        st.success("Master Admin Authentication Successful.")
        st.divider()
        
        admin_action = st.selectbox("Select Admin Control Module", [
            "➕ Add New Menu Item", 
            "✏️ Edit or Remove Menu Items",
            "🛡️ Review Order Modification Requests",
            "📊 Business Revenue & Daily Item Reports"
        ])
        
        if admin_action == "➕ Add New Menu Item":
            st.subheader("*Add New Item to POS Menu*")
            
            with st.form("admin_menu_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    new_item_name = st.text_input("Item Name (e.g., Cold Brew Coffee)")
                    new_item_cat = st.selectbox("Category", ["Burgers", "Sides", "Snacks", "Beverages", "Desserts"])
                    new_item_price = st.number_input("Price (₹)", min_value=1.0, value=150.0)
                with col_f2:
                    initial_stock = st.number_input("Initial Stock Quantity", min_value=1, value=50)
                    new_item_icon = st.selectbox("Emoji Icon", ["🍔", "🍟", "☕", "🥤", "🥐", "🍦", "🍕", "🥪", "🍰", "🍵", "🍩", "🌮"])
                    new_item_image = st.file_uploader("Optional Custom Photo (PNG, JPG)", type=["png", "jpg", "jpeg"])
                
                submit_btn = st.form_submit_button("➕ Add Item to POS Menu")
                
                if submit_btn:
                    if new_item_name:
                        img_to_store = Image.open(new_item_image) if new_item_image else None
                        st.session_state.custom_menu[new_item_name] = {
                            "category": new_item_cat,
                            "price": new_item_price,
                            "stock": initial_stock,
                            "icon": new_item_icon,
                            "image": img_to_store
                        }
                        st.success(f"Successfully added '{new_item_name}' to the live POS menu!")
                    else:
                        st.error("Please enter a valid item name.")

        elif admin_action == "✏️ Edit or Remove Menu Items":
            st.subheader("*Edit or Remove Existing Menu Items*")
            
            if not st.session_state.custom_menu:
                st.info("No menu items available to edit.")
            else:
                selected_edit_item = st.selectbox("Select Item to Modify", list(st.session_state.custom_menu.keys()))
                current_data = st.session_state.custom_menu[selected_edit_item]
                
                with st.form("edit_menu_form"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        edited_name = st.text_input("Item Name", value=selected_edit_item)
                        categories_list = ["Burgers", "Sides", "Snacks", "Beverages", "Desserts"]
                        cat_index = categories_list.index(current_data["category"]) if current_data["category"] in categories_list else 0
                        edited_cat = st.selectbox("Category", categories_list, index=cat_index)
                        edited_price = st.number_input("Price (₹)", min_value=1.0, value=float(current_data["price"]))
                    with col_e2:
                        edited_stock = st.number_input("Stock Quantity", min_value=0, value=int(current_data["stock"]))
                        icons_list = ["🍔", "🍟", "☕", "🥤", "🥐", "🍦", "🍕", "🥪", "🍰", "🍵", "🍩", "🌮"]
                        icon_index = icons_list.index(current_data["icon"]) if current_data.get("icon") in icons_list else 0
                        edited_icon = st.selectbox("Emoji Icon", icons_list, index=icon_index)
                        edited_image = st.file_uploader("Update Custom Photo (PNG, JPG)", type=["png", "jpg", "jpeg"])
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        save_changes = st.form_submit_button("💾 Save Changes")
                    with col_btn2:
                        delete_item = st.form_submit_button("🗑️ Delete Item")
                        
                    if save_changes:
                        if edited_name:
                            if edited_name != selected_edit_item:
                                del st.session_state.custom_menu[selected_edit_item]
                            
                            img_to_store = Image.open(edited_image) if edited_image else current_data.get("image")
                            st.session_state.custom_menu[edited_name] = {
                                "category": edited_cat,
                                "price": edited_price,
                                "stock": edited_stock,
                                "icon": edited_icon,
                                "image": img_to_store
                            }
                            st.success(f"Successfully updated '{edited_name}'!")
                            st.rerun()
                        else:
                            st.error("Item name cannot be empty.")
                            
                    if delete_item:
                        del st.session_state.custom_menu[selected_edit_item]
                        st.success(f"Successfully removed '{selected_edit_item}' from the menu.")
                        st.rerun()

        elif admin_action == "🛡️ Review Order Modification Requests":
            st.subheader("*🛡️ Pending Item Modification Requests*")
            df_items = load_item_sales_data()
            
            if df_items.empty:
                st.info("No orders found.")
            else:
                pending_mods = df_items[df_items['status'] == "Modification Requested"]
                if pending_mods.empty:
                    st.success("No pending item modification requests from counters.")
                else:
                    st.warning("Review specific item requests submitted by counter staff below:")
                    for idx, row in pending_mods.iterrows():
                        with st.container():
                            st.markdown(f"**Counter:** {row['counter']} | **Timestamp:** {row['date']}")
                            st.markdown(f"📦 **Requested Item Change:** `{row['quantity']}x {row['item_name']}` (Subtotal: ₹{row['subtotal']:.2f})")
                            st.markdown(f"📝 **Reason:** `{row['modification_reason']}`")
                            
                            col_app1, col_app2 = st.columns(2)
                            with col_app1:
                                if st.button(f"✅ Approve Item Modification", key=f"app_{row['date']}_{row['item_name']}"):
                                    supabase.table("order_items").update({"status": "Approved & Modified"}).eq("date", row['date']).eq("counter", row['counter']).eq("item_name", row['item_name']).execute()
                                    st.success(f"Approved change for {row['item_name']}! Counter can now process the partial refund.")
                                    st.rerun()
                            with col_app2:
                                if st.button(f"❌ Reject", key=f"rej_{row['date']}_{row['item_name']}"):
                                    supabase.table("order_items").update({"status": "Completed"}).eq("date", row['date']).eq("counter", row['counter']).eq("item_name", row['item_name']).execute()
                                    st.info("Request rejected. Order restored.")
                                    st.rerun()
                            st.divider()

        elif admin_action == "📊 Business Revenue & Daily Item Reports":
            st.subheader("*📊 Detailed Item Sales & Daily Revenue Report*")
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

                st.markdown("### *💰 Revenue Breakdown by Payment Mode*")
                pm1, pm2, pm3, pm4 = st.columns(4)
                pm1.metric("💵 Cash", f"₹{cash_total:,.2f}")
                pm2.metric("📱 UPI", f"₹{upi_total:,.2f}")
                pm3.metric("💳 Card", f"₹{card_total:,.2f}")
                pm4.metric("🌟 Total", f"₹{overall_total:,.2f}")
                
                st.divider()

                st.markdown("### *📋 Daily Itemized Sales Report*")
                if not df_items.empty:
                    valid_items = df_items[df_items['status'] != "Refunded & Closed"]
                    available_days = sorted(valid_items['Day'].astype(str).unique(), reverse=True)
                    selected_day = st.selectbox("Select Date for Item Breakdown", available_days)
                    
                    day_filtered_items = valid_items[valid_items['Day'].astype(str) == selected_day]
                    
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

                st.markdown("### *📥 Download System Reports*")
                excel_file = convert_dfs_to_excel(df_sales, df_items)
                st.download_button(
                    label="📥 Download Comprehensive Sales & Items Report (Excel)",
                    data=excel_file,
                    file_name=f"green_fusion_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
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
                st.subheader("*⚡ Quick Performance Metrics*")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Lifetime Revenue", f"₹{overall_total:,.2f}")
                m2.metric("Average Daily Sales", f"₹{df_sales_indexed.resample('D').sum()['total'].mean():,.2f}")
                m3.metric("Highest Single Bill", f"₹{df_sales['total'].max():,.2f}")
    else:
        if admin_password != "":
            st.error("Incorrect Admin Password.")
        else:
            st.info("🔒 Please enter the master password to unlock admin privileges.")