import os
import sys
import subprocess
import time
import webbrowser
import signal
import atexit

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import flask
        import flask_cors
        import flask_sqlalchemy
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        print("Failed to install dependencies. Please install manually:")
        print("pip install flask flask-cors flask-sqlalchemy")
        return False

def main():
    """Main launcher function"""
    print("=" * 50)
    print("       HEALTH LINK CARE - Starting")
    print("=" * 50)
    
    # Check and install dependencies if needed
    if not check_dependencies():
        print("Dependencies missing. Installing...")
        if not install_dependencies():
            print("Failed to install dependencies. Exiting.")
            input("Press Enter to exit...")
            return
    
    # Start the Flask server
    print("Starting server...")
    try:
        # Start the Flask app
        flask_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        input("Press Enter to exit...")
        return
    
    # Function to cleanup on exit
    def cleanup():
        print("Stopping server...")
        flask_process.terminate()
        flask_process.wait()
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(4)
    
    # Open browser
    print("Opening browser...")
    webbrowser.open("http://localhost:5000")
    
    print("\n" + "=" * 50)
    print("✅ Health Link Care is now running!")
    print("🌐 Open: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Wait for the process to complete
        flask_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup()

if __name__ == "__main__":
    main()