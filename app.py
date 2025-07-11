from flask import Flask, render_template, request, redirect, flash, url_for, session, Response
from datetime import timedelta
from flask import make_response
import os
import csv
import smtplib
import ssl
from email.message import EmailMessage
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from dotenv import load_dotenv
import re
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout

# Setup upload folder and allowed extensions
UPLOAD_FOLDER = 'Uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv'}  # Only CSV support for now

# Setup SQLite DB for users
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # Phone number required

# Create DB if not exists
with app.app_context():
    db.create_all()

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_email(name, to_email, subject, body, from_email):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    personalized_body = body.replace("{name}", name)
    msg.set_content(personalized_body)
    return msg

def send_welcome_emails(file_path, smtp_server, smtp_port, subject, body, email_address, email_password):
    try:
        logger.debug(f"Processing file: {file_path}")
        
        # Read CSV file
        recipients = []
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                for row in reader:
                    recipients.append(row)
        except Exception as file_error:
            logger.error(f"Failed to read file: {file_path}, error: {file_error}")
            raise ValueError(f"Failed to read file: {file_error}")

        # Validate required columns (case-insensitive)
        if not recipients:
            raise ValueError("File is empty or contains no valid data")
            
        first_row = recipients[0]
        available_columns = set(col.lower().strip() for col in first_row.keys())
        required_columns = {'name', 'email'}
        
        if not required_columns.issubset(available_columns):
            missing = required_columns - available_columns
            logger.error(f"Missing required columns: {', '.join(missing)}")
            available_cols_display = ', '.join(first_row.keys())  # Show original case
            raise ValueError(f"Missing required columns: {', '.join(missing)}. Available columns: {available_cols_display}. Note: Column names should be 'name' and 'email' (case-insensitive).")

        try:
            smtp_port_int = int(smtp_port)
        except Exception as port_error:
            logger.error(f"SMTP port is not a valid integer: {smtp_port}")
            raise ValueError(f"SMTP port is not a valid integer: {smtp_port}")

        context = ssl.create_default_context()
        emails_sent = 0
        failed_emails = 0
        
        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port_int, context=context) as server:
                logger.debug(f"Logging in to SMTP server: {smtp_server}:{smtp_port}")
                try:
                    server.login(email_address, email_password)
                    logger.info("SMTP authentication successful")
                except smtplib.SMTPAuthenticationError as auth_error:
                    logger.error(f"SMTP authentication failed: {auth_error}")
                    raise smtplib.SMTPAuthenticationError(auth_error.smtp_code, auth_error.smtp_error)
                except Exception as login_error:
                    logger.error(f"SMTP login failed: {login_error}")
                    raise login_error
                
                # Process each row in the file
                for index, row in enumerate(recipients):
                    # Handle case-insensitive column names (name, Name, NAME, email, Email, EMAIL, etc.)
                    name = None
                    email = None
                    
                    for key, value in row.items():
                        key_lower = key.lower().strip()
                        if key_lower == 'name':
                            name = str(value).strip() if value else ''
                        elif key_lower == 'email':
                            email = str(value).strip() if value else ''
                    
                    if not name or not email or email == 'nan':
                        logger.warning(f"Skipping row {index + 1}: missing name or email: name='{name}', email='{email}'")
                        failed_emails += 1
                        continue
                    
                    msg = create_email(name, email, subject, body, email_address)
                    try:
                        server.send_message(msg)
                        logger.info(f"✅ Email sent to {name} <{email}>")
                        emails_sent += 1
                    except Exception as send_error:
                        logger.error(f"❌ Failed to send email to {email}: {send_error}")
                        failed_emails += 1
                        continue  # Continue to next email on failure
            
            # Return results instead of setting flash messages here
            return {
                'success': True,
                'emails_sent': emails_sent,
                'failed_emails': failed_emails,
                'total_processed': emails_sent + failed_emails
            }
            
        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP error: {smtp_error}")
            raise smtp_error
        except Exception as smtp_general_error:
            logger.error(f"SMTP connection or sending error: {smtp_general_error}")
            raise smtp_general_error
            
    except Exception as e:
        logger.error(f"Error in send_welcome_emails: {str(e)}")
        raise e

# Validate phone number (10-12 digits, optional + country code)
def validate_phone(phone):
    pattern = r'^\+?\d{10,12}$'
    return bool(re.match(pattern, phone))

# ----------------- USER AUTH ROUTES -------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        if not email or not password or not phone:
            flash('Email, password, and phone number are required.', 'error')
            logger.debug("Registration failed: Missing required fields")
            return redirect(url_for('register'))

        # Validate phone number
        if not validate_phone(phone):
            flash('Phone number must be 10-12 digits (optional + country code).', 'error')
            logger.debug(f"Registration failed: Invalid phone number {phone}")
            return redirect(url_for('register'))

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered.', 'error')
            logger.debug(f"Registration failed: Email {email} already registered")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        logger.info(f"User registered: {email}")
        return redirect(url_for('login'))
    
    response = make_response(render_template('register.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required.', 'error')
            logger.debug("Login failed: Missing email or password")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'error')
            logger.debug(f"Login failed: Invalid credentials for {email}")
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session.permanent = True  # Enable session timeout
        logger.info(f"User logged in: {email}")
        flash('Logged in successfully!', 'success')
        return redirect(url_for('index'))
    
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Only remove user_id, keep flash messages
    flash('Logged out successfully.', 'info')
    logger.info("User logged out")
    return redirect(url_for('login'))

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning("Unauthorized access attempt to protected route")
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- MAIN PAGE -------------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        smtp_server = request.form.get('smtp_server')
        smtp_port = request.form.get('smtp_port')
        email_address = request.form.get('email_address')
        email_password = request.form.get('email_password')
        subject = request.form.get('subject')
        body = request.form.get('message')
        file = request.files.get('csv_file')

        logger.debug(f"Received POST request with: smtp_server={smtp_server}, smtp_port={smtp_port}, email_address={email_address}, subject={subject}, file={file.filename if file and file.filename else 'None'}")
        
        # Debug file information
        if file:
            logger.debug(f"File details: filename='{file.filename}', content_type='{file.content_type}', size={len(file.read())} bytes")
            file.seek(0)  # Reset file pointer after reading for debugging
        else:
            logger.debug("No file received in request.files")

        # Validate text fields first
        missing_fields = []
        if not smtp_server: missing_fields.append("SMTP Server")
        if not smtp_port: missing_fields.append("SMTP Port") 
        if not email_address: missing_fields.append("Email Address")
        if not email_password: missing_fields.append("Email Password")
        if not subject: missing_fields.append("Subject")
        if not body: missing_fields.append("Message Body")
        
        if missing_fields:
            logger.error(f"Missing required text fields: {', '.join(missing_fields)}")
            flash(f'⚠️ Missing required fields: {", ".join(missing_fields)}', 'error')
            return redirect(url_for('index'))

        # Validate file separately with more detailed error message
        if not file or not file.filename:
            logger.error("No file uploaded")
            flash('❌ Please select a CSV file to upload. Click on the upload area and choose a file.', 'error')
            return redirect(url_for('index'))
            
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            flash('❌ Please upload a valid CSV file (.csv). Other file types are not supported.', 'error')
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save the file
            file.save(filepath)
            logger.debug(f"File saved: {filepath}")
            
            # Send emails and get results
            result = send_welcome_emails(filepath, smtp_server, smtp_port, subject, body, email_address, email_password)
            
            # Set appropriate flash message based on results
            if result['emails_sent'] > 0:
                if result['failed_emails'] > 0:
                    flash(f'✅ {result["emails_sent"]} emails sent successfully! ⚠️ {result["failed_emails"]} failed.', 'warning')
                else:
                    flash(f'🎉 Success! {result["emails_sent"]} emails sent successfully!', 'success')
                logger.info(f"Email campaign completed: {result['emails_sent']} sent, {result['failed_emails']} failed")
            else:
                flash('⚠️ No valid emails were sent. Check your file for valid name and email entries.', 'warning')
                logger.warning("No emails were sent")
            
        except ValueError as ve:
            logger.error(f"Invalid file structure: {str(ve)}")
            flash(f'❌ Invalid file structure: {str(ve)}', 'error')
        except smtplib.SMTPAuthenticationError as sae:
            logger.error(f"SMTP authentication failed: {str(sae)}")
            flash('❌ Authentication failed. Check your email and app password.', 'error')
        except smtplib.SMTPException as se:
            logger.error(f"SMTP error: {str(se)}")
            flash(f'❌ SMTP error: {str(se)}', 'error')
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            flash(f'❌ Error processing file or sending emails: {str(e)}', 'error')
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                logger.debug(f"Cleaning up file: {filepath}")
                os.remove(filepath)
        
        # Redirect to show the flash message
        return redirect(url_for('index'))

    # GET request - show the form
    logger.debug("Rendering index.html")
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)