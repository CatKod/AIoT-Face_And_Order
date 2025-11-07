# 🎥 ESP32-CAM Face Detection System

Hệ thống nhận diện khuôn mặt real-time sử dụng ESP32-CAM và Flask Server với OpenCV.

## 📋 Tính năng

- ✅ Server Flask chạy trên cổng 5000
- ✅ Nhận ảnh từ ESP32-CAM qua HTTP POST
- ✅ Nhận diện khuôn mặt real-time bằng OpenCV (Haar Cascade)
- ✅ Hiển thị video stream với khung hình nhận diện
- ✅ Web interface đẹp mắt và responsive
- ✅ Hỗ trợ nhiều định dạng ảnh (binary, base64)

## 🚀 Cài đặt và Chạy

### 1. Cài đặt Python packages

```cmd
pip install -r requirements.txt
```

### 2. Chạy Flask Server

```cmd
python app.py
```

Server sẽ chạy tại: `http://192.168.1.28:5000/`

### 3. Truy cập Web Interface

Mở trình duyệt và truy cập:
- **Trang chủ:** http://192.168.1.28:5000/
- **Video Stream:** http://192.168.1.28:5000/stream
- **Ảnh mới nhất:** http://192.168.1.28:5000/latest

## 📡 Cấu hình ESP32-CAM

### Bước 1: Upload code Arduino

1. Mở file `arduino/esp32_cam_upload.ino` trong Arduino IDE
2. Thay đổi WiFi credentials:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```
3. Kiểm tra server URL (thay IP nếu cần):
```cpp
const char* serverUrl = "http://192.168.1.28:5000/upload";
```
4. Upload code lên ESP32-CAM

### Bước 2: Kết nối và Test

- ESP32-CAM sẽ tự động kết nối WiFi
- Chụp ảnh mỗi 2 giây
- Gửi ảnh lên Flask server
- Xem log qua Serial Monitor (115200 baud)

## 📂 Cấu trúc Project

```
AIoT-Face_And_Order/
├── app.py                      # Flask server chính
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Web interface
├── static/
│   └── face_detected.jpg      # Ảnh mới nhất (tự động tạo)
├── arduino/
│   ├── esp32_cam_upload.ino   # Code cho ESP32-CAM
│   └── esp32_cam_info.txt     # Thông tin server
└── README.md                  # File này
```

## 🔌 API Endpoints

### POST /upload
Nhận ảnh từ ESP32-CAM

**Request:**
- **Method:** POST
- **Content-Type:** 
  - `image/jpeg` (binary)
  - `application/json` (base64)

**Binary Upload (Recommended):**
```cpp
// Arduino ESP32
http.addHeader("Content-Type", "image/jpeg");
http.POST(fb->buf, fb->len);
```

**Base64 Upload:**
```json
{
  "image": "base64_encoded_jpeg_string"
}
```

**Response:**
```json
{
  "status": "success",
  "faces_detected": 2,
  "message": "Detected 2 face(s)"
}
```

### GET /stream
Video stream MJPEG với khung hình nhận diện

### GET /latest
Lấy ảnh mới nhất đã nhận diện (JPEG)

### GET /status
Kiểm tra trạng thái server

## 🛠️ Công nghệ sử dụng

- **Backend:** Flask (Python web framework)
- **Computer Vision:** OpenCV với Haar Cascade
- **Frontend:** HTML5, CSS3, JavaScript
- **Hardware:** ESP32-CAM
- **Protocol:** HTTP, MJPEG streaming

## 📊 Cách hoạt động

### Luồng xử lý:

1. **ESP32-CAM:**
   - Chụp ảnh JPEG
   - POST binary data đến `/upload`
   - Nhận response JSON

2. **Flask Server:**
   - Nhận ảnh từ request
   - Decode thành OpenCV image
   - Nhận diện khuôn mặt (Haar Cascade)
   - Vẽ khung hình chữ nhật
   - Lưu vào `static/face_detected.jpg`
   - Stream qua `/stream` endpoint

3. **Web Interface:**
   - Hiển thị MJPEG stream
   - Auto-refresh mỗi 30s nếu mất kết nối
   - Hiển thị trạng thái real-time

## 🎨 Face Detection Algorithm

Sử dụng **Haar Cascade Classifier** của OpenCV:

```python
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)
```

**Tham số nhận diện:**
- `scaleFactor=1.1`: Tăng kích thước cửa sổ tìm kiếm 10%
- `minNeighbors=5`: Số vùng láng giềng tối thiểu
- `minSize=(30, 30)`: Kích thước khuôn mặt nhỏ nhất

## 🔧 Troubleshooting

### Server không khởi động được
```cmd
# Kiểm tra port 5000 có bị chiếm không
netstat -ano | findstr :5000

# Đổi port trong app.py nếu cần
app.run(host='0.0.0.0', port=5001)
```

### ESP32-CAM không gửi được ảnh
- Kiểm tra WiFi credentials
- Kiểm tra IP của server (dùng `ipconfig`)
- Kiểm tra firewall có block port 5000 không
- Xem Serial Monitor để debug

### Không nhận diện được khuôn mặt
- Đảm bảo ánh sáng đủ
- Khuôn mặt phải nhìn thẳng camera
- Tăng `minNeighbors` nếu có nhiều false positive
- Giảm `minSize` để phát hiện khuôn mặt nhỏ hơn

### Stream lag hoặc chậm
- Giảm quality trong ESP32: `config.jpeg_quality = 15`
- Giảm frame size: `config.frame_size = FRAMESIZE_VGA`
- Tăng delay giữa các frame: `delay(3000)`

## 📝 Lưu ý

- Server phải và ESP32-CAM phải cùng mạng WiFi
- Thay đổi IP `192.168.1.28` thành IP thực của máy chạy Flask
- Sử dụng `ipconfig` (Windows) hoặc `ifconfig` (Linux/Mac) để xem IP
- Port 5000 phải được mở trong firewall

## 🔒 Bảo mật

⚠️ **Cảnh báo:** Code này dùng cho mục đích học tập và demo.

Để deploy production, cần:
- Thêm authentication
- Sử dụng HTTPS
- Rate limiting
- Validation input
- Error handling tốt hơn

## 📄 License

MIT License - Free to use for educational purposes

## 👨‍💻 Author

Created with ❤️ for AIoT Face Detection Project

---

**📞 Hỗ trợ:**
Nếu gặp vấn đề, hãy kiểm tra:
1. Python version >= 3.7
2. OpenCV được cài đặt đúng
3. ESP32-CAM board definition trong Arduino IDE
4. WiFi và network connectivity
