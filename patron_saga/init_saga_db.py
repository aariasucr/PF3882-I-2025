#!/usr/bin/env python3
"""
Saga Database Initialization Script
This script properly initializes all databases for the saga implementation.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the saga database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'saga'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('CREATE DATABASE saga')
            print("✅ Created 'saga' database")
        else:
            print("ℹ️  Database 'saga' already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def init_service_tables(service_name, app_module):
    """Initialize tables for a specific service"""
    try:
        # Change to service directory
        service_path = os.path.join(os.path.dirname(__file__), service_name)
        original_path = sys.path[:]
        sys.path.insert(0, service_path)
        
        # Set environment variable for database
        os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/saga'
        
        if service_name == 'carrito':
            from app import app, db
            with app.app_context():
                db.create_all()
                print(f"✅ Initialized {service_name} tables")
                
        elif service_name == 'inventario':
            from app import app, db
            with app.app_context():
                db.create_all()
                print(f"✅ Initialized {service_name} tables")
                
        elif service_name == 'pagos':
            from app import app
            from models import db
            with app.app_context():
                db.create_all()
                print(f"✅ Initialized {service_name} tables")
                
        elif service_name == 'saga_orchestrator':
            from orchestrator import app, db
            with app.app_context():
                db.create_all()
                print(f"✅ Initialized {service_name} tables")
        
        # Restore path
        sys.path = original_path
        
    except Exception as e:
        print(f"❌ Error initializing {service_name} tables: {e}")
        sys.path = original_path
        return False
    
    return True

def add_sample_data():
    """Add sample data to test the system"""
    try:
        # Add sample product to inventory
        service_path = os.path.join(os.path.dirname(__file__), 'inventario')
        sys.path.insert(0, service_path)
        
        from app import app, db, Product
        
        with app.app_context():
            # Check if sample product exists
            existing_product = Product.query.filter_by(sku='LAPTOP-001').first()
            
            if not existing_product:
                sample_product = Product(
                    name='Laptop Pro',
                    description='High-performance laptop for saga testing',
                    price=1299.99,
                    quantity=50,
                    category='Electronics',
                    sku='LAPTOP-001'
                )
                
                db.session.add(sample_product)
                db.session.commit()
                print("✅ Added sample product to inventory")
            else:
                print("ℹ️  Sample product already exists")
                
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")

def main():
    """Main initialization function"""
    print("🚀 Initializing Saga Database System...")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database. Exiting.")
        return
    
    # Step 2: Initialize service tables in dependency order
    services = [
        'inventario',  # Independent service
        'pagos',       # Independent service  
        'carrito',     # May reference products
        'saga_orchestrator'  # References other services
    ]
    
    for service in services:
        print(f"\n📊 Initializing {service}...")
        if not init_service_tables(service, None):
            print(f"⚠️  Warning: Failed to initialize {service}")
    
    # Step 3: Add sample data
    print(f"\n📦 Adding sample data...")
    add_sample_data()
    
    print("\n" + "=" * 50)
    print("🎉 Saga database initialization complete!")
    print("\nNext steps:")
    print("1. Start the services: docker-compose -f docker-compose.saga.yml up -d")
    print("2. Test the orchestrated saga: curl -X POST http://localhost:3003/saga/checkout")
    print("3. Test the choreographed saga: curl -X POST http://localhost:3004/saga/choreography/checkout")

if __name__ == "__main__":
    main() 