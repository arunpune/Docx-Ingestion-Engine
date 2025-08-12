"""
Invoice Reader Backend Module

This module provides OCR and AI-powered invoice processing capabilities.
It combines multiple technologies to extract structured data from invoice documents:

1. PDF Text Extraction: Direct text extraction from searchable PDFs
2. OCR Processing: EasyOCR for scanned documents and images  
3. AI Processing: Groq LLaMA model for intelligent data extraction
4. Data Structuring: Converts unstructured text to structured JSON/CSV

Key Features:
- Handles both PDF and image formats (JPG, PNG)
- Automatic fallback from text extraction to OCR
- AI-powered field recognition and extraction
- Structured output in pandas DataFrame format
- Comprehensive error handling and logging

Technologies Used:
- EasyOCR: Optical Character Recognition
- PyPDF: PDF text extraction
- pdf2image: PDF to image conversion
- OpenCV: Image processing
- LangChain + Groq: AI model integration
- Pandas: Data structuring
"""

# Import required libraries for document processing
import easyocr      # OCR (Optical Character Recognition) library
import numpy as np  # Numerical operations for image processing
import cv2          # Computer vision library for image operations
import re           # Regular expressions for text processing
import json         # JSON data handling
import pandas as pd # Data manipulation and analysis
from pypdf import PdfReader  # PDF reading and text extraction
from io import BytesIO       # Byte stream operations
from dotenv import load_dotenv  # Environment variable loading
from langchain_groq import ChatGroq  # Groq AI model integration
import os           # Operating system interface
from pdf2image import convert_from_bytes  # PDF to image conversion
from logging_config import logger  # Logging configuration

# Configure Poppler (required for PDF to image conversion)
# Poppler is a PDF rendering library needed by pdf2image
POPPLER_PATH = r"T:\github\Docx-Ingestion-Engine\invoice_reader\poppler\poppler-23.01.0\Library\bin"
os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")

# Load environment variables from .env file
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

# Validate that required API key is available
if not groq_api_key:
    logger.critical("GROQ_API_KEY is not set. Please check your .env file.")
    raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")

# Initialize the AI model for invoice processing
llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")
logger.info("Initialized Groq model.")

# Initialize EasyOCR reader for English text recognition
reader = easyocr.Reader(['en'])  # EasyOCR for OCR fallback

def get_pdf_text_with_ocr(pdf_doc):
    """
    Extract text from a PDF document with intelligent fallback to OCR.
    
    This function first attempts direct text extraction from the PDF.
    If the PDF contains scanned images or has minimal text, it falls back
    to OCR processing for better text recognition.
    
    Args:
        pdf_doc (bytes): PDF document as byte data
        
    Returns:
        str: Extracted text from the PDF document
    """
    text = ""
    try:
        logger.info("Starting PDF text extraction.")
        
        # First attempt: Direct text extraction from searchable PDFs
        pdf_reader = PdfReader(BytesIO(pdf_doc))
        logger.info(f"PDF has {len(pdf_reader.pages)} pages")
        
        # Process each page for text extraction
        for i, page in enumerate(pdf_reader.pages):
            logger.info(f"Processing page {i+1}")
            page_text = page.extract_text()
            
            # Check if meaningful text was extracted
            if page_text and page_text.strip():
                text += page_text + "\n"
                logger.info(f"Extracted {len(page_text)} characters from page {i+1}")
            else:
                logger.info(f"No text found on page {i+1}, will use OCR")
        
        if text.strip():
            logger.info(f"PDF text extraction completed. Total characters: {len(text)}")
            logger.debug(f"Extracted text preview: {text[:200]}...")
            return text
        else:
            logger.info("No text extracted via direct method, proceeding to OCR")
            
    except Exception as e:
        logger.warning(f"Text extraction from PDF failed: {e}")

    # If text extraction fails or returns empty, use OCR
    try:
        logger.info("Starting OCR fallback for scanned PDF.")
        
        # Convert PDF to images using Poppler
        pdf_images = convert_from_bytes(
            pdf_doc, 
            poppler_path=POPPLER_PATH,
            dpi=300,  # Higher DPI for better OCR accuracy
            fmt='RGB'
        )
        logger.info(f"Converted PDF to {len(pdf_images)} images")
        
        for i, img in enumerate(pdf_images):
            logger.info(f"Running OCR on page {i+1}")
            
            # Convert PIL image to numpy array for EasyOCR
            img_array = np.array(img)
            
            # Preprocess image for better OCR results
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply some image preprocessing for better OCR
            # Increase contrast
            img_enhanced = cv2.convertScaleAbs(img_gray, alpha=1.2, beta=10)
            
            # Reduce noise
            img_denoised = cv2.medianBlur(img_enhanced, 3)
            
            # Run OCR
            ocr_result = reader.readtext(img_denoised, detail=0)  # detail=0 returns only text
            page_text = "\n".join(ocr_result)
            
            if page_text.strip():
                text += page_text + "\n"
                logger.info(f"OCR extracted {len(page_text)} characters from page {i+1}")
            else:
                logger.warning(f"No text extracted via OCR from page {i+1}")
        
        if text.strip():
            logger.info(f"OCR extraction completed. Total characters: {len(text)}")
            logger.debug(f"OCR text preview: {text[:200]}...")
        else:
            logger.error("No text extracted via OCR either")
            
    except Exception as e:
        logger.error(f"OCR fallback failed: {e}")
        
    return text

def process_image(image_file):
    """Process an image file to extract text using OCR."""
    try:
        logger.info(f"Processing image file: {image_file.name}")
        
        # Read image file
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Failed to decode image")
            return None
        
        logger.info(f"Image dimensions: {image.shape}")
        
        # Preprocess image for better OCR results
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Increase contrast and brightness
        enhanced = cv2.convertScaleAbs(denoised, alpha=1.2, beta=10)
        
        # Apply adaptive thresholding for better text extraction
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Perform OCR with multiple approaches
        logger.info("Running OCR on processed image...")
        
        # Method 1: Direct OCR on enhanced image
        result1 = reader.readtext(enhanced, detail=0)
        text1 = "\n".join(result1) if result1 else ""
        
        # Method 2: OCR on thresholded image
        result2 = reader.readtext(thresh, detail=0)
        text2 = "\n".join(result2) if result2 else ""
        
        # Method 3: OCR on original image (fallback)
        result3 = reader.readtext(image, detail=0)
        text3 = "\n".join(result3) if result3 else ""
        
        # Choose the result with most text
        texts = [text1, text2, text3]
        raw_text = max(texts, key=len) if any(texts) else ""
        
        logger.info(f"OCR extracted {len(raw_text)} characters")
        logger.debug(f"OCR Raw Text Output:\n{raw_text[:200]}...")
        
        if not raw_text.strip():
            logger.warning("No text extracted from image")
            
        return raw_text
        
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        return None

def extracted_data(raw_text):
    """Extract structured data from raw text using Groq API."""
    if not raw_text or not raw_text.strip():
        logger.warning("No text provided for extraction")
        return None
    
    logger.info(f"Extracting data from {len(raw_text)} characters of text")
    
    template = """
    You are an expert data extraction assistant. Extract the following information from this invoice/document text.

    Text to analyze:
    {raw_text}

    Extract these fields and return ONLY a valid JSON object:
    - Invoice no. (invoice number, reference number, or similar)
    - Description (item description, service description)
    - Quantity (qty, amount, units)
    - Date (invoice date, billing date, due date)
    - Unit price (price per unit, rate)
    - Amount (line total, subtotal)
    - Total (grand total, final amount, total due)
    - Email (email address of vendor/customer)
    - Phone number (phone, mobile, contact number)
    - Address (billing address, vendor address)

    Important rules:
    1. If a field is not found, use 'N/A'
    2. Remove any currency symbols ($ € £ etc.)
    3. For numeric values, keep only numbers and decimal points
    4. Return ONLY valid JSON format
    5. Use double quotes for JSON keys and values

    Expected JSON format:
    {{
        "Invoice no.": "value_or_N/A",
        "Description": "value_or_N/A",
        "Quantity": "value_or_N/A",
        "Date": "value_or_N/A",
        "Unit price": "value_or_N/A",
        "Amount": "value_or_N/A",
        "Total": "value_or_N/A",
        "Email": "value_or_N/A",
        "Phone number": "value_or_N/A",
        "Address": "value_or_N/A"
    }}
    """
    
    prompt = template.format(raw_text=raw_text[:4000])  # Limit text length for API
    
    try:
        logger.info("Sending data to Groq API for extraction.")
        response = llm.predict(text=prompt, temperature=0.1)
        logger.debug(f"Groq API Response: {response}")

        if not response:
            raise ValueError("No response from Groq API")

        # Clean up the response to extract JSON
        response_clean = response.strip()
        
        # Try to find JSON content between curly braces
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, response_clean, re.DOTALL)
        
        if json_matches:
            # Take the first (and hopefully only) JSON match
            json_data = json_matches[0]
            
            # Validate JSON by parsing it
            try:
                parsed_data = json.loads(json_data)
                logger.info("Successfully parsed JSON response")
                return json_data
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed, trying to fix: {e}")
                
                # Try to fix common JSON issues
                fixed_json = json_data.replace("'", '"')  # Replace single quotes
                fixed_json = re.sub(r',\s*}', '}', fixed_json)  # Remove trailing commas
                fixed_json = re.sub(r',\s*]', ']', fixed_json)  # Remove trailing commas in arrays
                
                try:
                    parsed_data = json.loads(fixed_json)
                    logger.info("Successfully parsed fixed JSON response")
                    return fixed_json
                except json.JSONDecodeError:
                    logger.error("Could not fix JSON format")
                    return None
        else:
            logger.error("No valid JSON content found in Groq API response")
            logger.debug(f"Full response: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Error during data extraction: {e}", exc_info=True)
        
        # Fallback: Simple regex-based extraction when API fails
        logger.info("Attempting fallback regex extraction...")
        return fallback_extraction(raw_text)

def fallback_extraction(raw_text):
    """Fallback extraction using regex patterns when Groq API fails"""
    logger.info("Using fallback regex-based extraction")
    
    # Basic regex patterns for common invoice fields
    patterns = {
        'Invoice no.': [
            r'(?:invoice|inv)[\s#:]*([A-Z0-9-]+)',
            r'(?:number|no)[\s#:]*([A-Z0-9-]+)',
            r'#([A-Z0-9-]+)'
        ],
        'Date': [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\w+ \d{1,2}, \d{4})'
        ],
        'Total': [
            r'(?:total|amount due)[\s:$]*(\d+\.?\d*)',
            r'\$(\d+\.?\d*)',
            r'(\d+\.\d{2})\s*$'
        ],
        'Email': [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ],
        'Phone number': [
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'\((\d{3})\)\s*(\d{3}[-.\s]?\d{4})'
        ]
    }
    
    extracted = {
        'Invoice no.': 'N/A',
        'Description': 'N/A',
        'Quantity': 'N/A', 
        'Date': 'N/A',
        'Unit price': 'N/A',
        'Amount': 'N/A',
        'Total': 'N/A',
        'Email': 'N/A',
        'Phone number': 'N/A',
        'Address': 'N/A'
    }
    
    # Convert to lowercase for better matching
    text_lower = raw_text.lower()
    
    # Extract fields using regex
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted[field] = match.group(1) if match.lastindex else match.group(0)
                break
    
    # Extract description (usually the longest text block)
    lines = raw_text.split('\n')
    longest_line = max(lines, key=len) if lines else 'N/A'
    if len(longest_line) > 20:  # Only if it's substantial
        extracted['Description'] = longest_line.strip()
    
    logger.info(f"Fallback extraction completed: {extracted}")
    return json.dumps(extracted)

def create_docs(user_file_list):
    """Process the list of uploaded files (PDFs or images) and extract structured data."""
    df = pd.DataFrame(columns=['Invoice no.', 'Description', 'Quantity', 'Date', 
                               'Unit price', 'Amount', 'Total', 'Email', 'Phone number', 'Address'])

    if not user_file_list:
        logger.warning("No files provided for processing")
        return df

    logger.info(f"Processing {len(user_file_list)} files")

    for uploaded_file in user_file_list:
        logger.info(f"Processing file: {uploaded_file.name}")
        file_type = uploaded_file.type
        logger.info(f"File type: {file_type}")

        raw_data = None

        if file_type == "application/pdf":
            logger.info("Processing as PDF file")
            file_content = uploaded_file.read()
            logger.info(f"PDF file size: {len(file_content)} bytes")
            raw_data = get_pdf_text_with_ocr(file_content)
        elif file_type in ["image/jpeg", "image/png", "image/jpg"]:
            logger.info("Processing as image file")
            raw_data = process_image(uploaded_file)
        else:
            logger.warning(f"Unsupported file type: {uploaded_file.name} ({file_type})")
            continue

        if raw_data and raw_data.strip():
            logger.info(f"Extracted {len(raw_data)} characters of text from {uploaded_file.name}")
            logger.debug(f"Raw text preview: {raw_data[:300]}...")
            
            llm_extracted_data = extracted_data(raw_data)
            if llm_extracted_data:
                try:
                    logger.info("Parsing extracted JSON data")
                    # Clean the JSON string
                    cleaned_data = llm_extracted_data.replace("'", '"')
                    data_dict = json.loads(cleaned_data)
                    logger.info(f"Successfully parsed data: {list(data_dict.keys())}")
                    logger.debug(f"Parsed Data Dict: {data_dict}")

                    # Handle multiple line items if present
                    if isinstance(data_dict.get('Description'), str) and '\n' in data_dict['Description']:
                        logger.info("Processing multiple line items")
                        descriptions = data_dict['Description'].split('\n')
                        quantities = data_dict.get('Quantity', 'N/A').split('\n') if isinstance(data_dict.get('Quantity'), str) else ['N/A'] * len(descriptions)
                        unit_prices = data_dict.get('Unit price', 'N/A').split('\n') if isinstance(data_dict.get('Unit price'), str) else ['N/A'] * len(descriptions)
                        amounts = data_dict.get('Amount', 'N/A').split('\n') if isinstance(data_dict.get('Amount'), str) else ['N/A'] * len(descriptions)

                        for desc, qty, unit_price, amt in zip(descriptions, quantities, unit_prices, amounts):
                            row = {
                                'Invoice no.': data_dict.get('Invoice no.', 'N/A'),
                                'Description': desc.strip(),
                                'Quantity': qty.strip(),
                                'Date': data_dict.get('Date', 'N/A'),
                                'Unit price': unit_price.strip(),
                                'Amount': amt.strip(),
                                'Total': data_dict.get('Total', 'N/A'),
                                'Email': data_dict.get('Email', 'N/A'),
                                'Phone number': data_dict.get('Phone number', 'N/A'),
                                'Address': data_dict.get('Address', 'N/A')
                            }
                            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                            logger.debug(f"Added row: {row}")
                    else:
                        logger.info("Processing single line item")
                        # Ensure all required keys exist
                        row = {
                            'Invoice no.': data_dict.get('Invoice no.', 'N/A'),
                            'Description': data_dict.get('Description', 'N/A'),
                            'Quantity': data_dict.get('Quantity', 'N/A'),
                            'Date': data_dict.get('Date', 'N/A'),
                            'Unit price': data_dict.get('Unit price', 'N/A'),
                            'Amount': data_dict.get('Amount', 'N/A'),
                            'Total': data_dict.get('Total', 'N/A'),
                            'Email': data_dict.get('Email', 'N/A'),
                            'Phone number': data_dict.get('Phone number', 'N/A'),
                            'Address': data_dict.get('Address', 'N/A')
                        }
                        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                        logger.debug(f"Added row: {row}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from {uploaded_file.name}: {e}")
                    logger.debug(f"Problematic JSON: {llm_extracted_data}")
                except Exception as e:
                    logger.error(f"Unexpected error during parsing {uploaded_file.name}: {e}", exc_info=True)
            else:
                logger.warning(f"No data extracted from LLM for file: {uploaded_file.name}")
        else:
            logger.warning(f"No text extracted from file: {uploaded_file.name}")
    
    logger.info(f"Data extraction process completed. Processed {len(df)} records.")
    return df
