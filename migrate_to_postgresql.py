"""
Migration script to move data from SQLite to PostgreSQL
Run this script after setting up PostgreSQL to transfer existing data.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set environment variables for PostgreSQL before importing
os.environ['DATABASE_TYPE'] = 'postgresql'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'cafe_system'
os.environ['DB_USER'] = 'cafe_admin'
os.environ['DB_PASSWORD'] = 'secure_cafe_password'

from database_manager import DatabaseManager

class SQLiteToPostgreSQLMigration:
    def __init__(self):
        self.sqlite_db_path = 'data/cafe_system.db'
        self.postgres_db = DatabaseManager()
    
    def check_sqlite_exists(self):
        """Check if SQLite database exists."""
        return os.path.exists(self.sqlite_db_path)
    
    def get_sqlite_connection(self):
        """Get SQLite connection."""
        return sqlite3.connect(self.sqlite_db_path)
    
    def migrate_customers(self):
        """Migrate customers from SQLite to PostgreSQL."""
        print("👥 Migrating customers...")
        
        with self.get_sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.cursor()
            cursor.execute('SELECT * FROM customers')
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            migrated_count = 0
            for row in rows:
                customer = dict(zip(columns, row))
                
                # Parse preferences if exists
                preferences = None
                if customer['preferences']:
                    try:
                        preferences = json.loads(customer['preferences'])
                    except json.JSONDecodeError:
                        preferences = None
                
                try:
                    new_id = self.postgres_db.add_customer(
                        name=customer['name'],
                        email=customer['email'],
                        phone=customer['phone'],
                        face_encoding_path=customer['face_encoding_path'],
                        preferences=preferences
                    )
                    
                    # Update visit count and last visit
                    if customer['visit_count'] > 1:
                        with self.postgres_db.get_connection() as conn:
                            pg_cursor = conn.cursor()
                            pg_cursor.execute('''
                                UPDATE customers 
                                SET visit_count = %s, last_visit = %s, created_at = %s
                                WHERE id = %s
                            ''', (customer['visit_count'], customer['last_visit'], 
                                  customer['created_at'], new_id))
                            conn.commit()
                    
                    migrated_count += 1
                    print(f"  ✅ Migrated customer: {customer['name']} (ID: {customer['id']} → {new_id})")
                    
                except Exception as e:
                    print(f"  ❌ Error migrating customer {customer['name']}: {e}")
            
            print(f"📊 Migrated {migrated_count} customers")
            return migrated_count
    
    def migrate_menu_items(self):
        """Migrate menu items from SQLite to PostgreSQL."""
        print("🍽️  Migrating menu items...")
        
        with self.get_sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.cursor()
            cursor.execute('SELECT * FROM menu_items')
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            migrated_count = 0
            for row in rows:
                item = dict(zip(columns, row))
                
                # Parse JSON fields
                ingredients = None
                allergens = None
                
                if item['ingredients']:
                    try:
                        ingredients = json.loads(item['ingredients'])
                    except json.JSONDecodeError:
                        ingredients = None
                
                if item['allergens']:
                    try:
                        allergens = json.loads(item['allergens'])
                    except json.JSONDecodeError:
                        allergens = None
                
                try:
                    new_id = self.postgres_db.add_menu_item(
                        name=item['name'],
                        category=item['category'],
                        price=item['price'],
                        subcategory=item['subcategory'],
                        ingredients=ingredients,
                        allergens=allergens,
                        calories=item['calories'],
                        description=item['description']
                    )
                    
                    # Update availability
                    if not item['is_available']:
                        with self.postgres_db.get_connection() as conn:
                            pg_cursor = conn.cursor()
                            pg_cursor.execute('''
                                UPDATE menu_items SET is_available = %s WHERE id = %s
                            ''', (False, new_id))
                            conn.commit()
                    
                    migrated_count += 1
                    print(f"  ✅ Migrated item: {item['name']} (ID: {item['id']} → {new_id})")
                    
                except Exception as e:
                    print(f"  ❌ Error migrating item {item['name']}: {e}")
            
            print(f"📊 Migrated {migrated_count} menu items")
            return migrated_count
    
    def migrate_orders(self):
        """Migrate orders from SQLite to PostgreSQL."""
        print("📦 Migrating orders...")
        
        # First, get customer and menu item mappings
        customer_mapping = self.get_customer_mapping()
        menu_item_mapping = self.get_menu_item_mapping()
        
        with self.get_sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.cursor()
            
            # Get all orders
            cursor.execute('SELECT * FROM orders ORDER BY order_date')
            order_rows = cursor.fetchall()
            order_columns = [description[0] for description in cursor.description]
            
            migrated_count = 0
            for order_row in order_rows:
                order = dict(zip(order_columns, order_row))
                
                # Get order items
                cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
                item_rows = cursor.fetchall()
                
                if not item_rows:
                    continue
                
                item_columns = [description[0] for description in cursor.description]
                order_items = []
                
                for item_row in item_rows:
                    item = dict(zip(item_columns, item_row))
                    
                    # Map to new menu item ID
                    new_menu_item_id = menu_item_mapping.get(item['menu_item_id'])
                    if not new_menu_item_id:
                        print(f"  ⚠️  Skipping order item - menu item {item['menu_item_id']} not found")
                        continue
                    
                    # Parse customizations
                    customizations = {}
                    if item['customizations']:
                        try:
                            customizations = json.loads(item['customizations'])
                        except json.JSONDecodeError:
                            customizations = {}
                    
                    order_items.append({
                        'menu_item_id': new_menu_item_id,
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price'],
                        'customizations': customizations
                    })
                
                if not order_items:
                    continue
                
                # Map to new customer ID
                new_customer_id = customer_mapping.get(order['customer_id'])
                if not new_customer_id:
                    print(f"  ⚠️  Skipping order - customer {order['customer_id']} not found")
                    continue
                
                try:
                    new_order_id = self.postgres_db.add_order(
                        customer_id=new_customer_id,
                        items=order_items,
                        notes=order['notes']
                    )
                    
                    # Update order date if different
                    if order['order_date']:
                        with self.postgres_db.get_connection() as conn:
                            pg_cursor = conn.cursor()
                            pg_cursor.execute('''
                                UPDATE orders SET order_date = %s WHERE id = %s
                            ''', (order['order_date'], new_order_id))
                            conn.commit()
                    
                    migrated_count += 1
                    print(f"  ✅ Migrated order: {order['id']} → {new_order_id} ({len(order_items)} items)")
                    
                except Exception as e:
                    print(f"  ❌ Error migrating order {order['id']}: {e}")
            
            print(f"📊 Migrated {migrated_count} orders")
            return migrated_count
    
    def get_customer_mapping(self):
        """Get mapping of old customer IDs to new customer IDs."""
        mapping = {}
        
        # Get SQLite customers
        with self.get_sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.cursor()
            cursor.execute('SELECT id, name, email FROM customers')
            sqlite_customers = cursor.fetchall()
        
        # Get PostgreSQL customers
        postgres_customers = self.postgres_db.get_all_customers()
        
        for sqlite_id, name, email in sqlite_customers:
            for pg_customer in postgres_customers:
                if (pg_customer['name'] == name and 
                    pg_customer['email'] == email):
                    mapping[sqlite_id] = pg_customer['id']
                    break
        
        return mapping
    
    def get_menu_item_mapping(self):
        """Get mapping of old menu item IDs to new menu item IDs."""
        mapping = {}
        
        # Get SQLite menu items
        with self.get_sqlite_connection() as sqlite_conn:
            cursor = sqlite_conn.cursor()
            cursor.execute('SELECT id, name FROM menu_items')
            sqlite_items = cursor.fetchall()
        
        # Get PostgreSQL menu items
        postgres_items = self.postgres_db.get_menu_items(available_only=False)
        
        for sqlite_id, name in sqlite_items:
            for pg_item in postgres_items:
                if pg_item['name'] == name:
                    mapping[sqlite_id] = pg_item['id']
                    break
        
        return mapping
    
    def migrate_all(self):
        """Migrate all data from SQLite to PostgreSQL."""
        print("🔄 Starting migration from SQLite to PostgreSQL...")
        print("=" * 60)
        
        if not self.check_sqlite_exists():
            print("❌ SQLite database not found. Nothing to migrate.")
            return False
        
        try:
            # Test PostgreSQL connection
            with self.postgres_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
            print("✅ PostgreSQL connection successful")
            
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            print("Make sure PostgreSQL is running and credentials are correct.")
            return False
        
        try:
            # Migrate in order: customers, menu items, orders
            customer_count = self.migrate_customers()
            menu_count = self.migrate_menu_items()
            order_count = self.migrate_orders()
            
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print(f"📊 Summary:")
            print(f"   - Customers: {customer_count}")
            print(f"   - Menu Items: {menu_count}")
            print(f"   - Orders: {order_count}")
            print("")
            print("🚀 You can now use PostgreSQL with your cafe system!")
            print("🌐 Access pgAdmin at http://localhost:8080")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

def main():
    """Main migration function."""
    print("🏪 Cafe Face Recognition System - Database Migration")
    print("SQLite → PostgreSQL")
    print("=" * 60)
    
    migration = SQLiteToPostgreSQLMigration()
    
    # Confirm migration
    response = input("⚠️  This will migrate data from SQLite to PostgreSQL. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Migration cancelled.")
        return
    
    success = migration.migrate_all()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Update your environment variables to use PostgreSQL:")
        print("   export DATABASE_TYPE=postgresql")
        print("2. Restart your application")
        print("3. Verify data in pgAdmin")
        
        # Ask if user wants to backup SQLite
        backup_response = input("\n💾 Create backup of SQLite database? (Y/n): ")
        if backup_response.lower() not in ['n', 'no']:
            import shutil
            backup_path = f"data/cafe_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(migration.sqlite_db_path, backup_path)
            print(f"✅ SQLite backup created: {backup_path}")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main()
