import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import config

class DatabaseManager:
    """Manages the PostgreSQL database for customer and order information."""
    
    def __init__(self):
        # Database connection parameters
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'cafe_system'),
            'user': os.getenv('DB_USER', 'cafe_admin'),
            'password': os.getenv('DB_PASSWORD', 'secure_cafe_password')
        }
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.connection_params)
    
    def init_database(self):
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create customers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(50),
                    face_encoding_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_visit TIMESTAMP,
                    visit_count INTEGER DEFAULT 0,
                    preferences JSONB  -- JSON with indexing
                )
            ''')
            
            # Create menu_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    category VARCHAR(50) NOT NULL,
                    subcategory VARCHAR(50),
                    price DECIMAL(10,2) NOT NULL,
                    ingredients JSONB,
                    allergens JSONB,
                    calories INTEGER,
                    description TEXT,
                    is_available BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount DECIMAL(10,2),
                    notes TEXT
                )
            ''')
            
            # Create order_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                    menu_item_id INTEGER REFERENCES menu_items(id),
                    quantity INTEGER DEFAULT 1,
                    unit_price DECIMAL(10,2),
                    customizations JSONB
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_last_visit ON customers(last_visit)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category)')
            
            # JSON indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_preferences ON customers USING GIN (preferences)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_menu_ingredients ON menu_items USING GIN (ingredients)')
            
            conn.commit()
            
    def add_customer(self, name: str, email: str = None, phone: str = None, 
                    face_encoding_path: str = None, preferences: Dict = None) -> int:
        """Add a new customer to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO customers (name, email, phone, face_encoding_path, preferences, last_visit, visit_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (name, email, phone, face_encoding_path, json.dumps(preferences) if preferences else None, datetime.now(), 1))
            
            customer_id = cursor.fetchone()[0]
            conn.commit()
            return customer_id
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Retrieve customer information by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
            row = cursor.fetchone()
            
            if row:
                customer = dict(row)
                return customer
            return None
    
    def get_all_customers(self) -> List[Dict]:
        """Retrieve all customers from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute('SELECT * FROM customers ORDER BY last_visit DESC')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def update_customer_visit(self, customer_id: int):
        """Update customer's last visit and visit count."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE customers 
                SET last_visit = %s, visit_count = visit_count + 1
                WHERE id = %s
            ''', (datetime.now(), customer_id))
            conn.commit()
    
    def add_menu_item(self, name: str, category: str, price: float, 
                     subcategory: str = None, ingredients: List[str] = None,
                     allergens: List[str] = None, calories: int = None,
                     description: str = None) -> int:
        """Add a menu item to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO menu_items (name, category, subcategory, price, ingredients, 
                                      allergens, calories, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (name, category, subcategory, price, json.dumps(ingredients) if ingredients else None, 
                  json.dumps(allergens) if allergens else None, calories, description))
            
            item_id = cursor.fetchone()[0]
            conn.commit()
            return item_id
    
    def get_menu_items(self, category: str = None, available_only: bool = True) -> List[Dict]:
        """Retrieve menu items, optionally filtered by category."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = 'SELECT * FROM menu_items'
            params = []
            
            conditions = []
            if category:
                conditions.append('category = %s')
                params.append(category)
            if available_only:
                conditions.append('is_available = TRUE')
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def add_order(self, customer_id: int, items: List[Dict], notes: str = None) -> int:
        """Add a new order with items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate total amount
            total_amount = sum(float(item['unit_price']) * item['quantity'] for item in items)
            
            # Create order
            cursor.execute('''
                INSERT INTO orders (customer_id, total_amount, notes)
                VALUES (%s, %s, %s)
                RETURNING id
            ''', (customer_id, total_amount, notes))
            
            order_id = cursor.fetchone()[0]
            
            # Add order items
            for item in items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, customizations)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (order_id, item['menu_item_id'], item['quantity'], 
                      item['unit_price'], json.dumps(item.get('customizations', {}))))
            
            conn.commit()
            return order_id
    
    def get_customer_order_history(self, customer_id: int, limit: int = None) -> List[Dict]:
        """Get order history for a specific customer."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = '''
                SELECT o.*, oi.menu_item_id, oi.quantity, oi.unit_price, oi.customizations,
                       mi.name as item_name, mi.category, mi.subcategory
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                WHERE o.customer_id = %s
                ORDER BY o.order_date DESC
            '''
            
            params = [customer_id]
            if limit:
                query += ' LIMIT %s'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Group by order
            orders = {}
            for row in rows:
                order_id = row['id']
                if order_id not in orders:
                    orders[order_id] = {
                        'id': row['id'],
                        'customer_id': row['customer_id'],
                        'order_date': row['order_date'],
                        'total_amount': float(row['total_amount']),
                        'notes': row['notes'],
                        'items': []
                    }
                
                item = {
                    'menu_item_id': row['menu_item_id'],
                    'quantity': row['quantity'],
                    'unit_price': float(row['unit_price']),
                    'customizations': row['customizations'] or {},
                    'item_name': row['item_name'],
                    'category': row['category'],
                    'subcategory': row['subcategory']
                }
                orders[order_id]['items'].append(item)
            
            return list(orders.values())
    
    def get_popular_items(self, limit: int = 10) -> List[Dict]:
        """Get most popular menu items based on order frequency."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute('''
                SELECT mi.*, COUNT(oi.menu_item_id) as order_count,
                       SUM(oi.quantity) as total_quantity
                FROM menu_items mi
                JOIN order_items oi ON mi.id = oi.menu_item_id
                WHERE mi.is_available = TRUE
                GROUP BY mi.id
                ORDER BY order_count DESC, total_quantity DESC
                LIMIT %s
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_orders(self, limit: int = None) -> List[Dict]:
        """Get all orders from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = '''
                SELECT o.*, oi.menu_item_id, oi.quantity, oi.unit_price, oi.customizations,
                       mi.name as item_name, mi.category, mi.subcategory
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                ORDER BY o.order_date DESC
            '''
            
            params = []
            if limit:
                query += ' LIMIT %s'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Group by order
            orders = {}
            for row in rows:
                order_id = row['id']
                if order_id not in orders:
                    orders[order_id] = {
                        'id': row['id'],
                        'customer_id': row['customer_id'],
                        'order_date': row['order_date'],
                        'total_amount': float(row['total_amount']),
                        'notes': row['notes'],
                        'items': []
                    }
                
                item = {
                    'menu_item_id': row['menu_item_id'],
                    'quantity': row['quantity'],
                    'unit_price': float(row['unit_price']),
                    'customizations': row['customizations'] or {},
                    'item_name': row['item_name'],
                    'category': row['category'],
                    'subcategory': row['subcategory']
                }
                orders[order_id]['items'].append(item)
            
            return list(orders.values())
    
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
            except psycopg2.IntegrityError:
                pass  # Item already exists
