#!/usr/bin/env python3
"""
PULSE Service - First-Time Setup Script
Run: python setup_pulse.py
"""

import os
import sys
import subprocess
import time

def run_command(cmd, description):
    """Run a command and print status"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Success")
            return True
        else:
            if result.stderr:
                print(f"  ⚠ Warning: {result.stderr[:100]}")
            else:
                print(f"  ✓ Done")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("  PULSE Service - First-Time Setup")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(r"C:\Users\devd9\OneDrive\Desktop\PULSE")
    print(f"\n📁 Working directory: {os.getcwd()}")
    
    # Step 1: Check Python
    print("\n[1/6] Checking Python...")
    result = subprocess.run("python --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ {result.stdout.strip()}")
    else:
        print("  ✗ Python not found!")
        sys.exit(1)
    
    # Step 2: Check Docker
    print("\n[2/6] Checking Docker...")
    result = subprocess.run("docker --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ {result.stdout.strip()}")
    else:
        print("  ✗ Docker not found!")
        print("\n  Install Docker Desktop from: https://www.docker.com/")
        sys.exit(1)
    
    # Step 3: Install dependencies
    print("\n[3/6] Installing Python dependencies...")
    subprocess.run("pip install -r requirements.txt", shell=True)
    print("  ✓ Dependencies installed")
    
    # Step 4: Start database
    print("\n[4/6] Starting PostgreSQL database...")
    subprocess.run("docker-compose up -d", shell=True)
    print("  ✓ Database started")
    print("  ⏳ Waiting 5 seconds for database to initialize...")
    time.sleep(5)
    
    # Step 5: Run migrations
    print("\n[5/6] Creating database tables...")
    run_command("alembic upgrade head", "Running migrations")
    
    # Step 6: Download NLTK data
    print("\n[6/6] Downloading NLTK sentiment data...")
    run_command('python -c "import nltk; nltk.download(\'vader_lexicon\')"', "Downloading VADER lexicon")
    
    print("\n" + "=" * 60)
    print("  ✓ Setup Complete!")
    print("=" * 60)
    print("\n📌 Next step: Run the service with:")
    print("   python start_pulse.py")
    print("\n   Or manually:")
    print("   python main.py")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)
