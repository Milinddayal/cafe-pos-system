import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import plotly.express as px
import base64
import ast
import json
from html import escape
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image
from supabase import create_client, Client
import os
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Green Fusion - POS System", page_icon="☕", layout="wide")

LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_local_time():
    return datetime.now(LOCAL_TIMEZONE)


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

if 'order_submitted' not in st.session_state:
    st.session_state.order_submitted = False

if 'last_receipt' not in st.session_state:
    st.session_state.last_receipt = None

if 'order_completed' not in st.session_state:
    st.session_state.order_completed = bool(st.session_state.last_receipt)

if 'order_saved' not in st.session_state:
    st.session_state.order_saved = bool(st.session_state.last_receipt)

if 'current_bill' not in st.session_state:
    st.session_state.current_bill = (
        st.session_state.last_receipt.get('bill_number')
        if st.session_state.last_receipt else None
    )

if 'order_history' not in st.session_state:
    st.session_state.order_history = []

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

if '_session_sales_reset_applied' not in st.session_state:
    st.session_state.sales_history = []
    st.session_state.order_history = []
    st.session_state._session_sales_reset_applied = True

if 'target_mod_time' not in st.session_state:
    st.session_state.target_mod_time = None

if 'active_portal' not in st.session_state:
    st.session_state.active_portal = "🛒 Counter Staff Billing"

# --- DIRECT LINK / URL ROUTING ---
# Allows direct access via ?view=menu or ?view=kds
if "view" in st.query_params:
    requested_view = st.query_params.get("view", "").lower()
    if requested_view == "menu":
        st.session_state.active_portal = "🍽️ Menu Display Screen"
    elif requested_view == "kds":
        st.session_state.active_portal = "👨‍🍳 Kitchen Display (KDS)"

# --- FULL SCREEN / CLEAN APP VIEW MODE ---
# If you open your app with ?view=kiosk in the URL, it hides all Streamlit headers and toolbars automatically
is_kiosk = st.query_params.get("view") == "kiosk"

if is_kiosk:
    st.markdown("""
        <style>
            /* Hide Streamlit header, menu hamburger, and footer */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stSidebar"] {display: none;}
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                max-width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- SMART ICON GENERATOR (Category Based) ---
def get_smart_icon(category_name):
    icons = {
        "Gelato Amor": "🍨",
        "Premium Shakes": "🥤",
        "Sandwiches": "🥪",
        "French Fries": "🍟",
        "Pasta & Soup": "🍝",
        "Local Bites": "🍛",
        "Premium Tea": "🍵",
        "Warm Coffee": "☕",
        "Cold Brews": "🧊",
        "Mocktails": "🍹",
        "Fresh Juices": "🧃"
    }
    # Returns a default plate icon if the category isn't found, preventing crashes!
    return icons.get(category_name, "🍽️")

@st.cache_data(ttl=300)
def fetch_menu_items(_sb: Client):
    response = _sb.table("menu_items").select("*").execute()
    return response.data or []


# --- HARDCODED ROBUST MENU FALLBACK ---
def fetch_fallback_menu():
    return {
        "Pomegranate": {"category": "Fresh Juices", "price": 99.00, "stock": 50},
        "Malta": {"category": "Fresh Juices", "price": 119.00, "stock": 50},
        "Mosambi": {"category": "Fresh Juices", "price": 79.00, "stock": 50},
        "Mix Fruit": {"category": "Fresh Juices", "price": 79.00, "stock": 50},
        "Orange": {"category": "Fresh Juices", "price": 119.00, "stock": 50},
        "Pineapple": {"category": "Fresh Juices", "price": 99.00, "stock": 50},
        "Fruit Chart": {"category": "Fruit Chart", "price": 69.00, "stock": 50},
        "Vada Paw": {"category": "Snacks", "price": 59.00, "stock": 50},
        "Poha": {"category": "Snacks", "price": 69.00, "stock": 50},
        # --- French Fries Section ---
        "Fries": {"category": "French Fries", "price": 79.00, "stock": 50},
        "Peri Peri Fries": {"category": "French Fries", "price": 89.00, "stock": 50},
        "Cheese Fries": {"category": "French Fries", "price": 99.00, "stock": 50},
        # --- Potato Wedges Section ---
        "Potato Wedges": {"category": "Potato Wedges", "price": 89.00, "stock": 50},
        "Peri Peri Potato Wedges": {"category": "Potato Wedges", "price": 99.00, "stock": 50},
        "Cheese Potato Wedges": {"category": "Potato Wedges", "price": 109.00, "stock": 50},
        # --- Tea Section ---
        "Masala Tea": {"category": "Tea", "price": 59.00, "stock": 50},
        "Ice Tea": {"category": "Tea", "price": 79.00, "stock": 50},
        "Green Tea": {"category": "Tea", "price": 59.00, "stock": 50},
        # ----------------------------
        "White Sauce Pasta": {"category": "Pasta", "price": 139.00, "stock": 50},
        "Red Sauce Pasta": {"category": "Pasta", "price": 119.00, "stock": 50},
        "Dry Maggiee": {"category": "Maggiee", "price": 99.00, "stock": 50},
        "Soupy Maggiee": {"category": "Maggiee", "price": 99.00, "stock": 50},
        "Veg Sandwich": {"category": "Sandwich", "price": 79.00, "stock": 50},
        "Cheese Sandwich": {"category": "Sandwich", "price": 99.00, "stock": 50},
        "Paneer Sandwich": {"category": "Sandwich", "price": 119.00, "stock": 50},
        "Sip the Lip": {"category": "Mocktails", "price": 139.00, "stock": 50},
        "Green Forest": {"category": "Mocktails", "price": 119.00, "stock": 50},
        "Virgin Mojito": {"category": "Mocktails", "price": 99.00, "stock": 50},
        "Green Apple": {"category": "Mocktails", "price": 119.00, "stock": 50},
        "Ocean Blue": {"category": "Mocktails", "price": 139.00, "stock": 50},
        "Guava Pink": {"category": "Mocktails", "price": 149.00, "stock": 50},
        "Kiwi Crush": {"category": "Mocktails", "price": 129.00, "stock": 50},
        "The Red Call": {"category": "Mocktails", "price": 129.00, "stock": 50},
        "Irris Coffee": {"category": "Mocktails", "price": 139.00, "stock": 50},
        "The Yellow Call": {"category": "Mocktails", "price": 139.00, "stock": 50},
        "Pineapple Pastry": {"category": "Pastry Section", "price": 69.00, "stock": 50},
        "Black Forest Pastry": {"category": "Pastry Section", "price": 69.00, "stock": 50},
        "Red Velvet Pastry": {"category": "Pastry Section", "price": 69.00, "stock": 50},
        "Chocolate Pastry": {"category": "Pastry Section", "price": 69.00, "stock": 50},
        "Veg Soup": {"category": "Soup", "price": 79.00, "stock": 50},
        "Sweet Corn Soup": {"category": "Soup", "price": 89.00, "stock": 50},
        "Tomato Soup": {"category": "Soup", "price": 89.00, "stock": 50},
        "Crispy Sweet Corn Chat": {"category": "Sweet Corn Chart", "price": 99.00, "stock": 50},
        "Chocolate Shake": {"category": "Shakes Section", "price": 99.00, "stock": 50},
        "Strawberry Shake": {"category": "Shakes Section", "price": 99.00, "stock": 50},
        "Protein Shake": {"category": "Shakes Section", "price": 129.00, "stock": 50},
        "Banana Shake": {"category": "Shakes Section", "price": 89.00, "stock": 50},
        "Sweet Lassi": {"category": "Shakes Section", "price": 79.00, "stock": 50},
        "Butter Scotch": {"category": "Ice Cream", "price": 79.00, "stock": 50},
        "Vanilla": {"category": "Ice Cream", "price": 79.00, "stock": 50},
        "Chocolate": {"category": "Ice Cream", "price": 79.00, "stock": 50},
        "Strawberry": {"category": "Ice Cream", "price": 79.00, "stock": 50},
        "Kesar Pista": {"category": "Ice Cream", "price": 79.00, "stock": 50},
        "Hot Coffee": {"category": "Coffee", "price": 59.00, "stock": 50},
        "Lavazza Gusto": {"category": "Coffee", "price": 79.00, "stock": 50},
        "Barista Aroma Intenso": {"category": "Coffee", "price": 79.00, "stock": 50},
        "Chocolate Coffee": {"category": "Coffee", "price": 79.00, "stock": 50},
        "Espresso": {"category": "Coffee", "price": 79.00, "stock": 50},
        "Cold Coffee": {"category": "Cold Coffee", "price": 89.00, "stock": 50},
        "Espresso Bitter Cold": {"category": "Cold Coffee", "price": 109.00, "stock": 50},
        "Chocolate Coffee (Cold)": {"category": "Cold Coffee", "price": 129.00, "stock": 50},
        "Lavazza Gusto (Cold)": {"category": "Cold Coffee", "price": 129.00, "stock": 50},
        "Barista Aroma Intenso (Cold)": {"category": "Cold Coffee", "price": 129.00, "stock": 50},
        "Water Bottle (Custom MRP)": {"category": "Packed Items", "price": 20.00, "stock": 100},
        "Cold Drink Can (Custom MRP)": {"category": "Packed Items", "price": 40.00, "stock": 100},
        "Cold Drink Bottle (Custom MRP)": {"category": "Packed Items", "price": 20.00, "stock": 100},
        "Drink Can": {"category": "Packed Items", "price": 35.00, "stock": 100},
        "Token 1": {"category": "Tokens", "price": 20.00, "stock": 100},
        "Token 2 (₹30)": {"category": "Tokens", "price": 30.00, "stock": 100},
        "Token 2 (₹40)": {"category": "Tokens", "price": 40.00, "stock": 100}
        
    }


def fetch_live_menu(sb: Client):
    menu_items = fetch_menu_items(sb)
    if not menu_items:
        return fetch_fallback_menu()

    live_menu = {}
    for item in menu_items:
        item_name = item["name"]
        category = item.get("category") or "Uncategorized"
        live_menu[item_name] = {
            "category": category,
            "price": float(item["price"]),
            "stock": int(item.get("stock") or 0),
            "icon": item.get("icon") or get_smart_icon(category)
        }
    return live_menu


current_menu = fetch_live_menu(supabase)
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
def get_next_bill_number(sb):
    today_str = get_local_time().strftime('%Y%m%d')
    response = (
        sb.table('orders')
        .select('bill_number')
        .like('bill_number', f"GF-{today_str}-%")
        .execute()
    )
    existing_bills = response.data or []
    existing_sequences = []
    for bill in existing_bills:
        bill_number = str(bill.get("bill_number", ""))
        sequence = bill_number.rsplit("-", 1)[-1]
        if sequence.isdigit():
            existing_sequences.append(int(sequence))
    next_seq = max(existing_sequences, default=0) + 1
    return f"GF-{today_str}-{next_seq:03d}"


def render_printable_bill(bill_number, cart_items, total_amount, order_time=None):
    st.markdown("""
        <style>
        .printable-receipt {
            border: 1px dashed #ccc !important;
            border-radius: 5px !important;
            width: 300px;
            max-width: 100%;
            box-sizing: border-box;
            margin: 0 auto !important;
            padding: 15px !important;
            background: white !important;
            color: black !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        @media print {
            body * {
                visibility: hidden !important;
            }
            header,
            footer,
            [data-testid="stSidebar"],
            button,
            .stButton,
            .stAlert {
                display: none !important;
            }
            .printable-receipt,
            .printable-receipt * {
                visibility: visible !important;
            }
            .printable-receipt {
                display: block !important;
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 80mm !important;
                max-width: 80mm !important;
                box-sizing: border-box !important;
                margin: 0 !important;
                padding: 5mm !important;
                background: white !important;
                color: black !important;
                font-family: 'Courier New', Courier, monospace !important;
                font-size: 12px !important;
                border: none !important;
                border-radius: 0 !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    item_lines = []
    for item in cart_items:
        item_name = escape(str(item.get("Item", item.get("item", "Item"))))
        quantity = item.get("Qty", item.get("qty", 0))
        line_total = item.get("Total", item.get("total"))
        if line_total is None:
            price = item.get("Price", item.get("price", 0))
            line_total = price * quantity
        item_lines.append(
            f"<p style='margin: 2px 0;'>{item_name} x{quantity} — "
            f"₹{float(line_total):.2f}</p>"
        )

    receipt_time = order_time or get_local_time().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"""
        <div class="printable-receipt">
            <h3 style="text-align: center; margin: 0; font-size: 16px;">Green Fusion</h3>
            <p style="text-align: center; font-size: 10px; margin: 2px 0 10px 0;">Bite &amp; Sip by Dayals</p>
            <hr style="border-top: 1px dashed #000;">
            <p style="margin: 4px 0;"><b>Bill No:</b> {escape(str(bill_number))}</p>
            <p style="margin: 4px 0;"><b>Date:</b> {escape(str(receipt_time))}</p>
            <hr style="border-top: 1px dashed #000;">
            {''.join(item_lines)}
            <hr style="border-top: 1px dashed #000;">
            <h4 style="text-align: right; margin: 5px 0;">Total: ₹{float(total_amount):.2f}</h4>
            <p style="text-align: center; font-size: 10px; margin-top: 15px;">Thank you for visiting!<br>Please come again.</p>
        </div>
    """, unsafe_allow_html=True)

    st.info(
        "🖨️ **Print Receipt:** Press **Ctrl + P** (Windows) or **Cmd + P** (Mac) "
        "to print the thermal bill."
    )


def save_or_print_bill(bill_number, cart_items, total_amount, customer_name="Walk-in"):
    existing = (
        supabase.table("orders")
        .select("*")
        .eq("bill_number", bill_number)
        .execute()
    )
    if existing.data:
        st.info(f"Bill #{bill_number} is already recorded. Reusing the existing bill.")
        return existing.data[0]

    new_order = {
        "bill_number": bill_number,
        "total_amount": float(total_amount),
        "items": str(cart_items),
        "customer_name": customer_name,
        "payment_status": "Paid",
        "created_at": get_local_time().isoformat()
    }
    response = supabase.table("orders").insert(new_order).execute()
    if not response.data:
        raise RuntimeError("Supabase did not return the newly saved bill.")
    return response.data[0]


def build_bill_print_html(bill):
    items = bill.get("items", [])
    if isinstance(items, str):
        try:
            items = ast.literal_eval(items)
        except (SyntaxError, ValueError):
            items = []

    item_lines = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                quantity = escape(str(item.get("Qty", "")))
                name = escape(str(item.get("Item", "Item")))
                line_total = pd.to_numeric(item.get("Total", 0), errors="coerce")
                if pd.isna(line_total):
                    line_total = 0
                item_lines.append(
                    f"<p>{quantity}x {name}<span>₹{line_total:.2f}</span></p>"
                )
    if not item_lines:
        item_lines.append("<p>Item details unavailable</p>")

    bill_number = escape(str(bill.get("bill_number", bill.get("id", "N/A"))))
    customer_name = escape(str(bill.get("customer_name", "Walk-in")))
    payment_status = escape(str(bill.get("payment_status", "Paid")))
    total_amount = pd.to_numeric(bill.get("total_amount", 0), errors="coerce")
    if pd.isna(total_amount):
        total_amount = 0
    created_at = pd.to_datetime(bill.get("created_at"), errors="coerce")
    bill_time = created_at.strftime("%Y-%m-%d %H:%M:%S") if not pd.isna(created_at) else ""

    return f"""
        <div class="receipt">
            <h2>GREEN FUSION</h2>
            <p class="center">Bite &amp; Sip by Dayals</p>
            <hr>
            <p>Bill: {bill_number}</p>
            <p>Customer / Table: {customer_name}</p>
            <p>Date: {bill_time}</p>
            <p>Payment Status: {payment_status}</p>
            <hr>
            {''.join(item_lines)}
            <hr>
            <h3>Total: ₹{total_amount:.2f}</h3>
            <p class="center">*** THANK YOU! VISIT AGAIN ***</p>
            <button onclick="window.print()">Print Bill</button>
        </div>
        <style>
            body {{ font-family: 'Courier New', monospace; color: #000; }}
            .receipt {{ max-width: 320px; margin: auto; font-weight: bold; }}
            h2, .center {{ text-align: center; }}
            p span {{ float: right; }}
            button {{ width: 100%; padding: 10px; margin-top: 12px; cursor: pointer; }}
            @media print {{ button {{ display: none; }} }}
        </style>
    """


def log_sale(total_amount, payment_mode, cart_items, counter_id, bill_number):
    order_datetime = get_local_time()
    order_date = order_datetime.strftime('%Y-%m-%d %H:%M:%S')

    existing = (
        supabase.table("orders")
        .select("*")
        .eq("bill_number", bill_number)
        .execute()
    )
    if existing.data:
        st.info(f"Bill #{bill_number} is already recorded. Reusing the existing bill.")
        existing_created_at = existing.data[0].get("created_at")
        if existing_created_at:
            return pd.to_datetime(existing_created_at).strftime('%Y-%m-%d %H:%M:%S')
        return order_date

    supabase.table("orders").insert({
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

        item_name = item['Item']
        if item_name in current_menu:
            new_stock = max(0, current_menu[item_name]['stock'] - item['Qty'])
            supabase.table("menu_items").update({"stock": new_stock}).eq("name", item_name).execute()

    fetch_menu_items.clear()
    supabase.table("order_items").insert(items_to_insert).execute()
    save_or_print_bill(bill_number, cart_items, total_amount)

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


@st.fragment
def render_cart_section(sb: Client, counter_id: str, upi_id: str, qr_image_file):
    st.subheader("⚡ Quick Checkout")
    st.markdown('<div class="cart-box">', unsafe_allow_html=True)

    if not st.session_state.cart:
        st.info("Your cart is empty. Tap menu items.")
    else:
        cart_snapshot = list(st.session_state.cart)
        cart_df = pd.DataFrame(cart_snapshot)
        st.dataframe(cart_df[['Item', 'Qty', 'Total']], hide_index=True, width="stretch")

        subtotal = sum(item['Total'] for item in cart_snapshot)
        grand_total = subtotal

        st.divider()
        st.markdown(f"**Subtotal:** ₹{subtotal:.2f}")
        st.markdown(f"### *Grand Total:* ₹{grand_total:.2f}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button(
                "🗑️ Clear",
                width="stretch",
                disabled=st.session_state.order_saved
            ):
                st.session_state.cart = []
                st.session_state.order_submitted = False
                st.rerun(scope="fragment")
        with col_b:
            if st.button(
                "❌ Remove",
                width="stretch",
                disabled=st.session_state.order_saved
            ):
                if st.session_state.cart:
                    st.session_state.cart.pop()
                st.rerun(scope="fragment")

        st.divider()
        st.subheader("💳 *Payment Mode*")
        payment_mode = st.radio(
            "Choose Mode",
            ["💵 Cash", "📱 UPI QR", "💳 Card"],
            horizontal=True,
            disabled=st.session_state.order_saved
        )

        cash_given = 0.0
        if payment_mode == "📱 UPI QR":
            st.markdown(f"""
            <div style="background-color: #fdfbf7; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #d5ded0; margin-bottom: 8px;">
                <p style="margin: 0; font-weight: bold; color: #000 !important; font-size: 14px;">Scan QR to Pay</p>
                <p style="margin: 2px 0; font-size: 12px; color: #444 !important;">UPI ID: <b>{escape(str(upi_id))}</b></p>
            </div>
            """, unsafe_allow_html=True)
            if qr_image_file is not None:
                st.image(Image.open(qr_image_file), width=110)
        elif payment_mode == "💳 Card":
            st.markdown("""
            <div style="background-color: #fdfbf7; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #d5ded0; margin-bottom: 8px;">
                <p style="margin: 0; font-weight: bold; color: #000 !important; font-size: 14px;">Swipe / Tap Card</p>
                <p style="margin: 2px 0; font-size: 11px; color: #555 !important;">Connected billing card machine terminal.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            cash_given = st.number_input(
                "Cash Tendered (₹)",
                min_value=0.0,
                value=float(grand_total),
                step=10.0,
                disabled=st.session_state.order_saved
            )
            change_due = cash_given - grand_total
            if change_due >= 0:
                st.success(f"**Change:** ₹{change_due:.2f}")
            else:
                st.error(f"**Shortage:** ₹{abs(change_due):.2f}")

        st.write("")
        clean_payment_mode = (
            "Cash" if "Cash" in payment_mode
            else ("UPI QR" if "UPI" in payment_mode else "Card")
        )

        if st.button(
            "🚀 Complete Order & Print",
            type="primary",
            width="stretch",
            key="complete_order_btn"
        ):
            if st.session_state.order_saved:
                st.info("This order is already saved. Use the print buttons below.")
            elif st.session_state.order_submitted:
                st.info("This order is already being saved.")
            elif clean_payment_mode == "Cash" and cash_given < grand_total:
                st.error("Insufficient cash given!")
            else:
                st.session_state.order_submitted = True
                current_cart_snapshot = list(st.session_state.cart)
                try:
                    with st.spinner("Saving order to Supabase..."):
                        current_bill_no = get_next_bill_number(sb)
                        order_time = log_sale(
                            grand_total,
                            clean_payment_mode,
                            current_cart_snapshot,
                            counter_id,
                            current_bill_no
                        )
                except Exception as e:
                    st.session_state.order_submitted = False
                    st.error(f"Order could not be saved to Supabase: {e}")
                    return

                bill_items = "".join(
                    f"<p style='font-weight: bold;'>{item['Qty']}x "
                    f"{escape(str(item['Item']))} — ₹{item['Total']:.2f}</p>"
                    for item in current_cart_snapshot
                )
                cash_details = ""
                if clean_payment_mode == "Cash":
                    cash_details = (
                        f"<p style='font-weight: bold;'>Cash Given: ₹{cash_given:.2f}</p>"
                        f"<p style='font-weight: bold;'>Change Due: "
                        f"₹{cash_given - grand_total:.2f}</p>"
                    )

                kot_items = "".join(
                    f"<li style='font-size: 14px; font-weight: 900; margin-bottom: 4px;'>"
                    f"▪ {item['Qty']}x {escape(str(item['Item']))}</li>"
                    for item in current_cart_snapshot
                )
                direct_print_html = f"""
                <div class="print-controls" style="text-align: center; width: 100%; margin: 8px 0; display: flex; justify-content: center; gap: 10px;">
                    <button onclick="printReceipt('bill')" style="background-color: #45552E; color: #FAF5EA; padding: 10px 16px; font-size: 14px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer;">🖨️ Print Bill</button>
                    <button onclick="printReceipt('bill-kot')" style="background-color: #8C6D46; color: #FAF5EA; padding: 10px 16px; font-size: 14px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer;">🖨️ Print Bill + KOT</button>
                </div>
                <div id="bill-only-section" style="width: 78mm; max-width: 80mm; margin: 0 auto; font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; line-height: 1.3; color: #000; background: #fff; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact;">
                    <h2 style="font-weight: 900; margin: 0 0 2px 0; text-align: center;">GREEN FUSION</h2>
                    <p style="text-align: center; font-size: 11px; margin: 2px 0; font-style: italic;">Bite & Sip by Dayals</p>
                    <hr style="border: 0.5px dashed #000;">
                    <p style="text-align: center; font-size: 14px; font-weight: 900; margin: 4px 0;">BILL NO: {current_bill_no}</p>
                    <p style="text-align: center; font-size: 11px; color: #000; margin: 2px 0;">Terminal: {escape(str(counter_id))} | Date: {escape(str(order_time))}</p>
                    <p style="text-align: center; font-size: 11px; color: #000; margin: 2px 0;">Payment Mode: <b>{escape(str(clean_payment_mode))}</b></p>
                    <hr style="border: 1px solid #000;">
                    {bill_items}
                    <hr style="border: 1px solid #000;">
                    <p style="font-weight: bold;">Subtotal: ₹{subtotal:.2f}</p>
                    <h3 style="color: #000 !important; font-weight: 900;">Grand Total: ₹{grand_total:.2f}</h3>
                    {cash_details}
                    <p style="text-align: center; margin-top: 15px; font-size: 11px; font-weight: bold;">*** THANK YOU! VISIT AGAIN ***</p>
                </div>
                <div id="kot-only-section" style="width: 78mm; max-width: 80mm; margin: 0 auto; font-family: 'Courier New', Courier, monospace; font-size: 13px; font-weight: bold; line-height: 1.3; color: #000; background: #fff; padding: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact;">
                    <div style="page-break-before: always; break-before: page; padding-top: 10px;"></div>
                    <h3 style="text-align: center; margin: 0; font-weight: 900;">KITCHEN ORDER TICKET</h3>
                    <p style="text-align: center; font-size: 13px; font-weight: 900; margin: 3px 0;">BILL NO: {current_bill_no}</p>
                    <p style="text-align: center; font-size: 11px; margin: 3px 0; font-weight: bold;">Terminal: {escape(str(counter_id))} | Time: {escape(str(order_time))}</p>
                    <hr style="border: 1px solid #000;">
                    <ul style="list-style-type: none; padding: 0; margin: 5px 0;">{kot_items}</ul>
                    <hr style="border: 1px solid #000;">
                    <p style="text-align: center; font-size: 11px; font-weight: 900; margin: 0;">--- PREPARE IMMEDIATELY ---</p>
                </div>
                <script>
                    function printReceipt(mode) {{
                        const bill = document.getElementById("bill-only-section");
                        const kot = document.getElementById("kot-only-section");
                        const printWindow = window.open("", "_blank", "width=420,height=700");
                        if (!printWindow) {{
                            window.alert("The print window was blocked. Allow pop-ups for this POS, then try again.");
                            return;
                        }}

                        const receiptHtml = bill.outerHTML
                            + (mode === "bill-kot" ? kot.outerHTML : "");
                        printWindow.document.open();
                        printWindow.document.write(`<!DOCTYPE html>
                            <html>
                            <head>
                                <title>Green Fusion Receipt</title>
                                <style>
                                    @page {{ margin: 0; }}
                                    body {{
                                        margin: 0;
                                        padding: 5mm;
                                        color: #000;
                                        background: #fff;
                                        font-family: 'Courier New', Courier, monospace;
                                    }}
                                    #bill-only-section, #kot-only-section {{
                                        width: 78mm;
                                        max-width: 78mm;
                                        box-sizing: border-box;
                                    }}
                                    #kot-only-section {{
                                        page-break-before: always;
                                        break-before: page;
                                    }}
                                    @media screen {{
                                        body {{ padding: 12px; }}
                                    }}
                                </style>
                            </head>
                            <body>${{receiptHtml}}</body>
                            </html>`);
                        printWindow.document.close();
                        printWindow.addEventListener("afterprint", () => printWindow.close(), {{ once: true }});
                        printWindow.requestAnimationFrame(() => {{
                            printWindow.requestAnimationFrame(() => {{
                                printWindow.focus();
                                printWindow.print();
                            }});
                        }});
                    }}
                </script>
                """

                st.session_state.last_receipt = {
                    "receipt_html": direct_print_html,
                    "receipt_height": min(600, 460 + len(current_cart_snapshot) * 28),
                    "bill_number": current_bill_no,
                    "cart_items": current_cart_snapshot,
                    "total_amount": grand_total,
                    "token_html": "",
                    "order_time": order_time
                }
                st.session_state.current_bill = current_bill_no
                st.session_state.order_completed = True
                st.session_state.order_submitted = False
                st.session_state.order_saved = True
                st.rerun()

    if st.session_state.get('order_completed') and st.session_state.get('last_receipt'):
        receipt = st.session_state.last_receipt
        st.markdown("---")
        st.success(f"✅ Order saved successfully! Bill: {receipt['bill_number']}")
        components.html(
            receipt["receipt_html"],
            height=receipt["receipt_height"],
            scrolling=True
        )
        receipt_lines = [
            "GREEN FUSION",
            "Bite & Sip by Dayals",
            "----------------------------------",
            f"Bill No: {receipt['bill_number']}",
            f"Date: {receipt['order_time']}",
            "----------------------------------"
        ]
        for item in receipt['cart_items']:
            item_name = item.get("Item", item.get("item", "Item"))
            quantity = item.get("Qty", item.get("qty", 0))
            item_total = item.get("Total", item.get("total"))
            if item_total is None:
                price = item.get("Price", item.get("price", 0))
                item_total = price * quantity
            receipt_lines.append(
                f"{item_name} x{quantity} — ₹{float(item_total):.2f}"
            )
        receipt_lines.extend([
            "----------------------------------",
            f"Total: ₹{float(receipt['total_amount']):.2f}",
            "----------------------------------",
            "Thank you for visiting!",
            "Please come again."
        ])
        st.download_button(
            label="📥 Download Bill",
            data="\n".join(receipt_lines) + "\n",
            file_name=f"{receipt['bill_number']}.txt",
            mime="text/plain",
            width="stretch",
            key=f"download_btn_{receipt['bill_number']}"
        )
        st.info("🖨️ Use the print buttons above the receipt to print the bill or bill and KOT.")
        if st.button(
            "🔄 Start New Order",
            type="primary",
            width="stretch"
        ):
            st.session_state.last_receipt = None
            st.session_state.order_completed = False
            st.session_state.current_bill = None
            st.session_state.order_submitted = False
            st.session_state.order_saved = False
            st.session_state.cart = []
            st.rerun()
        st.markdown("---")

    st.markdown('</div>', unsafe_allow_html=True)


# --- SIDEBAR: SYSTEM PORTAL SELECTION & BRANDING ---
st.sidebar.title("🔐 System Login Portal")

portals_list = [
    "🛒 Counter Staff Billing", 
    "🛠️ Order Modification & Cancellation",
    "🍽️ Menu Display Screen",
    "👨‍🍳 Kitchen Display (KDS)", 
    "🔑 Admin Management Login"
]

if st.session_state.active_portal not in portals_list:
    st.session_state.active_portal = "🛒 Counter Staff Billing"

current_portal_index = portals_list.index(st.session_state.active_portal)
portal_mode = st.sidebar.selectbox("Choose Login Gateway", portals_list, index=current_portal_index)

if portal_mode != st.session_state.active_portal:
    st.session_state.active_portal = portal_mode

# Keep live refresh on shared display portals, not during checkout or printing.
if st.session_state.active_portal in (
    "🍽️ Menu Display Screen",
    "👨‍🍳 Kitchen Display (KDS)"
):
    st_autorefresh(interval=5000, key="greenfusion_live_sync")

st.sidebar.divider()
if logo_img_obj is not None:
    st.sidebar.image(logo_img_obj, width="stretch", caption="Green Fusion - Bite & Sip by Dayals")

st.sidebar.divider()
upi_id = st.sidebar.text_input("UPI ID / Paytm ID", "greenfusion@paytm")
qr_image_file = st.sidebar.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

st.sidebar.divider()
if st.sidebar.button("🔄 Refresh Menu & Cache", width="stretch"):
    st.cache_data.clear()
    st.success("Menu cache cleared! Reloading...")
    st.rerun()

# --- WATERMARK BACKGROUND & STYLING CSS ---
if logo_base64:
    bg_watermark_css = f"""
    .stApp {{
        background-color: #FAF5EA;
        background-image: url("data:image/jpeg;base64,{logo_base64}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: cover;
        background-attachment: fixed;
        opacity: 0.95;
    }}
    .block-container {{
        background-color: rgba(250, 245, 234, 0.85) !important;
        border-radius: 20px;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}
    """
else:
    bg_watermark_css = """
    .stApp {
        background-color: #FAF5EA;
    }
    """

st.markdown(f"""
    <style>
    {bg_watermark_css}
    
    /* Typography Fixes */
    h1, h2, h3, h4, h5, h6 {{
        color: #333F20 !important;
        font-family: 'Cormorant Garamond', 'Inter', serif;
        font-weight: 700 !important;
    }}
    
    h1 {{
        font-size: 2.2rem !important;
        margin-bottom: 0px !important;
    }}
    
    p, label, span {{
        color: #2B2822 !important;
        font-family: 'Jost', 'Inter', sans-serif;
    }}
    
    /* Clean up the POS Menu Cards */
    .pos-card {{
        background-color: #FFFFFF;
        padding: 15px 10px;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(69, 85, 46, 0.15);
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .pos-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(69, 85, 46, 0.1);
        border: 1px solid #d5ded0;
    }}
    
    /* FORCE WHITE ADD BUTTONS INSIDE MENU CARDS */
    .pos-card div.stButton > button {{
        background-color: #FFFFFF !important;
        color: #2B2822 !important;
        border: 1px solid rgba(43,40,34,0.2) !important;
        box-shadow: none !important;
    }}
    .pos-card div.stButton > button:hover {{
        background-color: #FAF5EA !important;
        color: #BD5B34 !important;
        border-color: #BD5B34 !important;
        transform: none !important;
    }}
    
    /* Clean up the Cart Box */
    .cart-box {{
        background-color: #FFFFFF !important;
        padding: 20px;
        border-radius: 16px;
        border: 2px solid #45552E;
        box-shadow: 0 6px 18px rgba(69, 85, 46, 0.08);
    }}
    
    .mod-container {{
        background: linear-gradient(135deg, rgba(242, 235, 219, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
        padding: 25px;
        border-radius: 16px;
        border: 2px solid #45552E;
        box-shadow: 0 6px 20px rgba(69, 85, 46, 0.12);
        margin-bottom: 20px;
    }}
    
    /* General Button Styling (Olive Green for Checkouts/Actions) */
    div.stButton > button {{
        background-color: #45552E !important;
        color: #FAF5EA !important;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: none !important;
        box-shadow: 0 4px 10px rgba(69, 85, 46, 0.2);
        transition: all 0.2s ease-in-out;
    }}
    div.stButton > button:hover {{
        background-color: #5a6e3c !important;
        box-shadow: 0 6px 15px rgba(69, 85, 46, 0.3);
        transform: translateY(-1px);
    }}
    
    .receipt-box {{
        background-color: #ffffff;
        padding: 20px;
        border: 2px dashed #45552E;
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
    
    /* Fix Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #F2EBDB !important;
        border-right: 1px solid #d5ded0;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GATEWAY 1: COUNTER STAFF BILLING
# ==========================================
if st.session_state.active_portal == "🛒 Counter Staff Billing":
    st.title("☕ Green Fusion POS")
    st.markdown("**Counter Staff Portal** | *Bite & Sip by Dayals*")
    
    col_login1, col_login2 = st.columns(2)
    with col_login1:
        counter_id = st.text_input("Enter Counter Number / Staff ID", "Counter 1")
    with col_login2:
        counter_pin = st.text_input("Counter Passcode", type="password")
        
    st.divider()
    
    actual_counter_pin = st.secrets.get("COUNTER_PIN", "6666")
    
    if counter_pin == actual_counter_pin:
        st.success(f"Logged in successfully as **{counter_id}**. Ready for billing operations.")

        col_menu, col_cart = st.columns([1.6, 1], gap="large")
        
        with col_menu:
            st.markdown("### 📋 Menu Categories")
            
            # Group items directly by their Supabase category name
            ui_menu_groups = {}
            for item_name, data in current_menu.items():
                cat = data["category"]
                if cat not in ui_menu_groups:
                    ui_menu_groups[cat] = []
                ui_menu_groups[cat].append((item_name, data))
                
            # Sort the categories alphabetically so the tabs are organized
            active_categories = sorted(ui_menu_groups.keys())
            
            if not active_categories:
                st.info("No menu items available.")
            else:
                # Create horizontal clickable tabs for each specific category
                tabs = st.tabs(active_categories)
                
                for index, cat in enumerate(active_categories):
                    with tabs[index]:
                        st.write("") # Adds a little padding
                        
                        # Get the specific items for this tab
                        menu_items_list = ui_menu_groups[cat]
                        
                        # Build the 3-column grid
                        for i in range(0, len(menu_items_list), 3):
                            cols = st.columns(3)
                            for j in range(3):
                                if i + j < len(menu_items_list):
                                    item_name, item_info = menu_items_list[i + j]
                                    with cols[j]:
                                        st.markdown('<div class="pos-card">', unsafe_allow_html=True)
                                        
                                        icon = item_info.get("icon", "☕")
                                        st.markdown(f"<div style='font-size: 32px; margin-bottom: 4px;'>{icon}</div>", unsafe_allow_html=True)
                                            
                                        st.markdown(f"<h4 style='margin: 2px 0; font-size: 13px; color: #000 !important;'>{item_name}</h4>", unsafe_allow_html=True)
                                        st.markdown(f"<p style='margin: 0 0 2px 0; color: #BD5B34 !important; font-weight: bold; font-size: 14px;'>₹{item_info['price']:.2f}</p>", unsafe_allow_html=True)
                                        st.markdown(f"<p style='margin: 0 0 6px 0; color: #666 !important; font-size: 11px;'>Stock: <b>{item_info['stock']}</b></p>", unsafe_allow_html=True)
                                        
                                        if item_info['stock'] > 0:
                                            # Using a unique key based on item name prevents Streamlit button errors
                                            if st.button(
                                                "Add",
                                                key=f"add_tab_{item_name}",
                                                width="stretch",
                                                disabled=st.session_state.order_saved
                                            ):
                                                found = False
                                                if not st.session_state.cart:
                                                    st.session_state.order_submitted = False
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
                                            st.error("Sold Out")
                                        
                                        st.markdown('</div>', unsafe_allow_html=True)

        with col_cart:
            render_cart_section(supabase, counter_id, upi_id, qr_image_file)
            
    elif counter_pin != "":
        st.error("❌ Incorrect Counter Passcode.")
    else:
        st.info("🔒 Please enter the Counter Passcode to access billing.")

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
                st.dataframe(summary_df, hide_index=True, width="stretch")
                
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
                            if item_name in current_menu:
                                new_stock = current_menu[item_name]['stock'] + qty
                                supabase.table("menu_items").update({"stock": new_stock}).eq("name", item_name).execute()
                                fetch_menu_items.clear()
                                
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
# GATEWAY 3: MENU DISPLAY SCREEN (INTERNAL APP VIEW)
# ==========================================
elif st.session_state.active_portal == "🍽️ Menu Display Screen":
    # Hide sidebar for public menu displays
    if st.query_params.get("view") == "menu":
        st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

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
    for item_name, data in current_menu.items():
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
                        st.markdown(f"<div style='font-size: 40px; margin-bottom: 6px;'>{icon}</div>", unsafe_allow_html=True)
                        st.markdown(f"<h3 style='margin: 4px 0; color: #000 !important; font-size: 16px;'>{item_name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin: 0; color: #BD5B34 !important; font-weight: bold; font-size: 17px;'>₹{item_info['price']:.2f}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin: 4px 0 0 0; color: #666; font-size: 11px;'>Category: {item_info['category']} | Stock: {item_info['stock']}</p>", unsafe_allow_html=True)
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
        today_str = get_local_time().strftime('%Y-%m-%d')
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
            st.subheader("*Add New Item to POS & Live Webpage Menu*")
            
            with st.form("admin_menu_form"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    new_item_name = st.text_input("Item Name (e.g., Cold Brew Coffee)")
                    new_item_cat = st.selectbox("Category", ["Burgers", "Sides", "Snacks", "Beverages", "Desserts"])
                    new_item_price = st.number_input("Price (₹)", min_value=1.0, value=150.0)
                with col_f2:
                    initial_stock = st.number_input("Initial Stock Quantity", min_value=1, value=50)
                    new_item_icon = st.selectbox("Emoji Icon", ["🍔", "🍟", "☕", "🥤", "🥐", "🍦", "🍕", "🥪", "🍰", "🍵", "🍩", "🌮"])
                
                submit_btn = st.form_submit_button("➕ Add Item to Cloud Database")
                
                if submit_btn:
                    if new_item_name:
                        supabase.table("menu_items").insert({
                            "name": new_item_name,
                            "category": new_item_cat,
                            "price": float(new_item_price),
                            "stock": int(initial_stock),
                            "icon": new_item_icon
                        }).execute()
                        fetch_menu_items.clear()
                        st.success(f"Successfully added '{new_item_name}' to Supabase! It will instantly appear on the live webpage.")
                        st.rerun()
                    else:
                        st.error("Please enter a valid item name.")

        elif admin_action == "✏️ Edit or Remove Menu Items":
            st.subheader("*Edit or Remove Existing Menu Items*")
            
            if not current_menu:
                st.info("No menu items available to edit.")
            else:
                selected_edit_item = st.selectbox("Select Item to Modify", list(current_menu.keys()))
                current_data = current_menu[selected_edit_item]
                
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
                        icons_list = ["🍔", "🍟", "☕", "🥤", "🥐", "🍦", "🍕", "🥪", "🍰", "🍵", "🍩", "🌮", "💧", "🧀", "🍜", "🍽️"]
                        icon_index = icons_list.index(current_data["icon"]) if current_data.get("icon") in icons_list else 0
                        edited_icon = st.selectbox("Emoji Icon", icons_list, index=icon_index)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        save_changes = st.form_submit_button("💾 Save Changes to Cloud")
                    with col_btn2:
                        delete_item = st.form_submit_button("🗑️ Delete Item")
                        
                    if save_changes:
                        if edited_name:
                            supabase.table("menu_items").update({
                                "name": edited_name,
                                "category": edited_cat,
                                "price": float(edited_price),
                                "stock": int(edited_stock),
                                "icon": edited_icon
                            }).eq("name", selected_edit_item).execute()
                            fetch_menu_items.clear()
                            
                            st.success(f"Successfully updated '{edited_name}' in the cloud database!")
                            st.rerun()
                        else:
                            st.error("Item name cannot be empty.")
                            
                    if delete_item:
                        supabase.table("menu_items").delete().eq("name", selected_edit_item).execute()
                        fetch_menu_items.clear()
                        st.success(f"Successfully removed '{selected_edit_item}' from the cloud database.")
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

            st.divider()
            st.subheader("*📅 Daily Revenue & Bills Summary*")
            try:
                today = get_local_time().date()
                tomorrow = today + timedelta(days=1)
                orders_response = (
                    supabase.table("orders")
                    .select("*")
                    .gte(
                        "created_at",
                        datetime.combine(
                            today, datetime.min.time(), tzinfo=LOCAL_TIMEZONE
                        ).isoformat()
                    )
                    .lt(
                        "created_at",
                        datetime.combine(
                            tomorrow, datetime.min.time(), tzinfo=LOCAL_TIMEZONE
                        ).isoformat()
                    )
                    .order("created_at", desc=True)
                    .execute()
                )
                df_orders = pd.DataFrame(orders_response.data)

                if df_orders.empty:
                    st.info("No sales or bills generated today.")
                else:
                    df_orders = df_orders.drop_duplicates(subset=['bill_number'])
                    df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
                    df_orders['Day'] = df_orders['created_at'].dt.date
                    df_orders['total_amount'] = pd.to_numeric(df_orders['total_amount'])

                    daily_summary = (
                        df_orders.groupby('Day')
                        .agg(
                            total_bills=('bill_number', 'count'),
                            total_revenue=('total_amount', 'sum')
                        )
                        .reset_index()
                        .sort_values('Day', ascending=False)
                    )
                    display_summary = daily_summary.rename(columns={
                        'Day': 'Date',
                        'total_bills': 'Total Bills',
                        'total_revenue': 'Total Revenue (₹)'
                    })
                    display_summary['Total Revenue (₹)'] = display_summary[
                        'Total Revenue (₹)'
                    ].apply(lambda amount: f"₹{amount:,.2f}")
                    st.dataframe(
                        display_summary,
                        hide_index=True,
                        width="stretch"
                    )

                    st.subheader("*📊 Daily Sales Chart*")
                    chart_data = daily_summary.set_index('Day')['total_revenue']
                    st.bar_chart(chart_data)

                    st.subheader("*🧾 Bill Details by Date*")
                    available_bill_days = daily_summary['Day'].tolist()
                    selected_bill_day = st.selectbox(
                        "Select Date to View Bills",
                        available_bill_days,
                        format_func=str,
                        key="admin_bill_date"
                    )
                    selected_bills = df_orders[df_orders['Day'] == selected_bill_day]
                    st.write(
                        f"Showing **{len(selected_bills)}** bill(s) generated on "
                        f"**{selected_bill_day}**:"
                    )

                    for index, bill in selected_bills.iterrows():
                        exact_bill_number = bill.get(
                            'bill_number', f"Bill #{bill.get('id', 'N/A')}"
                        )
                        bill_time = bill['created_at'].strftime('%H:%M:%S')
                        bill_total = bill['total_amount']
                        with st.expander(
                            f"Bill ID: {exact_bill_number} — Time: {bill_time} "
                            f"— Total: ₹{bill_total:.2f}"
                        ):
                            col_bill_details, col_bill_print = st.columns([3, 1])
                            with col_bill_details:
                                st.write(f"**Exact Bill Number:** {exact_bill_number}")
                                st.write(
                                    f"**Customer / Table:** "
                                    f"{bill.get('customer_name', 'Walk-in')}"
                                )
                                st.write(
                                    f"**Items Ordered:** "
                                    f"{bill.get('items_summary', bill.get('items', 'Details unavailable'))}"
                                )
                                st.write(
                                    f"**Payment Status:** "
                                    f"{bill.get('payment_status', 'Paid')}"
                                )
                            with col_bill_print:
                                if st.button(
                                    "🖨️ Print Bill",
                                    key=f"print_bill_{bill.get('id', index)}"
                                ):
                                    st.success(f"Print view ready for {exact_bill_number}.")
                                    components.html(
                                        build_bill_print_html(bill),
                                        height=520,
                                        scrolling=True
                                    )
            except Exception as e:
                st.error(f"Error loading revenue and bill data: {e}")
            
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
                    
                    st.dataframe(daily_item_summary, hide_index=True, width="stretch")
                    
                    fig_daily_items = px.bar(
                        daily_item_summary, 
                        x='Item Name', 
                        y='Total Quantity Sold', 
                        title=f"Units Sold Per Item on {selected_day}", 
                        text='Total Quantity Sold', 
                        color_discrete_sequence=['#45552E']
                    )
                    fig_daily_items.update_layout(xaxis_title="", yaxis_title="Units Sold", template="plotly_white")
                    st.plotly_chart(fig_daily_items, width="stretch")
                else:
                    st.info("No item details available yet.")

                st.divider()

                st.markdown("### *📥 Download System Reports*")
                excel_file = convert_dfs_to_excel(df_sales, df_items)
                st.download_button(
                    label="📥 Download Comprehensive Sales & Items Report (Excel)",
                    data=excel_file,
                    file_name=f"green_fusion_report_{get_local_time().strftime('%Y-%m-%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
                
                st.divider()

                df_sales_indexed = df_sales.set_index('Date')
                stat_view = st.selectbox("Select Timeframe Revenue Report", ["Daily", "Weekly", "Monthly", "Yearly"])
                
                if stat_view == "Daily":
                    data = df_sales_indexed.resample('D').sum(numeric_only=True).reset_index()
                    fig = px.bar(data, x='Date', y='total', title="Daily Revenue Breakdown (₹)", text='total', color_discrete_sequence=['#45552E'])
                elif stat_view == "Weekly":
                    data = df_sales_indexed.resample('W').sum(numeric_only=True).reset_index()
                    fig = px.line(data, x='Date', y='total', title="Weekly Revenue Trends (₹)", markers=True, color_discrete_sequence=['#45552E'])
                elif stat_view == "Monthly":
                    data = df_sales_indexed.resample('ME').sum(numeric_only=True).reset_index()
                    fig = px.bar(data, x='Date', y='total', title="Monthly Revenue Summary (₹)", color_discrete_sequence=['#6B8E23'])
                elif stat_view == "Yearly":
                    data = df_sales_indexed.resample('YE').sum(numeric_only=True).reset_index()
                    data['Date'] = data['Date'].dt.year
                    fig = px.bar(data, x='Date', y='total', title="Yearly Revenue Performance (₹)", color_discrete_sequence=['#3b4e1e'])
                
                fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)", template="plotly_white")
                st.plotly_chart(fig, width="stretch")
                
                st.divider()
                st.subheader("*⚡ Quick Performance Metrics*")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Lifetime Revenue", f"₹{overall_total:,.2f}")
                m2.metric("Average Daily Sales", f"₹{df_sales_indexed.resample('D').sum(numeric_only=True)['total'].mean():,.2f}")
                m3.metric("Highest Single Bill", f"₹{df_sales['total'].max():,.2f}")

    else:
        if admin_password != "":
            st.error("Incorrect Admin Password.")
        else:
            st.info("🔒 Please enter the master password to unlock admin privileges.")