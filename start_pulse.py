#!/usr/bin/env python3
"""
PULSE Service - Simple Startup Script
Run: python start_pulse.py
"""

import os
import sys
import subprocess
import time

def run_command(cmd, description, check=True):
    """Run a command and print status"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Success")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run("docker ps", shell=True, capture_output=True, check=True)
        return True
    except:
        return False

def main():
    print("=" * 50)
    print("  PULSE Service - Startup")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(r"C:\Users\devd9\OneDrive\Desktop\PULSE")
    print(f"\n📁 Working directory: {os.getcwd()}")
    
    # Check Docker
    print("\n[1/3] Checking Docker...")
    if not check_docker():
        print("  ✗ Docker is not running!")
        print("\n  Please start Docker Desktop and try again.")
        sys.exit(1)
    print("  ✓ Docker is running")
    
    # Start database
    print("\n[2/3] Starting PostgreSQL database...")
    
    # Check if container is already running
    result = subprocess.run(
        'docker ps --filter "name=pulse_postgres" --filter "status=running" --format "{{.Names}}"',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if "pulse_postgres" in result.stdout:
        print("  ✓ Database already running")
    else:
        subprocess.run("docker-compose up -d", shell=True)
        print("  ✓ Database started")
        print("  ⏳ Waiting 3 seconds for database to initialize...")
        time.sleep(3)
    
    # Start PULSE service
    print("\n[3/3] Starting PULSE service...")
    print("\n" + "=" * 50)
    print("  Service starting on http://localhost:8003")
    print("=" * 50)
    print("\n📖 API Docs: http://localhost:8003/docs")
    print("💚 Health:   http://localhost:8003/health")
    print("\n⚠️  Press CTRL+C to stop\n")
    
    # Start the service
    try:
        subprocess.run("python main.py", shell=True)
    except KeyboardInterrupt:
        print("\n\n✋ Service stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
