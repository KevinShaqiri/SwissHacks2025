# Document Verification System

A web application that allows users to upload verification documents and displays an accept/reject result.

## Features

- Upload interface for four required document types:
  - Passport (PNG format)
  - Client Profile (DOCX format) 
  - Account Opening Form (PDF format)
  - Client Description (TXT format)
- Validation of file types
- Display of acceptance or rejection result
- Modern, responsive UI

## Setup Instructions

1. Make sure you have Python installed (3.7+ recommended)

2. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

3. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and go to:
   ```
   http://127.0.0.1:5000/
   ```

## Implementation Notes

- Currently the acceptance/rejection is randomly determined. This placeholder can be replaced with actual verification logic.
- To implement your own verification logic, modify the code in the `upload_files` function in `app.py`.

## Future Enhancements

- Add user authentication
- Implement actual document verification
- Add database storage for uploaded documents
- Create an admin dashboard for document management 