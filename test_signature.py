import os
import fitz  # PyMuPDF for PDF handling
import cv2
import numpy as np
from PIL import Image
import tempfile

def crop_png_signature(input_path, output_path):
    """
    Crop a PNG image based on fixed coordinates where the signature is located.
    """
    try:
        # Open the image
        image = Image.open(input_path)

        # Define crop box (left, upper, right, lower) - using your provided coordinates
        top_left_corner = (240, 210)
        bottom_right_corner = (345, 250)
        crop_box = (top_left_corner[0], top_left_corner[1], 
                    bottom_right_corner[0], bottom_right_corner[1])

        # Crop the image
        cropped_image = image.crop(crop_box)

        # Save the cropped image
        cropped_image.save(output_path)
        print(f"PNG signature cropped and saved to {output_path}")
        return True
    
    except Exception as e:
        print(f"Error cropping PNG: {e}")
        return False

def extract_signature_from_pdf(pdf_path, output_signature_path):
    """
    Extract signature from a PDF file.
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        if len(doc) == 0:
            print("Error: PDF has no pages")
            return False
        
        # Get the first page
        page = doc[0]
        
        # Create a temporary file for the intermediate PNG
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            temp_png_path = tmp_file.name
        
        try:
            # Render page to an image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Save as temporary PNG
            pix.save(temp_png_path)
            
            # Extract signature from the temporary PNG
            result = extract_signature_from_png_cv(temp_png_path, output_signature_path)
            
            # Remove the temporary file
            os.unlink(temp_png_path)
            
            return result
            
        except Exception as e:
            # Clean up the temporary file if an error occurs
            if os.path.exists(temp_png_path):
                os.unlink(temp_png_path)
            raise e
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return False

def extract_signature_from_png_cv(png_path, output_path):
    """
    Extract signature from a PNG image using image processing techniques.
    This uses contour detection to identify the signature area.
    """
    # Read the image
    image = cv2.imread(png_path)
    if image is None:
        print(f"Error: Could not open or find the image: {png_path}")
        return False
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No signature contours found.")
        return False
    
    # Find the largest contour (assuming it's the signature)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Add some padding
    padding = 10
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)
    
    # Crop the signature
    signature = image[y:y+h, x:x+w]
    
    # Save the cropped signature
    cv2.imwrite(output_path, signature)
    print(f"PDF signature extracted and saved to {output_path}")
    return True

def main():
    # Set the input files
    png_path = "image.png"
    pdf_path = "account.pdf"
    
    # Create output directory
    output_dir = "extracted_signatures"
    os.makedirs(output_dir, exist_ok=True)
    
    # Output file paths
    png_signature_path = os.path.join(output_dir, "signature_from_png.png")
    pdf_signature_path = os.path.join(output_dir, "signature_from_pdf.png")
    
    # Process PNG using fixed coordinate cropping
    print(f"Processing PNG file: {png_path}")
    crop_png_signature(png_path, png_signature_path)
    
    # Process PDF using automatic signature detection
    print(f"Processing PDF file: {pdf_path}")
    extract_signature_from_pdf(pdf_path, pdf_signature_path)
    
    # print("Done! Extracted signatures saved in the 'extracted_signatures' folder")

    ###################################################################################
    # Add - Ask OpenAI API to give in a scale from 1 to 100 how similar the images are and if above a threshold we accept it.
    ###################################################################################

if __name__ == "__main__":
    main()