#!/usr/bin/env python3
"""
Setup script for healthcare data scrapers
Installs dependencies and prepares the environment
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_virtual_environment():
    """Set up or verify virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔧 Creating virtual environment...")
    success = run_command("python3 -m venv venv", "Virtual environment creation")
    
    if success:
        print("✅ Virtual environment created")
    
    return success

def install_dependencies():
    """Install Python dependencies"""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    # Check if we're in a virtual environment
    if os.environ.get('VIRTUAL_ENV'):
        pip_command = "pip install -r requirements.txt"
    else:
        pip_command = "venv/bin/pip install -r requirements.txt"
    
    return run_command(pip_command, "Installing Python dependencies")

def verify_installation():
    """Verify that installation was successful"""
    print("\n🔍 Verifying installation...")
    
    # Check if we can import key modules
    if os.environ.get('VIRTUAL_ENV'):
        python_command = "python"
    else:
        python_command = "venv/bin/python"
    
    test_command = f"{python_command} -c 'import requests, beautifulsoup4, pandas; print(\"All modules available\")'"
    
    success = run_command(test_command, "Module import test")
    
    if success:
        print("✅ Installation verification passed")
    else:
        print("❌ Installation verification failed")
    
    return success

def show_next_steps():
    """Show user what to do next"""
    print(f"\n{'='*60}")
    print("🎉 SETUP COMPLETE!")
    print(f"{'='*60}")
    print()
    print("Next steps:")
    print()
    print("1. Activate virtual environment:")
    print("   source venv/bin/activate")
    print()
    print("2. List available scrapers:")
    print("   python scraper_manager.py list")
    print()
    print("3. Run a specific scraper:")
    print("   python scraper_manager.py run hospitals")
    print()
    print("4. See all options:")
    print("   python scraper_manager.py --help")
    print()
    print("📖 Read README.md for detailed documentation")

def main():
    """Main setup process"""
    print("Healthcare Data Scrapers - Setup")
    print("=" * 40)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("⚠️  Installation may have issues, but continuing...")
    
    # Make scripts executable
    scripts = ["scraper_manager.py", "standardize_scrapers.py"]
    for script in scripts:
        if Path(script).exists():
            os.chmod(script, 0o755)
            print(f"✅ Made {script} executable")
    
    show_next_steps()

if __name__ == "__main__":
    main()