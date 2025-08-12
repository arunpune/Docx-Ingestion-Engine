#!/usr/bin/env python3
"""
Invoice Reader Test Utility

This script tests the OCR and AI processing capabilities.
Run this to verify your invoice processing setup is working correctly.
"""

import os
import sys
from pathlib import Path

# Add path for imports
sys.path.append(os.path.dirname(__file__))

def test_environment():
    """Test if all required environment variables and dependencies are set up"""
    
    print("🔍 Testing Invoice Processing Environment...")
    print("=" * 50)
    
    # Check if .env file exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_path):
        print("❌ Error: .env file not found!")
        print(f"   Expected location: {os.path.abspath(env_path)}")
        print("\n📋 To fix this:")
        print("1. Create a .env file in the invoice_reader/ folder")
        print("2. Add your Groq API key: GROQ_API_KEY=your_key_here")
        print("3. Get your key from: https://console.groq.com/keys")
        return False
    
    print("✅ .env file found")
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY not found in .env file")
        print("\n📋 To fix this:")
        print("1. Open the .env file")
        print("2. Add: GROQ_API_KEY=your_actual_key_here")
        print("3. Get your key from: https://console.groq.com/keys")
        return False
    
    if not groq_api_key.startswith('gsk_'):
        print("⚠️  Warning: GROQ_API_KEY doesn't look like a typical Groq key")
        print("   Groq keys usually start with 'gsk_'")
        print("   Continuing with provided key...")
    
    print(f"✅ GROQ_API_KEY found: {groq_api_key[:10]}...{groq_api_key[-4:]}")
    
    return True

def test_dependencies():
    """Test if all required Python packages are installed"""
    
    print("\n🔍 Testing Python Dependencies...")
    print("=" * 40)
    
    required_packages = [
        ('easyocr', 'EasyOCR for text recognition'),
        ('cv2', 'OpenCV for image processing'),
        ('pandas', 'Pandas for data manipulation'),
        ('pypdf', 'PyPDF for PDF processing'),
        ('pdf2image', 'PDF2Image for PDF conversion'),
        ('langchain_groq', 'LangChain Groq for AI processing'),
        ('numpy', 'NumPy for numerical operations'),
        ('PIL', 'Pillow for image operations'),
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("\n📋 To fix this, run:")
        print("pip install -r requirements.txt")
        return False
    
    print("\n✅ All required packages are installed")
    return True

def test_poppler():
    """Test if Poppler is properly installed for PDF processing"""
    
    print("\n🔍 Testing Poppler Installation...")
    print("=" * 40)
    
    try:
        from pdf2image import convert_from_bytes
        
        # Create a minimal test PDF in memory
        test_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000120 00000 n 
0000000200 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        # Try to convert the test PDF
        images = convert_from_bytes(test_pdf_content)
        
        if images:
            print("✅ Poppler is working correctly")
            print(f"✅ Successfully converted test PDF to {len(images)} image(s)")
            return True
        else:
            print("❌ Poppler conversion returned no images")
            return False
            
    except Exception as e:
        print(f"❌ Poppler test failed: {e}")
        print("\n📋 To fix Poppler installation:")
        print("\nWindows:")
        print("1. Download: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract to: invoice_reader/poppler/")
        print("\nmacOS:")
        print("brew install poppler")
        print("\nLinux (Ubuntu/Debian):")
        print("sudo apt-get install poppler-utils")
        return False

def test_groq_connection():
    """Test connection to Groq AI service"""
    
    print("\n🔍 Testing Groq AI Connection...")
    print("=" * 40)
    
    try:
        from langchain_groq import ChatGroq
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")
        
        # Test with a simple prompt
        test_prompt = "Reply with exactly: 'Test successful'"
        response = llm.invoke(test_prompt)
        
        if response and hasattr(response, 'content'):
            print("✅ Groq AI connection successful")
            print(f"✅ Model response: {response.content[:50]}...")
            return True
        else:
            print("❌ Groq AI returned unexpected response format")
            return False
            
    except Exception as e:
        print(f"❌ Groq AI test failed: {e}")
        print("\n📋 To fix this:")
        print("1. Verify your Groq API key is correct")
        print("2. Check your internet connection")
        print("3. Visit: https://console.groq.com/keys to get a new key")
        print("4. Ensure you have API credits available")
        return False

def test_ocr():
    """Test OCR functionality with EasyOCR"""
    
    print("\n🔍 Testing OCR Functionality...")
    print("=" * 40)
    
    try:
        import easyocr
        import numpy as np
        
        # Initialize EasyOCR reader
        reader = easyocr.Reader(['en'])
        
        # Create a simple test image with text
        # This creates a white image with black text
        import cv2
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # White background
        cv2.putText(img, 'Test Invoice 123', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Perform OCR
        results = reader.readtext(img)
        
        if results:
            detected_text = ' '.join([result[1] for result in results])
            print("✅ OCR is working correctly")
            print(f"✅ Detected text: '{detected_text}'")
            return True
        else:
            print("❌ OCR didn't detect any text in test image")
            return False
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        print("\n📋 This might be a temporary issue with:")
        print("1. EasyOCR model download (first run)")
        print("2. System dependencies")
        print("3. Try running the test again")
        return False

def main():
    """Run all tests"""
    
    print("🧪 Invoice Reader Test Suite")
    print("=" * 60)
    print("This will test all components needed for invoice processing\n")
    
    tests = [
        ("Environment Setup", test_environment),
        ("Python Dependencies", test_dependencies),
        ("Poppler PDF Processing", test_poppler),
        ("Groq AI Connection", test_groq_connection),
        ("OCR Functionality", test_ocr),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print('='*60)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your invoice processing system is ready!")
        print("\n🚀 You can now run the main application:")
        print("   python -m streamlit run email_invoice_dashboard.py")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please fix the issues above.")
        print("\n📋 Common fixes:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Create .env file with GROQ_API_KEY")
        print("3. Install Poppler for your operating system")
        print("4. Check internet connection for API tests")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
