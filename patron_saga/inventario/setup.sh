#!/bin/bash

# Product Inventory API Setup Script

echo "🚀 Starting Product Inventory API Setup..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment is not activated!"
    echo "Please activate your virtual environment:"
    echo "  source .venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected and active"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check PostgreSQL connection
echo "🔍 Checking PostgreSQL connection..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='postgres',
        user='postgres',
        password='postgres'
    )
    conn.close()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('Please ensure PostgreSQL is running with:')
    print('  - Username: postgres')
    print('  - Password: postgres')
    print('  - Host: localhost')
    print('  - Port: 5432')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Create database if it doesn't exist
echo "🗄️  Creating database 'saga' if it doesn't exist..."
python3 -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to postgres database
    conn = psycopg2.connect(
        host='localhost',
        database='postgres',
        user='postgres',
        password='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(\"SELECT 1 FROM pg_database WHERE datname='saga'\")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute('CREATE DATABASE saga')
        print('✅ Database \"saga\" created successfully')
    else:
        print('✅ Database \"saga\" already exists')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Database creation failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Initialize database with sample data
echo "🏗️  Initializing database with sample data..."
python3 init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the API server, run:"
echo "  python app.py"
echo ""
echo "The API will be available at:"
echo "  • Base URL: http://localhost:5000"
echo "  • Swagger Documentation: http://localhost:5000/apidocs"
echo "  • Health Check: http://localhost:5000/health"
echo ""
echo "Happy coding! 🚀" 