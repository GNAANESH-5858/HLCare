from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import uuid
import os
import sys
import re
from datetime import datetime, timedelta
# Add these imports
import logging
import traceback

# Set up logging to see errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this function to check dependencies
def check_dependencies():
    try:
        import flask
        import flask_cors
        import flask_sqlalchemy
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.path.join(BASE_DIR, "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path="/")
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static')
CORS(app)

# SQLite database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Import summarizer
try:
    from ai.summarizer import generate_summary
except ImportError:
    # Fallback if summarizer is not available
    def generate_summary(text):
        return "AI summary not available - summarizer module missing"

# ---- Models ----
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    health_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120))
    blood_group = db.Column(db.String(10))
    allergies = db.Column(db.String(300))
    emergency_contact = db.Column(db.String(50))
    current_medications = db.Column(db.String(500))
    conditions = db.Column(db.String(500))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    section = db.Column(db.String(80))
    title = db.Column(db.String(200))
    value = db.Column(db.String(500))
    date = db.Column(db.String(20))

# ---- Initialize Database ----
@app.route("/init-db")
def init_db():
    db.create_all()
    if Patient.query.first():
        return jsonify({"status":"already seeded"})
    
    # Create sample patients with more medical data
    p1 = Patient(
        health_id="1234-5675-9877-98", 
        name="Arjun Kumar", 
        blood_group="B+", 
        allergies="Peanuts, Dust",
        emergency_contact="9876543210",
        current_medications="Metformin 500mg daily",
        conditions="Type 2 Diabetes, Hypertension"
    )
    p2 = Patient(
        health_id="6789-0854-8484-85", 
        name="Ravi Singh", 
        blood_group="O+", 
        allergies="None known",
        emergency_contact="9123456780",
        current_medications="Aspirin 81mg daily",
        conditions="High cholesterol"
    )
    db.session.add_all([p1, p2])
    db.session.commit()
    
    # Create comprehensive sample reports
    reports = [
        # Patient 1 reports
        Report(patient_id=p1.id, section="vitals", title="Blood Pressure", value="130/85 mmHg", date="2025-01-15"),
        Report(patient_id=p1.id, section="vitals", title="Heart Rate", value="72 bpm", date="2025-01-15"),
        Report(patient_id=p1.id, section="labs", title="Blood Glucose", value="145 mg/dL", date="2025-01-10"),
        Report(patient_id=p1.id, section="labs", title="HbA1c", value="6.8%", date="2025-01-10"),
        Report(patient_id=p1.id, section="labs", title="Cholesterol", value="210 mg/dL", date="2025-01-10"),
        Report(patient_id=p1.id, section="history", title="Past Surgeries", value="Appendectomy (2015)", date="2015-06-20"),
        
        # Patient 2 reports
        Report(patient_id=p2.id, section="vitals", title="Blood Pressure", value="120/80 mmHg", date="2025-01-12"),
        Report(patient_id=p2.id, section="labs", title="Cholesterol", value="240 mg/dL", date="2025-01-08"),
        Report(patient_id=p2.id, section="labs", title="LDL", value="160 mg/dL", date="2025-01-08"),
        Report(patient_id=p2.id, section="history", title="Allergies", value="No known allergies", date="2024-12-01")
    ]
    db.session.add_all(reports)
    db.session.commit()
    
    return jsonify({"status":"db initialized with sample data"})

# ---- Helper Functions ----
def extract_abha_id(qr_data):
    """
    Extract ABHA ID from various QR code formats
    Supports: 14-digit numbers, XXXX-XXXX-XXXX-XX format, and text containing ABHA
    """
    if not qr_data:
        return None
        
    qr_data = qr_data.strip()
    
    # Case 1: 14-digit number (12345678901234)
    if qr_data.isdigit() and len(qr_data) == 14:
        return f"{qr_data[:4]}-{qr_data[4:8]}-{qr_data[8:12]}-{qr_data[12:14]}"
    
    # Case 2: Already in ABHA format (XXXX-XXXX-XXXX-XX)
    if len(qr_data) == 17 and qr_data.count('-') == 3:
        parts = qr_data.split('-')
        if (len(parts[0]) == 4 and len(parts[1]) == 4 and 
            len(parts[2]) == 4 and len(parts[3]) == 2):
            return qr_data
    
    # Case 3: Text containing ABHA ID pattern
    abha_pattern = r'\b(\d{4}-\d{4}-\d{4}-\d{2})\b'
    match = re.search(abha_pattern, qr_data)
    if match:
        return match.group(1)
    
    # Case 4: 14-digit number within text
    digit_pattern = r'\b(\d{14})\b'
    match = re.search(digit_pattern, qr_data)
    if match:
        digits = match.group(1)
        return f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:14]}"
    
    return None

# ---- Routes ----
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/emergency/<health_id>", methods=["GET"])
def emergency(health_id):
    patient = Patient.query.filter_by(health_id=health_id).first()
    if not patient:
        return jsonify({"error":"Patient not found"}), 404
    
    # Get recent reports for AI context
    recent_reports = Report.query.filter_by(patient_id=patient.id).order_by(Report.date.desc()).limit(3).all()
    
    # Build comprehensive text for AI summary
    medical_context = f"""
    Patient: {patient.name}
    Blood Group: {patient.blood_group}
    Allergies: {patient.allergies}
    Current Medications: {patient.current_medications}
    Conditions: {patient.conditions}
    
    Recent Medical Data:
    """
    
    for report in recent_reports:
        medical_context += f"{report.title}: {report.value} ({report.date}), "
    
    # Generate AI summary
    ai_summary = generate_summary(medical_context)
    
    return jsonify({
        "ABHA id": patient.health_id,
        "name": patient.name,
        "blood_group": patient.blood_group,
        "allergies": patient.allergies,
        "emergency_contact": patient.emergency_contact,
        "current_medications": patient.current_medications,
        "conditions": patient.conditions,
        "ai_summary": ai_summary
    })

@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    # Accept both parameter names that might be sent
    health_id = data.get("health_id") or data.get("ABHA id")
    password = data.get("password")
    
    patient = Patient.query.filter_by(health_id=health_id).first()
    if patient and password == "test":  # Demo password
        token = str(uuid.uuid4())
        return jsonify({
            "status": "success",
            "token": token,
            "patient_name": patient.name
        })
    
    return jsonify({"status": "failed", "message": "Invalid credentials"}), 401

@app.route("/records/<health_id>", methods=["GET"])
def records(health_id):
    patient = Patient.query.filter_by(health_id=health_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    reports = Report.query.filter_by(patient_id=patient.id).order_by(Report.date.desc()).all()
    
    reports_data = []
    for report in reports:
        reports_data.append({
            "id": report.id,
            "section": report.section,
            "title": report.title,
            "value": report.value,
            "date": report.date
        })
    
    return jsonify({
        "ABHA id": health_id,
        "patient_name": patient.name,
        "reports": reports_data
    })

# ---- QR Code Scanning Routes ----
@app.route("/api/scan-qr", methods=["POST"])
def scan_qr_code():
    """Process scanned QR code data and extract ABHA ID"""
    try:
        data = request.json or {}
        qr_data = data.get('qr_data', '').strip()
        
        if not qr_data:
            return jsonify({"status": "error", "message": "No QR data provided"}), 400
        
        # Extract ABHA ID from QR data
        health_id = extract_abha_id(qr_data)
        
        if not health_id:
            return jsonify({
                "status": "error", 
                "message": "No valid ABHA ID found in QR code. Please ensure the QR code contains a 14-digit ABHA number in format XXXX-XXXX-XXXX-XX or XXXXXXXXXXXXXX",
                "qr_data_received": qr_data
            }), 400
        
        # Verify the patient exists
        patient = Patient.query.filter_by(health_id=health_id).first()
        if not patient:
            return jsonify({
                "status": "error", 
                "message": "Patient not found with this ABHA ID",
                "health_id": health_id
            }), 404
        
        # Return success with patient info
        return jsonify({
            "status": "success",
            "message": "ABHA ID successfully extracted from QR code",
            "health_id": health_id,
            "patient_name": patient.name,
            "qr_data_received": qr_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error processing QR code: {str(e)}"
        }), 500

@app.route("/api/qr-login", methods=["POST"])
def qr_code_login():
    """Authenticate using QR code containing ABHA ID"""
    try:
        data = request.json or {}
        qr_data = data.get('qr_data', '').strip()
        
        if not qr_data:
            return jsonify({"status": "error", "message": "No QR data provided"}), 400
        
        # Extract ABHA ID from QR data
        health_id = extract_abha_id(qr_data)
        
        if not health_id:
            return jsonify({
                "status": "error", 
                "message": "No valid ABHA ID found in QR code"
            }), 400
        
        # Process the login
        patient = Patient.query.filter_by(health_id=health_id).first()
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
        
        # Generate login token
        token = str(uuid.uuid4())
        
        return jsonify({
            "status": "success",
            "token": token,
            "patient_name": patient.name,
            "health_id": health_id,
            "message": "QR login successful"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Login failed: {str(e)}"
        }), 500

@app.route("/api/generate-test-qr/<health_id>")
def generate_test_qr(health_id):
    """Generate test QR code data for a patient (for demo purposes)"""
    patient = Patient.query.filter_by(health_id=health_id).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Create multiple QR format options for testing
    qr_formats = {
        "14_digit": health_id.replace("-", ""),
        "standard_format": health_id,
        "text_format": f"ABHA ID: {health_id} | Name: {patient.name}",
        "medical_format": f"Patient: {patient.name} | ABHA: {health_id} | Blood Group: {patient.blood_group}"
    }
    
    return jsonify({
        "patient_name": patient.name,
        "health_id": health_id,
        "qr_formats": qr_formats,
        "message": "Use any of these formats in your QR code for testing"
    })

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json or {}
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    summary = generate_summary(text)
    return jsonify({"summary": summary})

@app.route("/debug")
def debug_info():
    debug_data = {
        "static_folder_path": app.static_folder,
        "static_folder_exists": os.path.exists(app.static_folder),
        "index_html_exists": os.path.exists(os.path.join(app.static_folder, "index.html")),
        "current_working_dir": os.getcwd(),
        "files_in_static_folder": os.listdir(app.static_folder) if os.path.exists(app.static_folder) else "FOLDER NOT FOUND"
    }
    return jsonify(debug_data)

@app.route('/logo.jpg')
def serve_logo():
    # Try multiple possible locations for the logo
    possible_paths = [
        os.path.join(BASE_DIR, 'logo.jpg'),
        os.path.join(BASE_DIR, 'static', 'images', 'logo.jpg'),
        os.path.join(BASE_DIR, 'frontend', 'logo.jpg'),
        os.path.join(BASE_DIR, '..', 'logo.jpg')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return send_from_directory(os.path.dirname(path), os.path.basename(path))
    
    # Return a default image if none found
    return send_from_directory(BASE_DIR, 'image.jpg')

@app.route("/test")
def test_route():
    """Simple test endpoint to check if server is working"""
    return jsonify({
        "status": "success", 
        "message": "Server is running!",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)