import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import config

class DatabaseManager:
    """Manages the SQLite database for customer and order information."""
    
    def __init__(self):
        self.db_path = config.DATABASE_FILE
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create customers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    face_encoding_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_visit TIMESTAMP,
                    visit_count INTEGER DEFAULT 0,
                    preferences TEXT  -- JSON string for dietary preferences
                )
            ''')
            
            # Create menu_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,  -- 'food' or 'drink'
                    subcategory TEXT,  -- 'coffee', 'tea', 'pastry', etc.
                    price REAL NOT NULL,
                    ingredients TEXT,  -- JSON string
                    allergens TEXT,  -- JSON string
                    calories INTEGER,
                    description TEXT,
                    is_available BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount REAL,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            
            # Create order_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    menu_item_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    unit_price REAL,
                    customizations TEXT,  -- JSON string for customizations
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
                )
            ''')
            
            conn.commit()
            
    def add_customer(self, name: str, email: str = None, phone: str = None, 
                    face_encoding_path: str = None, preferences: Dict = None) -> int:
        """Add a new customer to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            preferences_json = json.dumps(preferences) if preferences else None
            
            cursor.execute('''
                INSERT INTO customers (name, email, phone, face_encoding_path, preferences, last_visit, visit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, face_encoding_path, preferences_json, datetime.now(), 1))
            
            customer_id = cursor.lastrowid
            conn.commit()
            return customer_id
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Retrieve customer information by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                customer = dict(zip(columns, row))
                if customer['preferences']:
                    customer['preferences'] = json.loads(customer['preferences'])
                return customer
            return None
    
    def get_all_customers(self) -> List[Dict]:
        """Retrieve all customers from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers ORDER BY last_visit DESC')
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            customers = []
            for row in rows:
                customer = dict(zip(columns, row))
                if customer['preferences']:
                    customer['preferences'] = json.loads(customer['preferences'])
                customers.append(customer)
            return customers
    
    def update_customer_visit(self, customer_id: int):
        """Update customer's last visit and visit count."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customers 
                SET last_visit = ?, visit_count = visit_count + 1
                WHERE id = ?
            ''', (datetime.now(), customer_id))
            conn.commit()
    
    def add_menu_item(self, name: str, category: str, price: float, 
                     subcategory: str = None, ingredients: List[str] = None,
                     allergens: List[str] = None, calories: int = None,
                     description: str = None) -> int:
        """Add a menu item to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            ingredients_json = json.dumps(ingredients) if ingredients else None
            allergens_json = json.dumps(allergens) if allergens else None
            
            cursor.execute('''
                INSERT INTO menu_items (name, category, subcategory, price, ingredients, 
                                      allergens, calories, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, category, subcategory, price, ingredients_json, 
                  allergens_json, calories, description))
            
            item_id = cursor.lastrowid
            conn.commit()
            return item_id
    
    def get_menu_items(self, category: str = None, available_only: bool = True) -> List[Dict]:
        """Retrieve menu items, optionally filtered by category."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM menu_items'
            params = []
            
            conditions = []
            if category:
                conditions.append('category = ?')
                params.append(category)
            if available_only:
                conditions.append('is_available = 1')
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            items = []
            for row in rows:
                item = dict(zip(columns, row))
                if item['ingredients']:
                    item['ingredients'] = json.loads(item['ingredients'])
                if item['allergens']:
                    item['allergens'] = json.loads(item['allergens'])
                items.append(item)
            return items
    
    def add_order(self, customer_id: int, items: List[Dict], notes: str = None) -> int:
        """Add a new order with items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate total amount
            total_amount = sum(item['unit_price'] * item['quantity'] for item in items)
            
            # Create order
            cursor.execute('''
                INSERT INTO orders (customer_id, total_amount, notes)
                VALUES (?, ?, ?)
            ''', (customer_id, total_amount, notes))
            
            order_id = cursor.lastrowid
            
            # Add order items
            for item in items:
                customizations_json = json.dumps(item.get('customizations', {}))
                cursor.execute('''
                    INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, customizations)
                    VALUES (?, ?, ?, ?, ?)
                ''', (order_id, item['menu_item_id'], item['quantity'], 
                      item['unit_price'], customizations_json))
            
            conn.commit()
            return order_id
    
    def get_customer_order_history(self, customer_id: int, limit: int = None) -> List[Dict]:
        """Get order history for a specific customer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT o.*, oi.menu_item_id, oi.quantity, oi.unit_price, oi.customizations,
                       mi.name as item_name, mi.category, mi.subcategory
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                WHERE o.customer_id = ?
                ORDER BY o.order_date DESC
            '''
            
            params = [customer_id]
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Group by order
            orders = {}
            for row in rows:
                order_id = row[0]
                if order_id not in orders:
                    orders[order_id] = {
                        'id': row[0],
                        'customer_id': row[1],
                        'order_date': row[2],
                        'total_amount': row[3],
                        'notes': row[4],
                        'items': []
                    }
                
                item = {
                    'menu_item_id': row[5],
                    'quantity': row[6],
                    'unit_price': row[7],
                    'customizations': json.loads(row[8]) if row[8] else {},
                    'item_name': row[9],
                    'category': row[10],
                    'subcategory': row[11]
                }
                orders[order_id]['items'].append(item)
            
            return list(orders.values())
    
    def get_popular_items(self, limit: int = 10) -> List[Dict]:
        """Get most popular menu items based on order frequency."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mi.*, COUNT(oi.menu_item_id) as order_count,
                       SUM(oi.quantity) as total_quantity
                FROM menu_items mi
                JOIN order_items oi ON mi.id = oi.menu_item_id
                WHERE mi.is_available = 1
                GROUP BY mi.id
                ORDER BY order_count DESC, total_quantity DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            items = []
            for row in rows:
                item = dict(zip(columns, row))
                if item['ingredients']:
                    item['ingredients'] = json.loads(item['ingredients'])
                if item['allergens']:
                    item['allergens'] = json.loads(item['allergens'])
                items.append(item)
            return items
    
    def populate_sample_data(self):
        """Populate the database with sample menu items for testing."""
        sample_items = [
            # Coffee
            ("Espresso", "drink", "coffee", 2.50, ["coffee beans"], [], 5, "Classic Italian espresso shot"),
            ("Cappuccino", "drink", "coffee", 3.50, ["coffee beans", "milk"], ["dairy"], 120, "Espresso with steamed milk and foam"),
            ("Latte", "drink", "coffee", 4.00, ["coffee beans", "milk"], ["dairy"], 150, "Espresso with steamed milk"),
            ("Americano", "drink", "coffee", 3.00, ["coffee beans"], [], 10, "Espresso with hot water"),
            
            # Tea
            ("Green Tea", "drink", "tea", 2.00, ["green tea leaves"], [], 0, "Fresh green tea"),
            ("Earl Grey", "drink", "tea", 2.50, ["black tea", "bergamot"], [], 0, "Classic Earl Grey tea"),
            
            # Food
            ("Croissant", "food", "pastry", 3.00, ["flour", "butter", "eggs"], ["gluten", "dairy", "eggs"], 280, "Buttery French croissant"),
            ("Blueberry Muffin", "food", "pastry", 3.50, ["flour", "blueberries", "eggs", "milk"], ["gluten", "dairy", "eggs"], 320, "Fresh blueberry muffin"),
            ("Avocado Toast", "food", "sandwich", 7.50, ["bread", "avocado", "tomato"], ["gluten"], 350, "Toasted bread with fresh avocado"),
            ("Caesar Salad", "food", "salad", 8.00, ["lettuce", "parmesan", "croutons"], ["dairy", "gluten"], 250, "Classic Caesar salad"),
        ]
        
        for item in sample_items:
            try:
                self.add_menu_item(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7])
            except sqlite3.IntegrityError:
                pass  # Item already exists
