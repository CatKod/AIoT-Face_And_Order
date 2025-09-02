import cv2
import numpy as np
import os
import pickle
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import config

class FaceRecognitionManager:
    """
    Manages face detection and recognition operations.
    Note: This is a simplified version using OpenCV's built-in face detection.
    For production use, install face_recognition library for better accuracy.
    """
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_customer_ids = []
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.load_known_faces()
        
    def load_known_faces(self):
        """Load all known face encodings from customer directories."""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_customer_ids = []
        
        if not os.path.exists(config.CUSTOMER_DIR):
            return
            
        for customer_folder in os.listdir(config.CUSTOMER_DIR):
            customer_path = os.path.join(config.CUSTOMER_DIR, customer_folder)
            if not os.path.isdir(customer_path):
                continue
                
            # Load customer metadata
            metadata_path = os.path.join(customer_path, "metadata.json")
            if not os.path.exists(metadata_path):
                continue
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # For the OpenCV version, we'll use simpler face templates
            encodings_path = os.path.join(customer_path, "face_templates.pkl")
            if os.path.exists(encodings_path):
                with open(encodings_path, 'rb') as f:
                    templates = pickle.load(f)
                
                # Add all templates for this customer
                for template in templates:
                    self.known_face_encodings.append(template)
                    self.known_face_names.append(metadata['name'])
                    self.known_customer_ids.append(metadata['customer_id'])
    
    def detect_faces_in_frame(self, frame: np.ndarray) -> Tuple[List, List]:
        """Detect faces in a video frame using OpenCV."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        face_locations = []
        face_encodings = []
        
        for (x, y, w, h) in faces:
            # Convert to (top, right, bottom, left) format
            face_locations.append((y, x + w, y + h, x))
            
            # Extract face region as "encoding" (simplified approach)
            face_region = gray[y:y+h, x:x+w]
            if face_region.size > 0:
                # Resize to standard size for comparison
                face_template = cv2.resize(face_region, (100, 100))
                face_encodings.append(face_template.flatten())
        
        return face_locations, face_encodings
    
    def recognize_faces(self, face_encodings: List) -> List[Dict]:
        """Recognize faces using template matching (simplified approach)."""
        recognized_customers = []
        
        for face_encoding in face_encodings:
            best_match_index = -1
            best_similarity = 0
            
            for i, known_encoding in enumerate(self.known_face_encodings):
                if len(face_encoding) == len(known_encoding):
                    # Calculate similarity using normalized correlation
                    similarity = cv2.matchTemplate(
                        face_encoding.reshape(100, 100).astype(np.float32),
                        known_encoding.reshape(100, 100).astype(np.float32),
                        cv2.TM_CCOEFF_NORMED
                    )[0][0]
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match_index = i
            
            # Use a threshold for recognition
            if best_similarity > 0.6:  # Adjust threshold as needed
                customer_info = {
                    'customer_id': self.known_customer_ids[best_match_index],
                    'name': self.known_face_names[best_match_index],
                    'confidence': best_similarity
                }
                recognized_customers.append(customer_info)
            else:
                recognized_customers.append(None)  # Unknown face
        
        return recognized_customers
    
    def capture_and_save_face(self, customer_id: int, customer_name: str, 
                             num_photos: int = 5) -> bool:
        """Capture multiple photos of a customer and save face templates."""
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return False
        
        # Create customer directory
        customer_folder = f"customer_{customer_id}_{customer_name.replace(' ', '_')}"
        customer_path = os.path.join(config.CUSTOMER_DIR, customer_folder)
        os.makedirs(customer_path, exist_ok=True)
        
        images_path = os.path.join(customer_path, "images")
        os.makedirs(images_path, exist_ok=True)
        
        captured_templates = []
        captured_count = 0
        
        print(f"Capturing {num_photos} photos for {customer_name}. Press SPACE to capture, ESC to cancel.")
        
        while captured_count < num_photos:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces in current frame
            face_locations, face_encodings = self.detect_faces_in_frame(frame)
            
            # Draw rectangles around detected faces
            for face_location in face_locations:
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Display frame
            cv2.putText(frame, f"Captured: {captured_count}/{num_photos}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture, ESC to cancel", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Face Capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space key
                if len(face_encodings) == 1:  # Exactly one face detected
                    # Save image
                    image_filename = f"image_{captured_count + 1}.jpg"
                    image_path = os.path.join(images_path, image_filename)
                    cv2.imwrite(image_path, frame)
                    
                    # Save template
                    captured_templates.append(face_encodings[0])
                    captured_count += 1
                    
                    print(f"Captured photo {captured_count}")
                    
                    # Visual feedback
                    cv2.rectangle(frame, (face_locations[0][3], face_locations[0][0]), 
                                (face_locations[0][1], face_locations[0][2]), (0, 255, 0), 2)
                    cv2.imshow('Face Capture', frame)
                    cv2.waitKey(500)  # Show for 500ms
                    
                elif len(face_encodings) == 0:
                    print("No face detected. Please position your face in the frame.")
                else:
                    print("Multiple faces detected. Please ensure only one person is in the frame.")
            
            elif key == 27:  # ESC key
                print("Capture cancelled")
                cap.release()
                cv2.destroyAllWindows()
                return False
        
        cap.release()
        cv2.destroyAllWindows()
        
        if captured_count == num_photos:
            # Save face templates
            templates_path = os.path.join(customer_path, "face_templates.pkl")
            with open(templates_path, 'wb') as f:
                pickle.dump(captured_templates, f)
            
            # Save metadata
            metadata = {
                'customer_id': customer_id,
                'name': customer_name,
                'num_templates': len(captured_templates),
                'created_at': datetime.now().isoformat(),
                'images_path': images_path,
                'recognition_method': 'opencv_template_matching'
            }
            
            metadata_path = os.path.join(customer_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Reload known faces
            self.load_known_faces()
            
            print(f"Successfully saved {captured_count} face templates for {customer_name}")
            return True
        
        return False
    
    def start_camera_recognition(self, callback_function=None):
        """Start real-time camera recognition with callback for recognized customers."""
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("Starting face recognition. Press 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect and recognize faces
            face_locations, face_encodings = self.detect_faces_in_frame(frame)
            recognized_customers = self.recognize_faces(face_encodings)
            
            # Draw rectangles and labels
            for i, (face_location, customer_info) in enumerate(zip(face_locations, recognized_customers)):
                top, right, bottom, left = face_location
                
                if customer_info:
                    # Known customer
                    color = (0, 255, 0)  # Green
                    name = f"{customer_info['name']} ({customer_info['confidence']:.2f})"
                    
                    # Call callback function if provided
                    if callback_function:
                        callback_function(customer_info)
                else:
                    # Unknown person
                    color = (0, 0, 255)  # Red
                    name = "Unknown"
                
                # Draw rectangle and name
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), 
                          cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Display frame
            cv2.imshow('Cafe Face Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def get_face_encoding_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """Get face encoding from a single image file."""
        if not os.path.exists(image_path):
            return None
        
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        face_locations, face_encodings = self.detect_faces_in_frame(image)
        
        if len(face_encodings) > 0:
            return face_encodings[0]
        return None
