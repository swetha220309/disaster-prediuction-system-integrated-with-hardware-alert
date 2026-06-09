# Disaster Prediction System Integrated with Hardware Alert

## Overview

The Disaster Prediction System Integrated with Hardware Alert is a web-based application developed using Django that predicts potential natural disasters using sensor data and provides real-time alerts through hardware integration. The system aims to improve disaster preparedness and reduce risks by delivering timely warnings.

## Features

* Real-time disaster prediction
* Sensor data monitoring
* Hardware-based alert system
* User-friendly web interface
* Data visualization and analysis
* Early warning notifications
* Secure and reliable system architecture

## Technologies Used

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Python
* Django Framework

### Database

* SQLite

### Hardware Components

* Sensors (as per project implementation)
* Alert/Buzzer Module
* Microcontroller (Arduino/ESP32 if applicable)

## Project Structure

```text
disaster-prediction-system-integrated-with-hardware-alert/
│
├── manage.py
├── db.sqlite3
├── disaster_detection/
├── predictor/
├── templates/
├── static/
└── requirements.txt
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/USERNAME/disaster-prediction-system-integrated-with-hardware-alert.git
cd disaster-prediction-system-integrated-with-hardware-alert
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Start the Server

```bash
python manage.py runserver
```

### 7. Open in Browser

```text
http://127.0.0.1:8000/
```

## Working

1. Sensor data is collected from connected hardware devices.
2. The system processes the data and performs disaster prediction.
3. Prediction results are displayed through the web interface.
4. If a risk is detected, the hardware alert module is triggered.
5. Users receive early warnings for preventive action.

## Future Enhancements

* Integration with IoT cloud platforms
* SMS and Email alerts
* Mobile application support
* Advanced machine learning models
* Real-time weather API integration

## Authors

### Project Leader

* Swetha Sathyan

### Team Members

* Swathy Sreenivas
* Pooja Appukuttan
* Tammana Jayarajan

## License

This project is developed for educational and research purposes.
