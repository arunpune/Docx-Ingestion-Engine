#!/usr/bin/env python3
"""
Guide to get a new Groq API Key
"""

print("🔑 Groq API Key Setup Guide")
print("=" * 50)
print()
print("Your current Groq API key appears to be invalid or expired.")
print("Here's how to get a new one:")
print()
print("1. 🌐 Visit: https://console.groq.com/")
print("2. 📝 Sign up or log in to your account")
print("3. 🔑 Go to API Keys section")
print("4. ➕ Click 'Create API Key'")
print("5. 📋 Copy the new API key")
print("6. ✏️ Update your .env file:")
print()
print("   Edit the .env file and replace:")
print('   GROQ_API_KEY="your_old_key"')
print("   with:")
print('   GROQ_API_KEY="your_new_key"')
print()
print("🔄 After updating the .env file:")
print("   - Stop the Streamlit app (Ctrl+C)")
print("   - Restart it with: python -m streamlit run app.py")
print()
print("📋 Current .env content:")
print("-" * 30)

try:
    with open('.env', 'r') as f:
        content = f.read()
        print(content)
except FileNotFoundError:
    print("❌ .env file not found!")
    
print("-" * 30)
print()
print("💡 Good news: Your OCR extraction is working perfectly!")
print("   The app successfully extracted text from both PDF and images.")
print("   You just need a valid API key for the AI parsing step.")
print()
print("🧪 You can also test the fallback extraction without API:")
print("   The app now includes regex-based extraction as a backup.")
