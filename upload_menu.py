from supabase import create_client, Client

# Your Supabase credentials
SUPABASE_URL = "https://vdabufmcqzdilkhzrxim.supabase.co"
SUPABASE_KEY = "sb_publishable_D_7MmPn7tLWsxcPnuH6aHA_I_V19fJ6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Full POS catalog from the supplied menu.
MENU_ITEMS = {
    "Gelato Amor": {
        "Chocolate (Single)": 79.00,
        "Chocolate (Double)": 119.00,
        "Vanilla (Single)": 79.00,
        "Vanilla (Double)": 119.00,
        "Strawberry (Single)": 79.00,
        "Strawberry (Double)": 119.00,
        "Mango (Single)": 79.00,
        "Mango (Double)": 119.00,
        "Coffee (Single)": 79.00,
        "Coffee (Double)": 119.00,
        "Choco Chips (Single)": 79.00,
        "Choco Chips (Double)": 119.00,
        "Black Currant (Single)": 79.00,
        "Black Currant (Double)": 119.00,
    },
    "Premium Shakes": {
        "Protein Shake": 119.00,
        "Banana Shake": 89.00,
        "Strawberry Shake": 99.00,
        "Chocolate Shake": 99.00,
        "Badam Shake": 99.00,
        "Sweet Lassi": 89.00,
    },
    "Local Bites": {
        "Dry Maggie": 79.00,
        "Soupy Maggie": 69.00,
        "Indori Poha": 79.00,
        "Bas Poha": 69.00,
        "Bombay Ki Shan (Vada Paw)": 79.00,
        "Shub Suruwat Ganesh ji": 11.00,
    },
    "Pasta & Soup": {
        "Alfredo Pasta": 119.00,
        "Marinara Pasta": 109.00,
        "Veg Soup": 99.00,
        "Manchurian Soup": 119.00,
    },
    "French Fries": {
        "Salted Fries": 99.00,
        "Peri Peri Fries": 119.00,
        "Cheese Burst Fries": 129.00,
    },
    "Sandwiches": {
        "Veg Sandwich": 99.00,
        "Paneer Sandwich": 119.00,
        "Cheese Sandwich": 129.00,
    },
    "Fresh Juices": {
        "Orange (Small)": 69.00,
        "Orange (Large)": 119.00,
        "Pomegranate (Small)": 69.00,
        "Pomegranate (Large)": 119.00,
        "Watermelon (Small)": 69.00,
        "Watermelon (Large)": 119.00,
        "Mango (Small)": 69.00,
        "Mango (Large)": 119.00,
        "Malta (Small)": 69.00,
        "Malta (Large)": 119.00,
        "ABC (Small)": 69.00,
        "ABC (Large)": 119.00,
    },
    "Mocktails": {
        "Virgin Mojito": 119.00,
        "Sip the Lip": 129.00,
        "Green Forest": 129.00,
        "Ocean Rain": 129.00,
    },
    "Cold Brews": {
        "Hard Rock": 110.00,
        "Brew Ice": 99.00,
    },
    "Warm Coffee": {
        "Coffee Warmer": 69.00,
        "Espresso Shot": 69.00,
        "Hard Coffee": 79.00,
    },
    "Premium Tea": {
        "Green Tea": 59.00,
        "Masala Tea": 49.00,
        "Ginger Tea": 49.00,
        "Black Tea": 49.00,
        "Ice Tea": 79.00,
        "Water Packet": 10.00,
        "Water Bottle (₹15)": 15.00,
        "Water Bottle (₹20)": 20.00,
    },
}

new_menu_items = [
    {
        "name": item_name,
        "category": category,
        "price": price,
        "stock": 50,
    }
    for category, items in MENU_ITEMS.items()
    for item_name, price in items.items()
]

print("Clearing old menu items...")
supabase.table("menu_items").delete().neq("id", 0).execute()

print("Uploading complete menu...")
response = supabase.table("menu_items").insert(new_menu_items).execute()

print(f"✅ Successfully uploaded all {len(new_menu_items)} items to Green Fusion POS!")