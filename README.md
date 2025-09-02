# 🏪 Café Face Recognition & Recommendation System

A comprehensive AI-powered system for cafés that recognizes returning customers using face recognition and provides personalized food and drink recommendations based on their order history.

## 🌟 Features

### 👤 Face Recognition
- **Real-time customer detection** using connected camera
- **Secure face data storage** in organized customer folders
- **High accuracy recognition** with confidence scoring
- **Privacy-focused** data handling

### 📊 Customer Management
- **Complete customer profiles** with contact information
- **Visit tracking** and frequency analysis
- **Order history** with detailed item tracking
- **Easy customer registration** with guided photo capture

### 🎯 Intelligent Recommendations
- **Frequency-based suggestions** from past orders
- **Similarity matching** for related menu items
- **Recency weighting** for recent preferences
- **Complementary item suggestions** (e.g., pastry with coffee)

### 💻 Web Interface
- **Modern, responsive design** using Bootstrap
- **Real-time recognition dashboard**
- **Order management** and creation
- **Menu management** with categories and pricing
- **Customer analytics** and statistics

### 🏗️ Modular Architecture
- **Scalable database design** with SQLite
- **Configurable recommendation engine**
- **Extensible for future AI enhancements**
- **RESTful API** for integration

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Camera** connected to your computer
3. **Good lighting** for face detection
4. **Windows/macOS/Linux** (tested on Windows)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CatKod/AIoT-Face_And_Order.git
   cd AIoT-Face_And_Order
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the system**
   ```bash
   python main.py --info
   ```

### First Run

1. **Start the web interface**
   ```bash
   python main.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Add your first customer**
   - Click "Add Customer" in the dashboard
   - Enter customer information
   - Follow the camera prompts to capture face photos

4. **Start using the system**
   - Go to "Live Recognition" to test face detection
   - Create orders and track customer preferences
   - View personalized recommendations

## 📋 Detailed Usage

### Command Line Options

```bash
# Start web interface (default)
python main.py
python main.py --mode web

# Camera-only mode for recognition
python main.py --mode camera

# Demo mode with sample data
python main.py --mode demo

# Show system information
python main.py --info
```

### Web Interface Features

#### 🏠 Dashboard
- Overview of customers and popular items
- Quick access to all features
- System statistics

#### 👥 Customer Management
- View all customers with visit counts
- Detailed customer profiles
- Order history and statistics
- Face recognition status

#### 🎯 Live Recognition
- Real-time camera feed
- Automatic customer detection
- Recognition confidence scoring
- Quick order creation

#### 🍽️ Menu Management
- Add/edit menu items
- Category organization (food/drinks)
- Price and ingredient management
- Allergen information

#### 🛒 Order Management
- Create new orders
- View order history
- Customer order tracking
- Order analytics

### Face Recognition Setup

1. **Camera Requirements**
   - USB camera or built-in webcam
   - Good lighting conditions
   - Clear background preferred

2. **Customer Photo Capture**
   - Position customer facing the camera
   - Capture 5 photos from different angles
   - Press SPACE to capture each photo
   - Press ESC to cancel

3. **Recognition Tips**
   - Ensure good lighting
   - Remove sunglasses/hats
   - Look directly at camera
   - Maintain natural expression

### Recommendation System

The system uses multiple algorithms to generate recommendations:

1. **Frequency-based** (40% weight)
   - Items ordered most frequently by the customer

2. **Similarity-based** (30% weight)
   - Items similar to previously ordered items
   - Based on category, ingredients, and characteristics

3. **Recency-based** (30% weight)
   - Recent ordering patterns and preferences

4. **Complementary items**
   - Items commonly ordered together
   - Example: pastries with coffee

## 📁 Project Structure

```
AIoT-Face_And_Order/
├── main.py                    # Main entry point
├── config.py                  # Configuration settings
├── database_manager.py        # Database operations
├── face_recognition_manager.py # Face recognition logic
├── recommendation_engine.py   # Recommendation algorithms
├── app.py                     # Flask web application
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── customer/                 # Customer face data
│   └── customer_*/           # Individual customer folders
│       ├── metadata.json     # Customer information
│       ├── face_encodings.pkl # Face recognition data
│       └── images/           # Original photos
├── database/                 # Database files
│   └── cafe_system.db       # SQLite database
└── templates/               # HTML templates
    ├── base.html
    ├── index.html
    ├── customers.html
    └── ...
```

## 🔧 Configuration

Edit `config.py` to customize:

- **Camera settings** (device index, resolution)
- **Recognition parameters** (tolerance, model type)
- **Database location**
- **Web server settings**
- **Recommendation weights**

Example configuration:
```python
# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Face recognition settings
FACE_DETECTION_TOLERANCE = 0.6
MAX_FACE_DISTANCE = 0.5

# Recommendation weights
RECOMMENDATION_WEIGHT_FREQUENCY = 0.4
RECOMMENDATION_WEIGHT_RECENCY = 0.3
RECOMMENDATION_WEIGHT_SIMILARITY = 0.3
```

## 🛠️ Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera connection
   - Try different camera index in config
   - Ensure camera permissions are granted

2. **Face recognition not working**
   - Verify dlib installation
   - Check lighting conditions
   - Ensure face is clearly visible

3. **Database errors**
   - Check file permissions
   - Verify SQLite installation
   - Check disk space

4. **Web interface not loading**
   - Check if port 5000 is available
   - Verify Flask installation
   - Check firewall settings

### Performance Optimization

1. **For better recognition speed**
   - Use smaller camera resolution
   - Set `FACE_ENCODING_MODEL = "small"`
   - Reduce frame processing rate

2. **For better accuracy**
   - Use higher resolution
   - Set `FACE_ENCODING_MODEL = "large"`
   - Capture more training photos

## 🔒 Privacy & Security

- **Face data encryption** during storage
- **Local data processing** - no cloud uploads
- **Secure customer folders** with permissions
- **GDPR-compliant** data handling options
- **Consent tracking** in customer records

## 🚀 Future Enhancements

- [ ] **Mobile app** for staff
- [ ] **Advanced analytics** dashboard
- [ ] **Inventory integration**
- [ ] **Payment system** integration
- [ ] **Multi-camera support**
- [ ] **Cloud sync** options
- [ ] **Machine learning** preference prediction
- [ ] **Voice ordering** integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration options

## 🙏 Acknowledgments

- **OpenCV** for computer vision
- **face_recognition** library for face detection
- **Flask** for web framework
- **scikit-learn** for recommendation algorithms
- **Bootstrap** for UI components

---

**Built with ❤️ for modern cafés seeking to enhance customer experience through AI technology.**
