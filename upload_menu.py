from supabase import create_client, Client

# Your Supabase credentials
SUPABASE_URL = "https://vdabufmcqzdilkhzrxim.supabase.co"
SUPABASE_KEY = "sb_publishable_D_7MmPn7tLWsxcPnuH6aHA_I_V19fJ6"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Your complete menu, now including Seasonal Fruit Juices
new_menu_items = [
    # 💧 Water
    {"name": "Packaged Drinking Water", "category": "💧 Water", "price": 20, "stock": 50},
    
    # 🍟 French Fries
    {"name": "Classic Salted Fries", "category": "🍟 French Fries", "price": 99, "stock": 50},
    {"name": "Peri Peri Fries", "category": "🍟 French Fries", "price": 119, "stock": 50},
    
    # 🧀 Cheese Corner
    {"name": "Cheese Balls", "category": "🧀 Cheese Corner", "price": 149, "stock": 50},
    {"name": "Cheese Fries", "category": "🧀 Cheese Corner", "price": 169, "stock": 50},
    
    # 🍜 Quick Bites
    {"name": "Maggi", "category": "🍜 Quick Bites", "price": 60, "stock": 50},
    {"name": "Masala Maggi", "category": "🍜 Quick Bites", "price": 80, "stock": 50},
    {"name": "Cheese Maggi", "category": "🍜 Quick Bites", "price": 100, "stock": 50},
    {"name": "Poha", "category": "🍜 Quick Bites", "price": 70, "stock": 50},
    
    # 🥪 Sandwiches
    {"name": "Grilled Veg Sandwich", "category": "🥪 Sandwiches", "price": 120, "stock": 50},
    {"name": "Cheese Corn Sandwich", "category": "🥪 Sandwiches", "price": 140, "stock": 50},
    {"name": "Cheese Chilli Toast", "category": "🥪 Sandwiches", "price": 130, "stock": 50},
    {"name": "Paneer Wrap Sandwich", "category": "🥪 Sandwiches", "price": 160, "stock": 50},
    
    # 🍝 Pasta
    {"name": "White Sauce (Alfredo) Pasta", "category": "🍝 Pasta", "price": 199, "stock": 50},
    {"name": "Red Sauce (Arrabbiata) Pasta", "category": "🍝 Pasta", "price": 189, "stock": 50},
    
    # 🥣 Soups
    {"name": "Tomato Basil Soup", "category": "🥣 Soups", "price": 110, "stock": 50},
    {"name": "Sweet Corn Soup", "category": "🥣 Soups", "price": 110, "stock": 50},
    {"name": "Hot & Sour Soup", "category": "🥣 Soups", "price": 120, "stock": 50},
    
    # 🍹 Mocktails
    {"name": "Green Fusion Fizz", "category": "🍹 Mocktails", "price": 149, "stock": 50},
    {"name": "Virgin Mojito", "category": "🍹 Mocktails", "price": 129, "stock": 50},
    {"name": "Blue Lagoon", "category": "🍹 Mocktails", "price": 129, "stock": 50},
    {"name": "Watermelon Cooler", "category": "🍹 Mocktails", "price": 139, "stock": 50},
    {"name": "Strawberry Basil Fizz", "category": "🍹 Mocktails", "price": 149, "stock": 50},
    {"name": "Masala Soda", "category": "🍹 Mocktails", "price": 80, "stock": 50},
    
    # ☕ Coffee & Espresso
    {"name": "Espresso (Single)", "category": "☕ Coffee & Espresso", "price": 90, "stock": 50},
    {"name": "Espresso (Double)", "category": "☕ Coffee & Espresso", "price": 120, "stock": 50},
    {"name": "Americano", "category": "☕ Coffee & Espresso", "price": 110, "stock": 50},
    {"name": "Cappuccino", "category": "☕ Coffee & Espresso", "price": 130, "stock": 50},
    {"name": "Cafe Latte", "category": "☕ Coffee & Espresso", "price": 140, "stock": 50},
    {"name": "Cold Brew", "category": "☕ Coffee & Espresso", "price": 150, "stock": 50},
    {"name": "Iced Latte", "category": "☕ Coffee & Espresso", "price": 160, "stock": 50},
    {"name": "Mocha", "category": "☕ Coffee & Espresso", "price": 170, "stock": 50},
    
    # 🫖 Tea
    {"name": "Masala Chai", "category": "🫖 Tea", "price": 40, "stock": 50},
    {"name": "Green Tea", "category": "🫖 Tea", "price": 60, "stock": 50},
    {"name": "Lemon Iced Tea", "category": "🫖 Tea", "price": 110, "stock": 50},
    {"name": "Ginger Tea", "category": "🫖 Tea", "price": 40, "stock": 50},
    
    # 🥤 Shakes
    {"name": "Chocolate Shake", "category": "🥤 Shakes", "price": 150, "stock": 50},
    {"name": "Oreo Shake", "category": "🥤 Shakes", "price": 160, "stock": 50},
    {"name": "Strawberry Shake", "category": "🥤 Shakes", "price": 150, "stock": 50},
    {"name": "Mango Shake", "category": "🥤 Shakes", "price": 160, "stock": 50},
    {"name": "Cold Coffee Shake", "category": "🥤 Shakes", "price": 170, "stock": 50},
    
    # 🍨 Ice Creams
    {"name": "Vanilla Scoop", "category": "🍨 Ice Creams", "price": 70, "stock": 50},
    {"name": "Chocolate Scoop", "category": "🍨 Ice Creams", "price": 80, "stock": 50},
    {"name": "Strawberry Scoop", "category": "🍨 Ice Creams", "price": 80, "stock": 50},
    {"name": "Butterscotch Scoop", "category": "🍨 Ice Creams", "price": 90, "stock": 50},
    {"name": "Mango Scoop (seasonal)", "category": "🍨 Ice Creams", "price": 90, "stock": 50},

    # 🍊 Seasonal Fruit Juices (NEW)
    {"name": "Watermelon Juice", "category": "🍊 Seasonal Fruit Juices", "price": 99, "stock": 50},
    {"name": "Mosambi (Sweet Lime) Juice", "category": "🍊 Seasonal Fruit Juices", "price": 110, "stock": 50},
    {"name": "Fresh Orange Juice", "category": "🍊 Seasonal Fruit Juices", "price": 120, "stock": 50},
    {"name": "Pineapple Juice", "category": "🍊 Seasonal Fruit Juices", "price": 110, "stock": 50},
    {"name": "Mixed Seasonal Fruit Juice", "category": "🍊 Seasonal Fruit Juices", "price": 129, "stock": 50},
    {"name": "Pomegranate (Anaar) Juice", "category": "🍊 Seasonal Fruit Juices", "price": 149, "stock": 50},
    {"name": "ABC (Apple, Beetroot, Carrot)", "category": "🍊 Seasonal Fruit Juices", "price": 139, "stock": 50}
]

print("Clearing old menu items...")
supabase.table("menu_items").delete().neq("id", 0).execute()

print("Uploading complete menu...")
response = supabase.table("menu_items").insert(new_menu_items).execute()

print(f"✅ Successfully uploaded all {len(new_menu_items)} items to Green Fusion POS!")