#!/usr/bin/env python3
"""
Installation script for TIKTOD V3 dependencies
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")
        return False

def main():
    print("TIKTOD V3 - Installing Dependencies")
    print("=" * 40)
    
    # Read requirements from file
    requirements = []
    try:
        with open("requirements.txt", "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print("requirements.txt not found, using default packages")
        requirements = [
            "customtkinter",
            "selenium",
            "Pillow",
            "pytesseract", 
            "chromedriver-autoinstaller"
        ]
    
    print(f"Installing {len(requirements)} packages...")
    print()
    
    success_count = 0
    for package in requirements:
        if install_package(package):
            success_count += 1
    
    print()
    print("=" * 40)
    print(f"Installation complete: {success_count}/{len(requirements)} packages installed")
    
    if success_count == len(requirements):
        print("✓ All dependencies installed successfully!")
        print("\nYou can now run: python app.py")
    else:
        print("⚠ Some packages failed to install. Please check the errors above.")
        
    # Check for tesseract installation
    print("\nChecking for Tesseract OCR...")
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
        print("✓ Tesseract OCR found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Tesseract OCR not found. Please install it manually:")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("  macOS: brew install tesseract")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")

if __name__ == "__main__":
    main()
