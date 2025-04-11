from flask import Flask, render_template, request, redirect, url_for, flash
import os
import random
import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        # Check if all required files are present
        required_files = {
            'passport': ['png'],
            'profile': ['docx'],
            'account_form': ['pdf'],
            'description': ['txt']
        }
        
        uploaded_files = {}
        
        # Process each file upload
        for file_type, extensions in required_files.items():
            if file_type not in request.files:
                flash(f'No {file_type} file part')
                return redirect(url_for('index'))
            
            file = request.files[file_type]
            if file.filename == '':
                flash(f'No {file_type} file selected')
                return redirect(url_for('index'))
            
            if file and '.' in file.filename:
                extension = file.filename.rsplit('.', 1)[1].lower()
                if extension in extensions:
                    filename = f"{file_type}.{extension}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    uploaded_files[file_type] = file_path
                else:
                    flash(f'Invalid file type for {file_type}. Expected: {", ".join(extensions)}')
                    return redirect(url_for('index'))
        
        # Verify all files were uploaded
        if len(uploaded_files) == len(required_files):
            result = "Accept" if random.choice([True, False]) else "Reject"
            return render_template('result.html', result=result)
        else:
            flash('Not all required files were uploaded correctly')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 