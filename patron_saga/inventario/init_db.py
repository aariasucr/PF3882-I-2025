#!/usr/bin/env python3
"""
Database initialization script for Product Inventory API
"""

from app import app, db, Product
from decimal import Decimal


def init_database():
    """Initialize the database and create sample data"""

    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Check if we already have data
        if Product.query.first() is not None:
            print("Database already contains data. Skipping sample data creation.")
            return

        # Create sample products
        sample_products = [
            {
                'name': 'Gaming Laptop',
                'description': 'High-performance laptop for gaming and development',
                'price': Decimal('1299.99'),
                'quantity': 15,
                'category': 'Electronics',
                'sku': 'LAPTOP-001'
            },
            {
                'name': 'Wireless Mouse',
                'description': 'Ergonomic wireless mouse with precision tracking',
                'price': Decimal('49.99'),
                'quantity': 100,
                'category': 'Electronics',
                'sku': 'MOUSE-001'
            },
            {
                'name': 'Mechanical Keyboard',
                'description': 'RGB mechanical keyboard with blue switches',
                'price': Decimal('129.99'),
                'quantity': 50,
                'category': 'Electronics',
                'sku': 'KEYBOARD-001'
            },
            {
                'name': 'Office Chair',
                'description': 'Ergonomic office chair with lumbar support',
                'price': Decimal('299.99'),
                'quantity': 25,
                'category': 'Furniture',
                'sku': 'CHAIR-001'
            },
            {
                'name': 'Standing Desk',
                'description': 'Adjustable height standing desk',
                'price': Decimal('499.99'),
                'quantity': 10,
                'category': 'Furniture',
                'sku': 'DESK-001'
            },
            {
                'name': 'USB-C Hub',
                'description': 'Multi-port USB-C hub with HDMI and ethernet',
                'price': Decimal('79.99'),
                'quantity': 75,
                'category': 'Electronics',
                'sku': 'HUB-001'
            },
            {
                'name': 'External Monitor',
                'description': '27-inch 4K external monitor',
                'price': Decimal('399.99'),
                'quantity': 20,
                'category': 'Electronics',
                'sku': 'MONITOR-001'
            },
            {
                'name': 'Webcam',
                'description': '1080p HD webcam with auto-focus',
                'price': Decimal('89.99'),
                'quantity': 60,
                'category': 'Electronics',
                'sku': 'WEBCAM-001'
            }
        ]

        print("Creating sample products...")
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)

        try:
            db.session.commit()
            print(
                f"Successfully created {len(sample_products)} sample products!")
            print("\nSample products:")
            for product in Product.query.all():
                print(
                    f"- {product.name} (SKU: {product.sku}) - ${product.price} - Qty: {product.quantity}")

        except Exception as e:
            db.session.rollback()
            print(f"Error creating sample data: {str(e)}")
            raise


def reset_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Recreating tables...")
        db.create_all()
        print("Database reset complete!")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()

    init_database()
    print("\nDatabase initialization complete!")
    print("You can now start the Flask application with: python app.py")
