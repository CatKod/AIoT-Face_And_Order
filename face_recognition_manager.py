import cv2
import face_recognition
import numpy as np
import os
import pickle
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import config

class FaceRecognitionManager:
    """Manages face detection, recognition, and encoding operations."""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_customer_ids = []
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
            
            # Load face encodings
            encodings_path = os.path.join(customer_path, "face_encodings.pkl")
            if os.path.exists(encodings_path):
                with open(encodings_path, 'rb') as f:
                    encodings = pickle.load(f)
                
                # Add all encodings for this customer
                for encoding in encodings:
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(metadata['name'])
                    self.known_customer_ids.append(metadata['customer_id'])
    
    def detect_faces_in_frame(self, frame: np.ndarray) -> Tuple[List, List]:
        """Detect faces in a video frame and return locations and encodings."""
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]  # Convert BGR to RGB
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        # Scale back up face locations
        face_locations = [(top*4, right*4, bottom*4, left*4) for (top, right, bottom, left) in face_locations]
        
        return face_locations, face_encodings
    
    def recognize_faces(self, face_encodings: List) -> List[Dict]:
        """Recognize faces from encodings and return customer information."""
        recognized_customers = []
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding, 
                tolerance=config.FACE_DETECTION_TOLERANCE
            )
            
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index] and face_distances[best_match_index] < config.MAX_FACE_DISTANCE:
                    customer_info = {
                        'customer_id': self.known_customer_ids[best_match_index],
                        'name': self.known_face_names[best_match_index],
                        'confidence': 1 - face_distances[best_match_index]
                    }
                    recognized_customers.append(customer_info)
                else:
                    recognized_customers.append(None)  # Unknown face
            else:
                recognized_customers.append(None)  # No known faces to compare
        
        return recognized_customers
    
    def capture_and_save_face(self, customer_id: int, customer_name: str, 
                             num_photos: int = 5) -> bool:
        """Capture multiple photos of a customer and save face encodings."""
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
        
        captured_encodings = []
        captured_count = 0
        
        print(f"Capturing {num_photos} photos for {customer_name}. Press SPACE to capture, ESC to cancel.")
        
        while captured_count < num_photos:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Display frame
            cv2.putText(frame, f"Captured: {captured_count}/{num_photos}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture, ESC to cancel", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Face Capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space key
                # Process the frame
                face_locations, face_encodings = self.detect_faces_in_frame(frame)
                
                if len(face_encodings) == 1:  # Exactly one face detected
                    # Save image
                    image_filename = f"image_{captured_count + 1}.jpg"
                    image_path = os.path.join(images_path, image_filename)
                    cv2.imwrite(image_path, frame)
                    
                    # Save encoding
                    captured_encodings.append(face_encodings[0])
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
            # Save face encodings
            encodings_path = os.path.join(customer_path, "face_encodings.pkl")
            with open(encodings_path, 'wb') as f:
                pickle.dump(captured_encodings, f)
            
            # Save metadata
            metadata = {
                'customer_id': customer_id,
                'name': customer_name,
                'num_encodings': len(captured_encodings),
                'created_at': datetime.now().isoformat(),
                'images_path': images_path
            }
            
            metadata_path = os.path.join(customer_path, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Reload known faces
            self.load_known_faces()
            
            print(f"Successfully saved {captured_count} face encodings for {customer_name}")
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
        
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) > 0:
            return face_encodings[0]
        return None
