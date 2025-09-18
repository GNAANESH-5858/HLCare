# Health Link Care

Emergency medical records system with QR authentication and AI-powered summaries.

## Features

- QR code scanning for patient identification
- Emergency medical summaries
- Secure authentication
- Responsive web design
- AI-powered medical data analysis

## Setup

### Option 1: Easy Run (Windows)
1. Double-click `Start_hidden.vbs`
2. Open http://localhost:5000 in your browser

### Option 2: Easy Run (Mac/Linux)
1. Make script executable: `chmod +x run_app.sh`
2. Double-click `run_app.sh` or run `./run_app.sh`
3. Open http://localhost:5000 in your browser

### Option 3: Manual Setup
1. Install Python requirements: `pip install -r requirements.txt`
2. Run the application: `python app.py`
3. Open http://localhost:5000 in your browser

## Test Credentials

- ABHA ID: `1234-5675-9877-98` (Arjun Kumar)
- ABHA ID: `6789-0854-8484-85` (Ravi Singh)


## API Endpoints

- `GET /` - Main application
- `GET /init-db` - Initialize database with sample data
- `GET /emergency/<health_id>` - Get emergency summary
- `POST /login` - Authenticate user
- `GET /records/<health_id>` - Get detailed records

## Technology Stack

- Backend: Python Flask
- Frontend: HTML5, CSS3, JavaScript
- Database: SQLite

- QR Scanning: jsQR library
