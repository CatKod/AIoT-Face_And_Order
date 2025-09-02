from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
import cv2
import base64
import numpy as np
import json
from datetime import datetime
import os
import threading
from flask import Response

# Import our custom modules
from database_manager import DatabaseManager
try:
    from face_recognition_manager import FaceRecognitionManager
except ImportError:
    # Fallback to OpenCV version if face_recognition library is not available
    from face_recognition_manager_opencv import FaceRecognitionManager
from recommendation_engine import RecommendationEngine
import config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
CORS(app)

# Initialize components
db_manager = DatabaseManager()
face_manager = FaceRecognitionManager()
recommendation_engine = RecommendationEngine()

# Global variables for camera state
camera_active = False
recognized_customer = None

# Global variables for video streaming
camera = None
video_active = False
recognition_active = False
latest_recognition_result = None

def generate_frames():
    """Generate video frames for streaming."""
    global camera, video_active, recognition_active, latest_recognition_result
    
    while video_active:
        if camera is None:
            camera = cv2.VideoCapture(config.CAMERA_INDEX)
            if not camera.isOpened():
                break
        
        success, frame = camera.read()
        if not success:
            break
        
        # Perform face recognition if enabled
        if recognition_active:
            try:
                face_locations, face_encodings = face_manager.detect_faces_in_frame(frame)
                recognized_customers = face_manager.recognize_faces(face_encodings)
                
                # Draw rectangles and labels
                for i, (face_location, customer_info) in enumerate(zip(face_locations, recognized_customers)):
                    top, right, bottom, left = face_location
                    
                    if customer_info:
                        # Known customer
                        color = (0, 255, 0)  # Green
                        name = f"{customer_info['name']} ({customer_info['confidence']:.2f})"
                        latest_recognition_result = customer_info
                        
                        # Update visit count
                        db_manager.update_customer_visit(customer_info['customer_id'])
                    else:
                        # Unknown person
                        color = (0, 0, 255)  # Red
                        name = "Unknown"
                        latest_recognition_result = None
                    
                    # Draw rectangle and name
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 6), 
                              cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            except Exception as e:
                print(f"Recognition error: {e}")
        
        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Main dashboard page."""
    recent_customers = db_manager.get_all_customers()[:10]  # Get 10 most recent customers
    popular_items = db_manager.get_popular_items(5)
    
    return render_template('index.html', 
                         recent_customers=recent_customers,
                         popular_items=popular_items)

@app.route('/customers')
def customers():
    """Customer management page."""
    all_customers = db_manager.get_all_customers()
    return render_template('customers.html', customers=all_customers)

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    """Individual customer detail page."""
    customer = db_manager.get_customer_by_id(customer_id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers'))
    
    order_history = db_manager.get_customer_order_history(customer_id, limit=20)
    recommendations = recommendation_engine.get_customer_recommendations(customer_id)
    
    return render_template('customer_detail.html', 
                         customer=customer,
                         order_history=order_history,
                         recommendations=recommendations)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    """Add new customer page."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        
        # Add customer to database
        customer_id = db_manager.add_customer(name, email, phone)
        
        # Capture face photos
        success = face_manager.capture_and_save_face(customer_id, name)
        
        if success:
            flash(f'Customer {name} added successfully!', 'success')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        else:
            flash('Failed to capture face photos. Please try again.', 'error')
            return redirect(url_for('add_customer'))
    
    return render_template('add_customer.html')

@app.route('/menu')
def menu():
    """Menu management page."""
    food_items = db_manager.get_menu_items(category='food')
    drink_items = db_manager.get_menu_items(category='drink')
    
    return render_template('menu.html', 
                         food_items=food_items,
                         drink_items=drink_items)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    """Add new menu item."""
    try:
        name = request.form['name']
        category = request.form['category']
        subcategory = request.form.get('subcategory', '')
        price = float(request.form['price'])
        description = request.form.get('description', '')
        ingredients = request.form.get('ingredients', '').split(',')
        allergens = request.form.get('allergens', '').split(',')
        calories = int(request.form.get('calories', 0)) if request.form.get('calories') else None
        
        # Clean up lists
        ingredients = [ing.strip() for ing in ingredients if ing.strip()]
        allergens = [all.strip() for all in allergens if all.strip()]
        
        item_id = db_manager.add_menu_item(
            name=name,
            category=category,
            subcategory=subcategory if subcategory else None,
            price=price,
            ingredients=ingredients if ingredients else None,
            allergens=allergens if allergens else None,
            calories=calories,
            description=description if description else None
        )
        
        flash(f'Menu item "{name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding menu item: {str(e)}', 'error')
    
    return redirect(url_for('menu'))

@app.route('/orders')
def orders():
    """Order management page."""
    # Get recent orders across all customers
    all_customers = db_manager.get_all_customers()
    recent_orders = []
    
    for customer in all_customers[:20]:  # Limit to recent customers
        customer_orders = db_manager.get_customer_order_history(customer['id'], limit=5)
        for order in customer_orders:
            order['customer_name'] = customer['name']
            recent_orders.append(order)
    
    # Sort by date
    recent_orders.sort(key=lambda x: x['order_date'], reverse=True)
    
    return render_template('orders.html', orders=recent_orders[:50])

@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    """Create new order page."""
    if request.method == 'POST':
        try:
            customer_id = int(request.form['customer_id'])
            notes = request.form.get('notes', '')
            
            # Parse order items
            items = []
            menu_items = db_manager.get_menu_items()
            
            for key, value in request.form.items():
                if key.startswith('quantity_') and int(value) > 0:
                    menu_item_id = int(key.split('_')[1])
                    quantity = int(value)
                    
                    # Find menu item details
                    menu_item = next((item for item in menu_items if item['id'] == menu_item_id), None)
                    if menu_item:
                        items.append({
                            'menu_item_id': menu_item_id,
                            'quantity': quantity,
                            'unit_price': menu_item['price'],
                            'customizations': {}
                        })
            
            if items:
                order_id = db_manager.add_order(customer_id, items, notes)
                db_manager.update_customer_visit(customer_id)
                flash('Order created successfully!', 'success')
                return redirect(url_for('orders'))
            else:
                flash('Please select at least one item', 'error')
        
        except Exception as e:
            flash(f'Error creating order: {str(e)}', 'error')
    
    # GET request - show order form
    customers = db_manager.get_all_customers()
    menu_items = db_manager.get_menu_items()
    
    return render_template('create_order.html', 
                         customers=customers,
                         menu_items=menu_items)

@app.route('/recognition')
def recognition():
    """Face recognition page."""
    return render_template('recognition.html')

@app.route('/api/start_recognition', methods=['POST'])
def start_recognition():
    """Start face recognition camera."""
    global recognition_active, video_active, camera
    recognition_active = True
    video_active = True
    return jsonify({'status': 'started'})

@app.route('/api/stop_recognition', methods=['POST'])
def stop_recognition():
    """Stop face recognition camera."""
    global recognition_active, video_active, camera
    recognition_active = False
    video_active = False
    if camera:
        camera.release()
        camera = None
    return jsonify({'status': 'stopped'})

@app.route('/api/get_latest_recognition')
def get_latest_recognition():
    """Get the latest recognition result."""
    global latest_recognition_result
    if latest_recognition_result:
        customer = db_manager.get_customer_by_id(latest_recognition_result['customer_id'])
        recommendations = recommendation_engine.get_customer_recommendations(latest_recognition_result['customer_id'], limit=3)
        
        return jsonify({
            'recognized': True,
            'customer': customer,
            'confidence': latest_recognition_result['confidence'],
            'recommendations': recommendations
        })
    else:
        return jsonify({'recognized': False})

@app.route('/api/get_recommendations/<int:customer_id>')
def get_recommendations(customer_id):
    """Get recommendations for a customer via API."""
    try:
        recommendations = recommendation_engine.get_customer_recommendations(customer_id)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer_stats/<int:customer_id>')
def customer_stats(customer_id):
    """Get customer statistics."""
    try:
        customer = db_manager.get_customer_by_id(customer_id)
        order_history = db_manager.get_customer_order_history(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Calculate stats
        total_orders = len(order_history)
        total_spent = sum(order['total_amount'] for order in order_history)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Most ordered items
        item_counts = {}
        for order in order_history:
            for item in order['items']:
                item_name = item['item_name']
                item_counts[item_name] = item_counts.get(item_name, 0) + item['quantity']
        
        most_ordered = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats = {
            'customer': customer,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'average_order_value': avg_order_value,
            'most_ordered_items': most_ordered
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/menu_items')
def api_menu_items():
    """Get all menu items via API."""
    try:
        items = db_manager.get_menu_items()
        return jsonify({'menu_items': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    global video_active
    video_active = True
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
    os.makedirs(config.STATIC_DIR, exist_ok=True)
    
    # Populate sample data if database is empty
    try:
        existing_items = db_manager.get_menu_items()
        if not existing_items:
            db_manager.populate_sample_data()
            print("Sample menu data populated!")
    except Exception as e:
        print(f"Error populating sample data: {e}")
    
    print(f"Starting Café Face Recognition System...")
    print(f"Visit http://{config.FLASK_HOST}:{config.FLASK_PORT} to access the web interface")
    
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
