# Email Campaign Manager with MySQL Integration

A powerful Flask-based email campaign management system that stores all data in MySQL database. Send personalized bulk emails with CSV/Excel contact lists, track campaign performance, and manage email logs.

## ✨ Features

- **User Authentication**: Secure user registration and login system
- **MySQL Database**: All data stored in MySQL for reliability and scalability
- **Campaign Management**: Create, track, and manage email campaigns
- **Contact Import**: Upload contacts from CSV, XLSX, or XLS files
- **Email Personalization**: Use `{name}` placeholder for personalized messages
- **SMTP Support**: Works with Gmail, Outlook, and other SMTP providers
- **Email Logging**: Track successful sends and failures with detailed logs
- **Campaign Analytics**: View success rates and campaign statistics
- **Responsive UI**: Modern Bootstrap-based interface

## �️ Database Schema

### Tables Overview:
- **users**: User accounts with authentication
- **campaigns**: Email campaign information and settings
- **contacts**: Contact lists imported from CSV/Excel files
- **email_logs**: Detailed logs of all email sending attempts

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- MySQL Workbench (recommended)

## � Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repository-url>
cd email-campaign-manager

# Install dependencies
pip install -r requirements.txt
```

### 2. MySQL Setup

Follow the detailed instructions in `MYSQL_SETUP.md` or quick setup:

```sql
-- Connect to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE email_campaign_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'email_campaign_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES 
ON email_campaign_db.* TO 'email_campaign_user'@'localhost';

FLUSH PRIVILEGES;
EXIT;
```

### 3. Environment Configuration

Create a `.env` file:

```env
SECRET_KEY=your_secret_key_here_change_this_in_production

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=email_campaign_user
DB_PASSWORD=your_secure_password
DB_NAME=email_campaign_db
```

### 4. Test Database Connection

```bash
python test_db.py
```

### 5. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## 📊 File Format Requirements

Your contact files should contain these columns:

| Column | Description | Required |
|--------|-------------|----------|
| name   | Contact name | Yes |
| email  | Email address | Yes |

### Example CSV:
```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
Alice Johnson,alice@example.com
```

### Supported Formats:
- CSV (.csv)
- Excel (.xlsx, .xls)
- Maximum file size: 10MB

## 🔧 SMTP Configuration

### Gmail Setup:
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App passwords
3. Use these settings:
   - SMTP Server: `smtp.gmail.com`
   - SMTP Port: `465`
   - Email: Your Gmail address
   - Password: Generated app password

### Outlook/Hotmail:
- SMTP Server: `smtp-mail.outlook.com`
- SMTP Port: `587`

### Other Providers:
Check your email provider's SMTP settings documentation.

## 🎯 Usage Guide

### 1. Register/Login
- Create an account or login with existing credentials
- Phone number required for registration

### 2. Create Campaign
- Fill in campaign details (name, subject, message)
- Configure SMTP settings
- Upload contact list (CSV/Excel)
- Use `{name}` in your message for personalization

### 3. Track Results
- View campaign statistics on dashboard
- Check detailed logs in campaign details
- Monitor success/failure rates

### 4. Manage Campaigns
- View all campaigns in "My Campaigns"
- Access detailed analytics and logs
- Delete old campaigns if needed

## 🏗️ Application Structure

```
email-campaign-manager/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── test_db.py            # Database connection test
├── MYSQL_SETUP.md        # Detailed MySQL setup guide
├── README.md             # This file
├── templates/            # HTML templates
│   ├── index.html        # Main campaign creation form
│   ├── campaigns.html    # Campaign listing page
│   ├── campaign_details.html # Detailed campaign view
│   ├── login.html        # Login page
│   └── register.html     # Registration page
├── Uploads/              # Temporary file storage (auto-created)
└── app.log              # Application log file
```

## 🔐 Security Features

- **Password Hashing**: Werkzeug secure password hashing
- **Session Management**: Secure session handling with timeout
- **Input Validation**: File type and size validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **CSRF Protection**: Form security measures

## 📈 Database Features

- **Automatic Database Creation**: App creates database if it doesn't exist
- **Table Auto-generation**: SQLAlchemy creates all tables automatically
- **Foreign Key Relationships**: Proper data relationships
- **UTF-8 Support**: Full Unicode character support
- **Connection Pooling**: Efficient database connections

## 🛠️ Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   ```bash
   # Check MySQL service
   sudo systemctl status mysql
   
   # Test connection
   python test_db.py
   ```

2. **SMTP Authentication Error**
   - Use app-specific passwords for Gmail
   - Check SMTP server and port settings
   - Verify email credentials

3. **File Upload Issues**
   - Ensure file has 'name' and 'email' columns
   - Check file size (max 10MB)
   - Verify file format (CSV, XLSX, XLS)

4. **Permission Errors**
   - Check database user privileges
   - Verify file system permissions

### Debug Mode:
Set `FLASK_DEBUG=True` in `.env` for detailed error messages.

## 🔄 Backup and Maintenance

### Database Backup:
```bash
mysqldump -u email_campaign_user -p email_campaign_db > backup.sql
```

### Log Rotation:
Monitor and rotate `app.log` file regularly to prevent disk space issues.

### Regular Maintenance:
- Clean up old campaign data periodically
- Monitor database size and performance
- Update dependencies regularly

## 🌟 Advanced Features

### Campaign Analytics:
- Success rate tracking
- Email delivery statistics
- Error message logging
- Campaign comparison

### Data Export:
- Export contact lists
- Campaign performance reports
- Email log analysis

### Scalability:
- MySQL database for high performance
- Connection pooling for concurrent users
- Efficient query optimization

## � API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET/POST | Main campaign creation |
| `/login` | GET/POST | User authentication |
| `/register` | GET/POST | User registration |
| `/logout` | GET | User logout |
| `/campaigns` | GET | List all campaigns |
| `/campaign/<id>` | GET | Campaign details |
| `/delete_campaign/<id>` | POST | Delete campaign |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review MySQL setup guide
3. Run database connection test
4. Check application logs

## 🔮 Future Enhancements

- Email template system
- Scheduled campaigns
- A/B testing
- Advanced analytics dashboard
- Email bounce handling
- Integration with external APIs
- Multi-language support

---

**Note**: Always use app-specific passwords for email providers like Gmail. Never use your regular account password for SMTP authentication.