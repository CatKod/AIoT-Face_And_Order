#!/usr/bin/env python3
"""
Café Face Recognition and Recommendation System
Main entry point for the application

This system provides:
1. Face recognition for customer identification
2. Order history tracking
3. Personalized recommendations
4. Web-based management interface
5. Camera integration for real-time recognition

Usage:
    python main.py [options]

Options:
    --mode web          Start web interface (default)
    --mode camera       Start camera recognition only
    --mode demo         Run demo mode with sample data
    --help             Show this help message
"""

import sys
import argparse
import threading
import time
from datetime import datetime

# Import our modules
from database_manager import DatabaseManager
try:
    from face_recognition_manager import FaceRecognitionManager
except ImportError:
    # Fallback to OpenCV version if face_recognition library is not available
    from face_recognition_manager_opencv import FaceRecognitionManager
    print("Note: Using OpenCV-based face recognition (install face_recognition library for better accuracy)")
from recommendation_engine import RecommendationEngine
from app import app
import config

def setup_database():
    """Initialize database with sample data if needed."""
    print("Setting up database...")
    db = DatabaseManager()
    
    # Check if we have any menu items
    items = db.get_menu_items()
    if not items:
        print("Populating database with sample menu items...")
        db.populate_sample_data()
        print("Sample data added successfully!")
    else:
        print(f"Database already contains {len(items)} menu items.")
    
    return db

def run_web_interface():
    """Start the Flask web application."""
    print(f"Starting web interface on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print("Access the dashboard to manage customers, orders, and view recommendations.")
    print("Press Ctrl+C to stop the server.")
    
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)

def run_camera_recognition():
    """Start camera-only recognition mode."""
    print("Starting camera recognition mode...")
    print("This will open a camera window for real-time face recognition.")
    print("Press 'q' in the camera window to quit.")
    
    face_manager = FaceRecognitionManager()
    db = DatabaseManager()
    
    def on_customer_recognized(customer_info):
        """Callback function when a customer is recognized."""
        customer = db.get_customer_by_id(customer_info['customer_id'])
        if customer:
            # Update visit count
            db.update_customer_visit(customer_info['customer_id'])
            
            # Get recommendations
            rec_engine = RecommendationEngine()
            recommendations = rec_engine.get_customer_recommendations(customer_info['customer_id'], limit=3)
            
            print(f"\n🎉 Customer Recognized: {customer['name']}")
            print(f"   Confidence: {customer_info['confidence']:.2f}")
            print(f"   Total visits: {customer['visit_count']}")
            
            if recommendations:
                print("   Recommended items:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec['item']['name']} - {rec['reason']}")
            else:
                print("   No recommendations available yet.")
            print("-" * 50)
    
    try:
        face_manager.start_camera_recognition(callback_function=on_customer_recognized)
    except KeyboardInterrupt:
        print("\nCamera recognition stopped.")

def run_demo_mode():
    """Run demonstration mode with sample data."""
    print("Running demo mode...")
    
    # Setup database
    db = setup_database()
    
    # Add a sample customer if none exist
    customers = db.get_all_customers()
    if not customers:
        print("Adding sample customer...")
        customer_id = db.add_customer("Demo Customer", "demo@cafe.com", "+1234567890")
        
        # Add some sample orders
        menu_items = db.get_menu_items()
        if menu_items:
            sample_orders = [
                [{'menu_item_id': menu_items[0]['id'], 'quantity': 1, 'unit_price': menu_items[0]['price']}],
                [{'menu_item_id': menu_items[1]['id'], 'quantity': 2, 'unit_price': menu_items[1]['price']}],
                [{'menu_item_id': menu_items[0]['id'], 'quantity': 1, 'unit_price': menu_items[0]['price']},
                 {'menu_item_id': menu_items[2]['id'], 'quantity': 1, 'unit_price': menu_items[2]['price']}]
            ]
            
            for order_items in sample_orders:
                db.add_order(customer_id, order_items, "Sample order")
                time.sleep(0.1)  # Small delay between orders
        
        print("Sample customer and orders added!")
    
    # Generate recommendations for demo
    rec_engine = RecommendationEngine()
    customer = customers[0] if customers else db.get_customer_by_id(1)
    
    if customer:
        print(f"\nDemo Customer: {customer['name']}")
        print(f"Total visits: {customer['visit_count']}")
        
        recommendations = rec_engine.get_customer_recommendations(customer['id'])
        if recommendations:
            print("\nPersonalized Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec['item']['name']} (${rec['item']['price']:.2f})")
                print(f"   Reason: {rec['reason']}")
                print(f"   Score: {rec['score']:.2f}\n")
        else:
            print("No recommendations available.")
    
    print(f"\nDemo complete! Start the web interface to explore more features:")
    print(f"python main.py --mode web")

def print_system_info():
    """Print system information and status."""
    print("=" * 60)
    print("🏪 CAFÉ FACE RECOGNITION & RECOMMENDATION SYSTEM")
    print("=" * 60)
    print(f"Version: 1.0.0")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check components
    try:
        db = DatabaseManager()
        customers = db.get_all_customers()
        menu_items = db.get_menu_items()
        print(f"📊 Database Status: ✅ Connected")
        print(f"   - Customers: {len(customers)}")
        print(f"   - Menu Items: {len(menu_items)}")
    except Exception as e:
        print(f"📊 Database Status: ❌ Error - {e}")
    
    try:
        face_manager = FaceRecognitionManager()
        known_faces = len(face_manager.known_face_encodings)
        print(f"👤 Face Recognition: ✅ Ready")
        print(f"   - Known Faces: {known_faces}")
    except Exception as e:
        print(f"👤 Face Recognition: ❌ Error - {e}")
    
    try:
        rec_engine = RecommendationEngine()
        print(f"🎯 Recommendation Engine: ✅ Ready")
    except Exception as e:
        print(f"🎯 Recommendation Engine: ❌ Error - {e}")
    
    print()
    print("📁 Project Structure:")
    print(f"   - Customer Data: {config.CUSTOMER_DIR}")
    print(f"   - Database: {config.DATABASE_FILE}")
    print(f"   - Web Interface: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print()

def main():
    """Main function to handle command line arguments and start the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="Café Face Recognition and Recommendation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start web interface (default)
  python main.py --mode web         # Start web interface
  python main.py --mode camera      # Start camera recognition only
  python main.py --mode demo        # Run demo with sample data
  python main.py --info             # Show system information
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['web', 'camera', 'demo'], 
        default='web',
        help='Execution mode (default: web)'
    )
    
    parser.add_argument(
        '--info', 
        action='store_true',
        help='Show system information and exit'
    )
    
    args = parser.parse_args()
    
    # Print system info if requested
    if args.info:
        print_system_info()
        return
    
    print_system_info()
    
    try:
        # Setup database
        setup_database()
        
        # Start the appropriate mode
        if args.mode == 'web':
            run_web_interface()
        elif args.mode == 'camera':
            run_camera_recognition()
        elif args.mode == 'demo':
            run_demo_mode()
            
    except KeyboardInterrupt:
        print("\n\nSystem shutdown requested. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check the error message above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()