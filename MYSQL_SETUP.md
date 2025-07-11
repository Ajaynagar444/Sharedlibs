# MySQL Database Setup for Email Campaign Manager

This guide will help you set up MySQL Workbench and configure the database for your Flask email campaign application.

## Prerequisites

- MySQL Server 8.0 or higher
- MySQL Workbench (latest version)
- Python 3.8 or higher

## Step 1: Install MySQL Server and Workbench

### Windows:
1. Download MySQL Installer from: https://dev.mysql.com/downloads/installer/
2. Run the installer and select "Custom" setup
3. Install:
   - MySQL Server 8.0
   - MySQL Workbench 8.0
   - MySQL Shell (optional)

### macOS:
```bash
# Using Homebrew
brew install mysql
brew install --cask mysqlworkbench
```

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install mysql-server mysql-workbench-community
```

## Step 2: Configure MySQL Server

### Start MySQL Service:

**Windows:**
- MySQL service should start automatically
- Or use: `net start mysql80`

**macOS:**
```bash
brew services start mysql
```

**Linux:**
```bash
sudo systemctl start mysql
sudo systemctl enable mysql  # Enable auto-start
```

### Secure MySQL Installation:
```bash
sudo mysql_secure_installation
```

Follow the prompts to:
- Set root password
- Remove anonymous users
- Disable remote root login
- Remove test database

## Step 3: Create Database User

### Option A: Using MySQL Workbench GUI

1. Open MySQL Workbench
2. Connect to your MySQL server (localhost:3306)
3. Go to **Server** → **Users and Privileges**
4. Click **Add Account**
5. Fill in:
   - **Login Name**: `email_campaign_user`
   - **Authentication Type**: `Standard`
   - **Password**: `your_secure_password`
6. Go to **Schema Privileges** tab
7. Click **Add Entry**
8. Select **Selected schema**: `email_campaign_db`
9. Grant these privileges:
   - SELECT, INSERT, UPDATE, DELETE
   - CREATE, DROP, ALTER
   - INDEX, REFERENCES
10. Click **Apply**

### Option B: Using Command Line

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

-- Flush privileges
FLUSH PRIVILEGES;

-- Exit
EXIT;
```

## Step 4: Update Environment Configuration

Edit your `.env` file with the correct database settings:

```env
# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=email_campaign_user
DB_PASSWORD=your_secure_password
DB_NAME=email_campaign_db

# Flask Configuration
SECRET_KEY=your_secret_key_here_change_this_in_production
```

## Step 5: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

## Step 6: Test Database Connection

Create a test script `test_db.py`:

```python
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"✅ Database connection successful!")
    print(f"MySQL version: {version[0]}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

Run the test:
```bash
python test_db.py
```

## Step 7: Initialize Database Tables

The Flask application will automatically create the database and tables when you first run it:

```bash
python app.py
```

## Step 8: Verify Tables in MySQL Workbench

1. Open MySQL Workbench
2. Connect to your database
3. Expand `email_campaign_db` schema
4. You should see these tables:
   - `users` - User accounts
   - `campaigns` - Email campaigns
   - `contacts` - Contact lists from CSV/Excel files
   - `email_logs` - Email sending logs

## Database Schema Overview

### users table:
- `id` (Primary Key)
- `email` (Unique)
- `password` (Hashed)
- `phone`
- `created_at`

### campaigns table:
- `id` (Primary Key)
- `user_id` (Foreign Key → users.id)
- `name`
- `subject`
- `message_body`
- `smtp_server`
- `smtp_port`
- `sender_email`
- `created_at`
- `status` (draft/completed/failed)
- `emails_sent`
- `emails_failed`

### contacts table:
- `id` (Primary Key)
- `campaign_id` (Foreign Key → campaigns.id)
- `name`
- `email`
- `created_at`

### email_logs table:
- `id` (Primary Key)
- `campaign_id` (Foreign Key → campaigns.id)
- `contact_email`
- `contact_name`
- `status` (sent/failed)
- `error_message`
- `sent_at`

## Troubleshooting

### Common Issues:

1. **Connection Refused:**
   - Check if MySQL service is running
   - Verify port 3306 is open

2. **Access Denied:**
   - Check username/password in .env file
   - Verify user privileges

3. **Database Not Found:**
   - Ensure database `email_campaign_db` exists
   - Check database name in .env file

4. **Character Set Issues:**
   - Database should use `utf8mb4` charset
   - Check collation is `utf8mb4_unicode_ci`

### MySQL Service Commands:

**Windows:**
```cmd
net start mysql80
net stop mysql80
```

**macOS:**
```bash
brew services start mysql
brew services stop mysql
```

**Linux:**
```bash
sudo systemctl start mysql
sudo systemctl stop mysql
sudo systemctl status mysql
```

## Security Best Practices

1. **Strong Passwords**: Use complex passwords for database users
2. **Limited Privileges**: Grant only necessary permissions
3. **Firewall**: Restrict database access to localhost only
4. **Regular Backups**: Set up automated database backups
5. **SSL/TLS**: Enable encrypted connections for production

## Backup and Restore

### Create Backup:
```bash
mysqldump -u email_campaign_user -p email_campaign_db > backup.sql
```

### Restore Backup:
```bash
mysql -u email_campaign_user -p email_campaign_db < backup.sql
```

## Next Steps

1. Configure your email SMTP settings
2. Prepare your CSV/Excel contact files
3. Start using the application by running `python app.py`
4. Access the web interface at `http://localhost:5000`

Your MySQL database is now ready for the Email Campaign Manager application!