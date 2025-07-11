import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection and basic operations"""
    
    print("🔍 Testing MySQL Database Connection...")
    print("-" * 50)
    
    # Get database configuration from environment
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4'
    }
    
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print("-" * 50)
    
    try:
        # Test connection without database first
        print("1. Testing connection to MySQL server...")
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset']
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"   ✅ MySQL server connection successful!")
        print(f"   📊 MySQL version: {version[0]}")
        
        # Check if database exists
        print(f"\n2. Checking if database '{db_config['database']}' exists...")
        cursor.execute(f"SHOW DATABASES LIKE '{db_config['database']}'")
        db_exists = cursor.fetchone()
        
        if db_exists:
            print(f"   ✅ Database '{db_config['database']}' exists!")
        else:
            print(f"   ⚠️  Database '{db_config['database']}' does not exist.")
            print(f"   📝 Creating database '{db_config['database']}'...")
            cursor.execute(f"CREATE DATABASE {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"   ✅ Database '{db_config['database']}' created successfully!")
        
        cursor.close()
        connection.close()
        
        # Test connection to specific database
        print(f"\n3. Testing connection to database '{db_config['database']}'...")
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # Test basic operations
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()
        print(f"   ✅ Connected to database: {current_db[0]}")
        
        # Show existing tables
        print(f"\n4. Checking existing tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"   📋 Found {len(tables)} table(s):")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()
                print(f"      - {table[0]}: {count[0]} records")
        else:
            print("   📋 No tables found (this is normal for a fresh installation)")
        
        # Test write permissions
        print(f"\n5. Testing write permissions...")
        test_table = "connection_test_temp"
        
        try:
            cursor.execute(f"""
                CREATE TEMPORARY TABLE {test_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_message VARCHAR(100)
                )
            """)
            
            cursor.execute(f"INSERT INTO {test_table} (test_message) VALUES ('Connection test successful')")
            cursor.execute(f"SELECT test_message FROM {test_table}")
            result = cursor.fetchone()
            
            if result and result[0] == 'Connection test successful':
                print("   ✅ Write permissions working correctly!")
            else:
                print("   ❌ Write test failed!")
                
        except Exception as write_error:
            print(f"   ❌ Write permission test failed: {write_error}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE CONNECTION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("\n✅ Your database is ready for the Flask application!")
        print("🚀 You can now run: python app.py")
        
        return True
        
    except pymysql.Error as db_error:
        print(f"\n❌ Database connection failed!")
        print(f"Error: {db_error}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if MySQL service is running")
        print("2. Verify database credentials in .env file")
        print("3. Ensure the database user has proper privileges")
        print("4. Check if the database exists")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please create a .env file with your database configuration.")
        print("\nExample .env content:")
        print("DB_HOST=localhost")
        print("DB_PORT=3306")
        print("DB_USER=your_mysql_username")
        print("DB_PASSWORD=your_mysql_password")
        print("DB_NAME=email_campaign_db")
        exit(1)
    
    # Check if required environment variables are set
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please check your .env file configuration.")
        exit(1)
    
    # Run the test
    success = test_database_connection()
    exit(0 if success else 1)