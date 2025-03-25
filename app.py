from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from functools import wraps
from config import Config
import pymysql

# Use PyMySQL as the MySQL driver
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'user'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    twofa_secret = db.Column(db.String(256), nullable=True)

class Product(db.Model):
    __tablename__ = 'product'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Root route
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Flask API with 2FA and JWT Authentication',
        'endpoints': {
            'register': '/register (POST)',
            'login': '/login (POST)',
            'products': '/products (GET, POST)',
            'product': '/products/<id> (PUT, DELETE)'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested URL was not found on the server.'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error has occurred.'
    }), 500

# JWT Authentication Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# User Registration
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        # Generate 2FA secret
        secret = pyotp.random_base32()
        
        # Create new user
        new_user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            twofa_secret=secret
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=data['username'],
            issuer_name="Flask 2FA Demo"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'message': 'User registered successfully',
            'qr_code': qr_code,
            'secret': secret
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error during registration: {str(e)}'}), 500

# Login and 2FA Verification
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not data.get('totp_code'):
            return jsonify({'message': '2FA code required'}), 200
        
        # Verify 2FA code
        totp = pyotp.TOTP(user.twofa_secret)
        if not totp.verify(data['totp_code']):
            return jsonify({'message': 'Invalid 2FA code'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, app.config['JWT_SECRET_KEY'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error during login: {str(e)}'}), 500

# Product CRUD Operations
@app.route('/products', methods=['POST'])
@token_required
def create_product(current_user):
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('price') or not data.get('quantity'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        new_product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            quantity=data['quantity']
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': {
                'id': new_product.id,
                'name': new_product.name,
                'description': new_product.description,
                'price': float(new_product.price),
                'quantity': new_product.quantity
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating product: {str(e)}'}), 500

@app.route('/products', methods=['GET'])
@token_required
def get_products(current_user):
    try:
        products = Product.query.all()
        return jsonify({
            'products': [{
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'quantity': product.quantity
            } for product in products]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching products: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if data.get('name'):
            product.name = data['name']
        if data.get('description'):
            product.description = data['description']
        if data.get('price'):
            product.price = data['price']
        if data.get('quantity'):
            product.quantity = data['quantity']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'quantity': product.quantity
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating product: {str(e)}'}), 500

@app.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting product: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
    app.run(debug=True, host='0.0.0.0', port=5000) 