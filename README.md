# 🚀 Medro Hi-Tech AI Solution - Email Automation Platform

A professional email automation tool built with Flask for bulk email campaigns with personalized messaging.

## ✨ Features

- 🔐 **User Authentication** - Secure registration and login system
- 📧 **Bulk Email Automation** - Send personalized emails to multiple recipients
- 📁 **File Support** - CSV, XLSX, and XLS file uploads
- 🎯 **Personalization** - Dynamic name replacement in email content
- 🔒 **SMTP Integration** - Support for Gmail, Outlook, and other SMTP servers
- 📱 **Responsive Design** - Modern, mobile-friendly interface
- 📊 **Real-time Preview** - See how your emails will look before sending
- 🛡️ **Secure & Reliable** - Built with security best practices

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd email-automation-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your secret key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 📋 Usage

### 1. Registration & Login
- Create an account with email, password, and phone number
- Login to access the dashboard

### 2. Prepare Your Data File
Create a CSV or Excel file with these columns:
- `name` - Recipient's name
- `email` - Recipient's email address

**Example:**
```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
```

### 3. Configure SMTP Settings
- **Gmail**: `smtp.gmail.com`, Port: `465`
- **Outlook**: `smtp-mail.outlook.com`, Port: `587`
- Use App Passwords for Gmail (not your regular password)

### 4. Send Emails
- Fill in SMTP configuration
- Enter your email credentials
- Write subject and message (use `{name}` for personalization)
- Upload your recipients file
- Click "Send Bulk Emails"

## 🔧 SMTP Configuration

### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the 16-character app password in the tool

### Outlook Setup
1. Use your regular Outlook credentials
2. Server: `smtp-mail.outlook.com`
3. Port: `587` (TLS)

## 📁 File Structure

```
email-automation-tool/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── templates/            # HTML templates
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   └── index.html        # Main dashboard
├── Uploads/              # Temporary file uploads (auto-created)
├── users.db              # SQLite database (auto-created)
└── app.log               # Application logs (auto-created)
```

## 🚀 Deployment

### Environment Variables for Production
```bash
SECRET_KEY=your_production_secret_key
FLASK_ENV=production
```

### Security Considerations
- Change the default secret key
- Use HTTPS in production
- Set up proper firewall rules
- Regular security updates

## 📞 Support

For technical support or questions about Medro Hi-Tech AI Solution:
- Email: support@medrohi-tech.com
- Website: www.medrohi-tech.com

## 📄 License

© 2024 Medro Hi-Tech AI Solution. All rights reserved.

---

**Built with ❤️ by Medro Hi-Tech AI Solution Team**