# Business Management System

## 1. Project Overview
The Business Management System is a comprehensive, web-based application designed to help businesses manage their daily operations. It streamlines inventory management, tracks sales and purchases, manages customer and supplier ledgers, and provides detailed reporting. The system is built with a focus on ease of use, robust tracking of financial flows, and reliable data management.

**Main Features:**
- Complete Sale and Purchase workflows (including Returns).
- Customer and Supplier management with advanced ledger tracking.
- Expense and Cash ledger management.
- Dynamic Due Tracking with support for advance balances.
- Detailed reporting modules for sales, collections, incomes, and stock.
- Multi-user authentication and role-based access control.

## 2. Technology Stack
- **Python Framework:** Flask (v3.0.3)
- **Frontend Technologies:** HTML5, CSS3, JavaScript (jQuery, Select2, DataTables), Bootstrap 5, Jinja2 templating.
- **Database:** Turso / libSQL (using `libsql-experimental` and `sqlalchemy-libsql`) via Flask-SQLAlchemy.
- **Other Major Libraries:**
  - `Flask-Login` for session management and authentication.
  - `Flask-Migrate` for database schema migrations.
  - `gunicorn` for production deployment.
  - `Pillow` and `cloudinary` for avatar uploads.

## 3. Project Structure
- `app.py`: Application factory, Flask configuration, and initialization routines.
- `models.py`: Database models (SQLAlchemy) defining the schema for Businesses, Admins, Products, Sales, Purchases, Ledgers, etc.
- `routes.py`: Core routing and general application views.
- `auth.py`: Authentication, login, and access control decorators.
- `sale.py`, `purchase.py`, `customer.py`, `supplier.py`: Blueprint modules handling specific domain logic.
- `customer_collection.py`, `supplier_payment.py`: Handling of payment receipts, due tracking, and ledger updates.
- `templates/`: Jinja2 HTML templates for the frontend views.
- `static/`: Static assets (CSS, JS, Images).
- `migrations/`: Alembic database migration scripts.

## 4. Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory and populate it with the required variables (see section 5).

5. **Initialize the database:**
   The application is configured to automatically create the initial schema and a default `siteadmin` account upon startup if it does not exist.
   To run migrations manually:
   ```bash
   flask db upgrade
   ```

6. **Run the application:**
   ```bash
   python app.py
   # OR
   flask run --host=0.0.0.0 --port=8080
   ```

## 5. Environment Variables
Create a `.env` file in the project root with the following variables:

- `DATABASE_URL`: The connection string for the Turso/libSQL database (e.g., `sqlite+libsql://<your-db-url>/?secure=true`).
- `TURSO_AUTH_TOKEN`: The authentication token required to connect to the Turso database.
- `CLOUDINARY_URL`: The connection string for Cloudinary avatar uploads (e.g., `cloudinary://<api_key>:<api_secret>@<cloud_name>`).
- `SECRET_KEY` (Optional but recommended): Flask application secret key for session signing.

*(Note: Do not expose actual tokens or passwords in version control.)*

## 6. Database
This project utilizes the **Turso Database** (libSQL), a lightweight and highly scalable SQLite-compatible database designed for edge deployments. 
- **Configuration**: Ensure `DATABASE_URL` uses the `sqlite+libsql://` scheme and `TURSO_AUTH_TOKEN` is provided in the `.env` file.
- **Data Migration**: This is a fresh database configuration optimized for libSQL. No legacy PostgreSQL data migration is required.

## 7. Features
- **Sales**: Create, edit, and track sales invoices. Supports adding multiple products via barcode/search, calculating discounts, VAT, and shipping costs.
- **Customer Management**: Maintain a directory of customers with contact details and full transaction histories.
- **Customer Collection**: Record payments received from customers.
- **Due Tracking**: Automatically tracks historic due balances dynamically based on sales, returns, and collections.
- **Customer Advance Balance (Negative Due)**: Customers can overpay, seamlessly resulting in a negative due which acts as an advance balance applied to future purchases.
- **Reports**: Generate detailed date-filtered reports for Sales, Collections, Incomes, Customer Ledgers, and more. DataTables integration allows exporting to PDF, Excel, or Print.
- **Authentication**: Secure login system with role-based access control (Admin vs. Employee).

## 8. Recent Changes
- **Added Previous Due display on the Add Sale page**: Sales agents can now see a customer's exact historic due in real-time when creating an invoice.
- **Added Customer Advance Balance support**: Users can now record collections that exceed a customer's current due, safely storing negative due values as advance balances.
- **Reused existing APIs**: Optimized frontend features to rely on existing backend data routes (e.g., `get_customer_due`) to minimize duplication.
- **No unnecessary database schema changes**: Enhanced due calculations without altering the underlying database schema.

## 9. Development Notes
- **Coding Guidelines**: Ensure all new routes are registered via Flask Blueprints. Use Jinja2 template inheritance (`base.html`) for consistent UI.
- **Adding New Modules**: When creating a new module (e.g., a new ledger type), create a dedicated Python file for the Blueprint, register it in `app.py`, and add the corresponding SQLAlchemy model in `models.py`.
- **Database Changes**: Always use `Flask-Migrate` (`flask db migrate -m "message"`) to generate migration scripts when modifying `models.py`. Review the generated script before running `flask db upgrade`.

## 10. License
This project is proprietary and confidential. Unauthorized copying, distribution, or modification is strictly prohibited.