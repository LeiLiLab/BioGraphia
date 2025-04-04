"""
One-click startup script

Features:
1. Start Flask backend server
2. Start Vue frontend development server
3. Optional standalone mode with data auto-reset every 5 minutes
"""

import subprocess
import sys
import os
import time
import shutil
import argparse
from threading import Thread, Timer
import importlib.util

def check_dependencies():
    """Check if necessary Python packages are installed"""
    required_packages = ['flask', 'flask_cors']
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("Error: Missing necessary Python packages.")
        print("Please run the following command to install:")
        print("pip install " + " ".join(missing_packages))
        print("\nIf you have already installed but still see this message, please ensure you are using the correct Python environment:")
        print(f"Current Python path: {sys.executable}")
        return False
    return True

def backup_data_folder():
    """Create a backup of the data folder"""
    data_path = os.path.join('data')
    backup_path = os.path.join('data_backup')
    
    # Ensure the data folder exists
    if not os.path.exists(data_path):
        print(f"Warning: Data folder '{data_path}' does not exist. Creating it.")
        os.makedirs(data_path)
    
    # If a backup already exists, delete it first
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)
    
    # Create a backup
    print(f"Creating backup of data folder to {backup_path}")
    shutil.copytree(data_path, backup_path)
    return backup_path

def restore_data_folder(backup_path):
    """Restore data folder from backup"""
    data_path = os.path.join('data')
    
    print(f"Restoring data folder from backup {backup_path}")
    
    # Ensure the data folder exists
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
    
    # Restore from backup
    shutil.copytree(backup_path, data_path)
    print("Data folder restored successfully")

def schedule_data_reset(backup_path, interval=300):
    """Schedule periodic reset of data folder"""
    def reset_and_reschedule():
        restore_data_folder(backup_path)
        schedule_data_reset(backup_path, interval)
    
    timer = Timer(interval, reset_and_reschedule)
    timer.daemon = True
    timer.start()
    print(f"Scheduled next data reset in {interval} seconds")

def run_backend():
    """Run backend server"""
    if not check_dependencies():
        sys.exit(1)
        
    print("Starting backend server...")
    backend_path = os.path.join('src', 'server', 'app.py')
    try:
        # Use current Python interpreter to run the backend
        subprocess.run([sys.executable, backend_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Backend server start failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed: {str(e)}")
        sys.exit(1)

def run_frontend():
    """Run frontend development server"""
    print("Starting frontend server with custom port...")
    try:
        # Read frontend port from .env file
        frontend_port = None
        with open('.env', 'r') as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'VITE_FRONTEND_PORT' in line:
                        frontend_port = line.split('=')[1].strip()
                        break
        
        # If not found or read failed, use default value
        if frontend_port:
            split_port = frontend_port.split('#')[0].strip()
            frontend_port = split_port

        print(f"Using frontend port: {frontend_port}")
        
        # Use read port to start frontend service
        if sys.platform.startswith('win'):
            subprocess.run(['npx', 'quasar', 'dev', '--port', frontend_port], check=True, shell=True)
        else:
            subprocess.run(['npx', 'quasar', 'dev', '--port', frontend_port], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Frontend server start failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed: {str(e)}")
        sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Start the application')
    parser.add_argument('--standalone', action='store_true', help='Enable standalone mode with data auto-reset every 5 minutes')
    return parser.parse_args()

def main():
    """Main function: Start backend and frontend servers in parallel"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        print(f"Using Python: {sys.executable}")
        
        # Check dependencies
        if not check_dependencies():
            return
        
        # If standalone mode is enabled, backup data folder and set periodic reset
        backup_path = None
        if args.standalone:
            print("Standalone mode enabled: Data will be reset every 5 minutes")
            backup_path = backup_data_folder()
            schedule_data_reset(backup_path)

        # Create backend thread
        backend_thread = Thread(target=run_backend)
        backend_thread.daemon = True  # Set as daemon thread so it terminates when main program exits
        backend_thread.start()
        
        # Wait for backend to start
        time.sleep(2)
        
        # Start frontend (main thread)
        run_frontend()
        
    except KeyboardInterrupt:
        print("\nClosing server...")
    except Exception as e:
        print(f"Start failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 