#!/usr/bin/env python3
"""
Setup script to download and configure Poppler for Windows
"""

import os
import requests
import zipfile
import sys
from pathlib import Path

def download_poppler():
    """Download and setup Poppler for Windows"""
    print("🚀 Setting up Poppler for PDF processing...")
    
    # Create poppler directory
    poppler_dir = Path("poppler")
    poppler_dir.mkdir(exist_ok=True)
    
    # Download URL for Poppler Windows
    url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.01.0-0/Release-23.01.0-0.zip"
    zip_file = "poppler.zip"
    
    print(f"📥 Downloading Poppler from: {url}")
    
    try:
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(zip_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Download completed!")
        
        # Extract the zip file
        print("📦 Extracting Poppler...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(poppler_dir)
        
        # Find the bin directory
        bin_path = None
        for root, dirs, files in os.walk(poppler_dir):
            if 'bin' in dirs:
                bin_path = os.path.join(root, 'bin')
                break
        
        if bin_path:
            abs_bin_path = os.path.abspath(bin_path)
            print(f"✅ Poppler extracted to: {abs_bin_path}")
            
            # Update the backend.py to use this path
            update_backend_with_poppler_path(abs_bin_path)
            
            # Clean up
            os.remove(zip_file)
            print("🧹 Cleaned up temporary files")
            print("🎉 Poppler setup completed successfully!")
            print(f"📍 Poppler bin path: {abs_bin_path}")
            
        else:
            print("❌ Could not find bin directory in extracted files")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up Poppler: {str(e)}")
        return False
    
    return True

def update_backend_with_poppler_path(poppler_path):
    """Update backend.py to include the poppler path"""
    backend_file = "backend.py"
    
    if not os.path.exists(backend_file):
        print("⚠️ backend.py not found, skipping path update")
        return
    
    try:
        # Read the current backend.py
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add poppler path configuration at the top
        poppler_config = f'''
# Poppler configuration for PDF processing
import os
POPPLER_PATH = r"{poppler_path}"
os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")

'''
        
        # Check if poppler config already exists
        if "POPPLER_PATH" not in content:
            # Add the configuration after the imports
            lines = content.split('\n')
            import_end = 0
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_end = i + 1
            
            # Insert poppler config after imports
            lines.insert(import_end, poppler_config)
            content = '\n'.join(lines)
            
            # Write back to file
            with open(backend_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Updated backend.py with Poppler path")
        else:
            print("ℹ️ Poppler path already configured in backend.py")
            
    except Exception as e:
        print(f"⚠️ Could not update backend.py: {str(e)}")

if __name__ == "__main__":
    print("🔧 Poppler Setup for Invoice Reader")
    print("=" * 40)
    
    success = download_poppler()
    
    if success:
        print("\n🎉 Setup completed! You can now process PDF invoices.")
        print("💡 Restart your Streamlit app to apply changes:")
        print("   Ctrl+C to stop current app, then run: streamlit run app.py")
    else:
        print("\n❌ Setup failed. Please try manual installation:")
        print("1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract to a folder")
        print("3. Add the bin folder to your system PATH")
