from flask import Flask, render_template, request, redirect, flash, url_for, session, Response
from datetime import timedelta, datetime
from flask import make_response
import os
import pandas as pd
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
import pymysql

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
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB file size limit
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}  # Support CSV and Excel files

# MySQL Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'email_campaign_db')

# Setup MySQL DB connection
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_timeout': 20,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)

# User model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with campaigns
    campaigns = db.relationship('Campaign', backref='user', lazy=True, cascade='all, delete-orphan')

# Campaign model
class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    smtp_server = db.Column(db.String(100), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False)
    sender_email = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')  # draft, completed, failed
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    
    # Relationship with contacts
    contacts = db.relationship('Contact', backref='campaign', lazy=True, cascade='all, delete-orphan')
    email_logs = db.relationship('EmailLog', backref='campaign', lazy=True, cascade='all, delete-orphan')

# Contact model (from CSV/Excel files)
class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Email Log model
class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    contact_email = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # sent, failed
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database and tables
def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        connection.close()
        logger.info(f"Database {DB_NAME} created or already exists")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise e

# Initialize database
try:
    create_database()
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

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

def store_contacts_from_file(file_path, campaign_id):
    """Store contacts from CSV/Excel file to database"""
    try:
        logger.debug(f"Processing file for campaign {campaign_id}: {file_path}")
        
        # Read file with pandas
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")

        # Validate required columns
        if df.empty:
            raise ValueError("File is empty or contains no valid data")
            
        available_columns = set(col.lower() for col in df.columns)
        required_columns = {'name', 'email'}
        
        if not required_columns.issubset(available_columns):
            missing = required_columns - available_columns
            raise ValueError(f"Missing required columns: {', '.join(missing)}. Available columns: {', '.join(available_columns)}")

        contacts_added = 0
        
        # Process each row and store in database
        for index, row in df.iterrows():
            name = str(row.get('name', '') or row.get('Name', '')).strip()
            email = str(row.get('email', '') or row.get('Email', '')).strip()
            
            if not name or not email or email.lower() == 'nan':
                logger.warning(f"Skipping row {index + 1}: missing name or email")
                continue
            
            # Check if contact already exists for this campaign
            existing_contact = Contact.query.filter_by(
                campaign_id=campaign_id, 
                email=email
            ).first()
            
            if not existing_contact:
                contact = Contact(
                    campaign_id=campaign_id,
                    name=name,
                    email=email
                )
                db.session.add(contact)
                contacts_added += 1
        
        db.session.commit()
        logger.info(f"Stored {contacts_added} contacts for campaign {campaign_id}")
        return contacts_added
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error storing contacts: {str(e)}")
        raise e

def send_campaign_emails(campaign_id, email_password):
    """Send emails for a campaign and log results"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        contacts = Contact.query.filter_by(campaign_id=campaign_id).all()
        if not contacts:
            raise ValueError("No contacts found for this campaign")
        
        context = ssl.create_default_context()
        emails_sent = 0
        failed_emails = 0
        
        with smtplib.SMTP_SSL(campaign.smtp_server, campaign.smtp_port, context=context) as server:
            logger.debug(f"Logging in to SMTP server: {campaign.smtp_server}:{campaign.smtp_port}")
            
            try:
                server.login(campaign.sender_email, email_password)
                logger.info("SMTP authentication successful")
            except smtplib.SMTPAuthenticationError as auth_error:
                logger.error(f"SMTP authentication failed: {auth_error}")
                raise smtplib.SMTPAuthenticationError(auth_error.smtp_code, auth_error.smtp_error)
            
            # Send emails to all contacts
            for contact in contacts:
                msg = create_email(contact.name, contact.email, campaign.subject, campaign.message_body, campaign.sender_email)
                
                try:
                    server.send_message(msg)
                    emails_sent += 1
                    
                    # Log successful send
                    email_log = EmailLog(
                        campaign_id=campaign_id,
                        contact_email=contact.email,
                        contact_name=contact.name,
                        status='sent'
                    )
                    db.session.add(email_log)
                    logger.info(f"✅ Email sent to {contact.name} <{contact.email}>")
                    
                except Exception as send_error:
                    failed_emails += 1
                    
                    # Log failed send
                    email_log = EmailLog(
                        campaign_id=campaign_id,
                        contact_email=contact.email,
                        contact_name=contact.name,
                        status='failed',
                        error_message=str(send_error)
                    )
                    db.session.add(email_log)
                    logger.error(f"❌ Failed to send email to {contact.email}: {send_error}")
        
        # Update campaign statistics
        campaign.emails_sent = emails_sent
        campaign.emails_failed = failed_emails
        campaign.status = 'completed' if emails_sent > 0 else 'failed'
        
        db.session.commit()
        
        return {
            'success': True,
            'emails_sent': emails_sent,
            'failed_emails': failed_emails,
            'total_processed': emails_sent + failed_emails
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending campaign emails: {str(e)}")
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

        try:
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password=hashed_password, phone=phone)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            logger.info(f"User registered: {email}")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            logger.error(f"Registration error: {e}")
            return redirect(url_for('register'))
    
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
    session.pop('user_id', None)
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
    user_id = session['user_id']
    
    if request.method == 'POST':
        campaign_name = request.form.get('campaign_name', f'Campaign {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        smtp_server = request.form.get('smtp_server')
        smtp_port = request.form.get('smtp_port')
        email_address = request.form.get('email_address')
        email_password = request.form.get('email_password')
        subject = request.form.get('subject')
        body = request.form.get('message')
        file = request.files.get('csv_file')

        logger.debug(f"Received POST request with: smtp_server={smtp_server}, smtp_port={smtp_port}, email_address={email_address}, subject={subject}, file={file.filename if file else 'None'}")

        # Validate all required fields
        if not all([smtp_server, smtp_port, email_address, email_password, subject, body, file]):
            logger.error("Missing required fields")
            flash('⚠️ All fields are required.', 'error')
            return redirect(url_for('index'))

        # Validate file
        if not file or not allowed_file(file.filename):
            logger.error("Invalid or missing file")
            flash('❌ Please upload a valid CSV, XLSX, or XLS file.', 'error')
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save the file temporarily
            file.save(filepath)
            logger.debug(f"File saved: {filepath}")
            
            # Create campaign record
            campaign = Campaign(
                user_id=user_id,
                name=campaign_name,
                subject=subject,
                message_body=body,
                smtp_server=smtp_server,
                smtp_port=int(smtp_port),
                sender_email=email_address,
                status='draft'
            )
            db.session.add(campaign)
            db.session.commit()
            
            # Store contacts from file
            contacts_added = store_contacts_from_file(filepath, campaign.id)
            
            if contacts_added == 0:
                flash('⚠️ No valid contacts found in the uploaded file.', 'warning')
                db.session.delete(campaign)
                db.session.commit()
                return redirect(url_for('index'))
            
            # Send emails and get results
            result = send_campaign_emails(campaign.id, email_password)
            
            # Set appropriate flash message based on results
            if result['emails_sent'] > 0:
                if result['failed_emails'] > 0:
                    flash(f'✅ {result["emails_sent"]} emails sent successfully! ⚠️ {result["failed_emails"]} failed.', 'warning')
                else:
                    flash(f'🎉 Success! {result["emails_sent"]} emails sent successfully!', 'success')
                logger.info(f"Email campaign completed: {result['emails_sent']} sent, {result['failed_emails']} failed")
            else:
                flash('⚠️ No emails were sent. Check your SMTP settings and try again.', 'warning')
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

    # GET request - show the form with user's campaigns
    user_campaigns = Campaign.query.filter_by(user_id=user_id).order_by(Campaign.created_at.desc()).limit(10).all()
    logger.debug("Rendering index.html")
    response = make_response(render_template('index.html', campaigns=user_campaigns))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ----------------- CAMPAIGN MANAGEMENT ROUTES -------------------

@app.route('/campaigns')
@login_required
def campaigns():
    """View all campaigns for the logged-in user"""
    user_id = session['user_id']
    user_campaigns = Campaign.query.filter_by(user_id=user_id).order_by(Campaign.created_at.desc()).all()
    return render_template('campaigns.html', campaigns=user_campaigns)

@app.route('/campaign/<int:campaign_id>')
@login_required
def campaign_details(campaign_id):
    """View details of a specific campaign"""
    user_id = session['user_id']
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('campaigns'))
    
    contacts = Contact.query.filter_by(campaign_id=campaign_id).all()
    email_logs = EmailLog.query.filter_by(campaign_id=campaign_id).order_by(EmailLog.sent_at.desc()).all()
    
    return render_template('campaign_details.html', campaign=campaign, contacts=contacts, email_logs=email_logs)

@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    """Delete a campaign and all associated data"""
    user_id = session['user_id']
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=user_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('campaigns'))
    
    try:
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully.', 'success')
        logger.info(f"Campaign {campaign_id} deleted by user {user_id}")
    except Exception as e:
        db.session.rollback()
        flash('Error deleting campaign.', 'error')
        logger.error(f"Error deleting campaign {campaign_id}: {e}")
    
    return redirect(url_for('campaigns'))

if __name__ == '__main__':
    app.run(debug=True)