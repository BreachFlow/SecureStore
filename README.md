# Flask API with 2FA and JWT Authentication

This is a secure Flask API that implements user authentication with Two-Factor Authentication (2FA) using Google Authenticator and JWT tokens for CRUD operations on a Products table.

## Features

- User registration with secure password hashing
- Two-Factor Authentication using Google Authenticator
- JWT-based authentication for API endpoints
- CRUD operations for Products table
- MySQL database integration

## Prerequisites

- Python 3.8 or higher
- MySQL server
- phpMyAdmin (for database management)
- Google Authenticator app (for 2FA)

## Setup

1. Create a MySQL database using phpMyAdmin:
   - Open phpMyAdmin in your web browser (typically at http://localhost/phpmyadmin)
   - Click on "New" in the left sidebar
   - Enter "securestore" as the database name
   - Click "Create"

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Configure the database connection in `config.py`:
   - Update the `SQLALCHEMY_DATABASE_URI` with your MySQL credentials:
     ```python
     SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/securestore'
     ```
   - Replace 'username' and 'password' with your MySQL credentials
   - Set a secure `JWT_SECRET_KEY`

4. Run the application:
```bash
python app.py
```

The application will automatically create the necessary tables in the database.

## Database Structure

### User Table
```sql
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    twofa_secret VARCHAR(256)
);
```

### Product Table
```sql
CREATE TABLE product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL
);
```

## API Endpoints

### User Registration
```
POST /register
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

### Login with 2FA
```
POST /login
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password",
    "totp_code": "2fa_code"
}
```

### Product Operations

All product endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer your_jwt_token
```

#### Create Product
```
POST /products
Content-Type: application/json

{
    "name": "Product Name",
    "description": "Product Description",
    "price": 99.99,
    "quantity": 100
}
```

#### Get All Products
```
GET /products
```

#### Update Product
```
PUT /products/<product_id>
Content-Type: application/json

{
    "name": "Updated Name",
    "price": 89.99,
    "quantity": 50
}
```

#### Delete Product
```
DELETE /products/<product_id>
```

## Security Features

- Passwords are hashed using Werkzeug's security functions
- JWT tokens expire after 10 minutes
- Two-Factor Authentication using Google Authenticator
- Secure password storage in MySQL
- Protected CRUD operations with JWT authentication
- Error handling and database transaction management

## Notes

- The application runs in debug mode by default. For production, disable debug mode and use a proper WSGI server.
- Make sure to use HTTPS in production to secure the API endpoints.
- Store sensitive configuration values in environment variables.
- The database tables will be automatically created when you run the application for the first time.
- If you encounter any database connection issues, verify your MySQL credentials and make sure the MySQL server is running. 