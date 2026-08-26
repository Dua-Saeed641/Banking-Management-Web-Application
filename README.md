# Netbanking Management System

A full-stack banking management web application simulating core NetBanking functionality, relationship officer management, and enterprise banking governance. Built with Python, Flask, Flask-SQLAlchemy, and modern UI design system standards.

---

## Overview

The **Banking Management System** provides a secure, role-based platform for three primary user classes: **NetBanking Customers**, **PR Officers (PROs)**, and **Banking Administrators**. The application enforces dynamic minimum balance policies based on active banking scheme enrollments, handles real-time deposits and withdrawals with transaction ledger tracking, and provides relationship officers with customer portfolio management tools.

---

## Key Features

### User NetBanking
* **Account Onboarding**: Instant registration with auto-generated 10-digit bank account number and ₹1,000 default minimum balance requirement.
* **Account Dashboard**: Hero card displaying real-time balance, account status, IFSC code, and assigned PRO.
* **Quick Financial Operations**:
  * **Deposits**: Instant balance updates with transaction ledger entry.
  * **Withdrawals**: Validated against dynamic scheme minimum balance rules (prevents balance from dropping below requirement).
* **Transaction History**: Searchable transaction ledger with unique reference numbers (`TXN-XXXXX`), status badges, and timestamping.
* **Banking Schemes Workspace**:
  * View active scheme details and interest rates.
  * Receive, accept, or decline scheme recommendations suggested by assigned PRO.
  * Automatic replacement of previous schemes upon accepting a new recommendation.

### Banking Professional (PRO) Portal
* **Approval-Based Onboarding**: Applicants submit registration requests and wait for Administrator approval before receiving an employee code (`EMP001`).
* **Customer Roster Management**: View assigned customer profiles, bank account numbers, and balance totals.
* **Scheme Recommendation Engine**:
  * Recommend active banking schemes tailored to customer account balances.
  * Automated eligibility check preventing recommendations if customer balance is below scheme requirement.
  * Prevention of duplicate pending recommendations.
* **Customer Transaction Auditing**: Review transaction ledgers for assigned customers.
* **Inline Account Controls**: Freeze or activate assigned customer accounts when needed.

### Administrator Portal
* **System Governance Dashboard**: Executive metrics dashboard featuring customer count, PRO count, active schemes, total transaction volume, and access control distribution charts.
* **PRO Application Review**: Approve pending PRO applications with auto-assignment of employee codes, or blacklist untrusted applicants.
* **PRO Portfolio Management**: Inspect PRO profiles, total recommendation performance (Accepted / Pending / Rejected / Replaced), and customer assignments.
* **User Management**: Reassign customers to available PROs, freeze/activate bank accounts, or blacklist users.
* **Banking Scheme Lifecycle Management**: Full CRUD operations for creating, editing, and toggling banking schemes in the product catalog.

---

## Security & Access Control

* **Role-Based Authorization Decorators**: `@admin_required`, `@pro_required`, and `@login_required` guard every controller endpoint.
* **Session Integrity & Object Scoping**:
  * Customers can only access their own bank account and scheme recommendations.
  * PROs can only view and manage customers explicitly assigned to them by an Admin.
* **Account Access Control**:
  * **Frozen Accounts**: Blocks deposit, withdrawal, and scheme acceptance actions immediately.
  * **Blacklisted Users/PROs**: Revokes session access and blocks authentication attempts.
* **Password Hashing**: Secure password hashing using Werkzeug `scrypt` hashing algorithm.

---

## Banking Scheme Lifecycle

```text
       ADMIN CREATES SCHEME
               │
               ▼
     PRO RECOMMENDS SCHEME TO USER
(Checks Customer Balance >= Min Balance)
               │
               ▼
       PENDING RECOMMENDATION
               │
       ┌───────┴───────┐
       ▼               ▼
USER ACCEPTS     USER REJECTS
       │
       ├─► Previous Scheme -> Replaced
       │
       ▼
ACTIVE SCHEME LINKED TO BANK ACCOUNT
       │
       ▼
DYNAMIC MINIMUM BALANCE ENFORCED ON WITHDRAWALS
```

---

## End-to-End Workflow

```text
USER REGISTRATION ──► BANK ACCOUNT CREATED (Default Min. Balance ₹1,000)
                              │
PRO REGISTRATION  ──► ADMIN APPROVES PRO (Assigns Employee Code EMP001)
                              │
ADMIN ASSIGNMENT  ──► PRO ASSIGNED TO USER (User.assigned_pro_id updated)
                              │
PRO RECOMMENDATION──► PRO RECOMMENDS BANKING SCHEME (Status: Pending)
                              │
SCHEME ACCEPTANCE ──► USER ACCEPTS SCHEME (BankAccount.scheme_id linked)
                              │
FINANCIAL DEPOSIT ──► USER DEPOSITS FUNDS (Transaction Recorded in Ledger)
                              │
WITHDRAWAL CHECK  ──► DYNAMIC MIN BALANCE ENFORCED (Balance >= Scheme Min)
                              │
ACCOUNT FREEZING  ──► ADMIN / PRO FREEZES ACCOUNT (All Transactions Blocked)
```

---

## Architecture

```text
Client Browser (HTML5 / Bootstrap 5 / Vanilla CSS)
       │
       ▼
Flask Web Framework (Controllers & Routes)
       │
       ├── Flask-Login (Session & Identity Management)
       ├── Custom Decorators (@admin_required, @pro_required)
       │
       ▼
Flask-SQLAlchemy (ORM Layer)
       │
       ▼
SQLite Database (Relational Data Persistence)
```

---

## Technology Stack

| Component | Technology |
| --- | --- |
| **Backend Framework** | Python 3.14, Flask 3.x |
| **Authentication** | Flask-Login |
| **ORM & Database** | Flask-SQLAlchemy, SQLite |
| **Password Security** | Werkzeug Security (`generate_password_hash`) |
| **Frontend UI** | Jinja2 Templates, HTML5, Vanilla CSS3, Bootstrap 5.3, Bootstrap Icons 1.11 |
| **Automated Testing** | Python `unittest` |

---

## Project Structure

```text
ATM-simulation/
├── app.py                      # Application entry point & Flask initialization
├── initial_data.py             # Database seeder (creates default Admin account)
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── application/
│   ├── config.py               # Application configuration classes
│   ├── database.py             # SQLAlchemy & LoginManager instances
│   ├── models.py               # Database models (User, Admin, PRO, BankAccount, etc.)
│   └── controllers.py          # Application routes and business logic
├── static/
│   └── style.css               # Design system styling & tokens
├── templates/
│   ├── base.html               # Shared layout & top navigation header
│   ├── home.html               # Portal landing page
│   ├── admin/                  # Admin management templates
│   ├── pro/                    # PRO workspace templates
│   ├── user/                   # User NetBanking templates
│   └── auth/                   # Login & registration templates
└── tests/
    └── test_e2e_lifecycle.py   # Isolated automated E2E lifecycle test suite
```

---

## Installation & Setup

### Prerequisites
* Python 3.9+ installed on your system.

### 1. Clone & Set Up Environment
```bash
# Clone the repository
git clone https://github.com/Dua-Saeed641/ATM-simulation.git
cd ATM-simulation

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Database Setup

Initialize the SQLite database and seed the default Administrator account:

```bash
python initial_data.py
```

*Default Admin Credentials:*
- **Email**: `admin@gmail.com`
- **Password**: `admin123`

---

## Running the Application

Start the local development server:

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:8080` (or `http://localhost:8080`).

---

## Testing

### Automated End-to-End Test Suite
The project includes a self-contained, isolated end-to-end integration test suite that executes the complete banking lifecycle on a temporary test database without altering your development data:

```bash
python tests/test_e2e_lifecycle.py
```

#### What the Test Suite Verifies:
1. **User Registration**: Verifies user creation and default `BankAccount` initialization.
2. **PRO Registration & Guards**: Verifies unapproved PRO access restrictions.
3. **Admin Approval & Code Generation**: Verifies PRO approval and employee code assignment (`EMP001`).
4. **PRO Assignment**: Verifies assigning a PRO to a user.
5. **Scheme Recommendation**: Verifies PRO scheme recommendation and duplicate prevention.
6. **Scheme Acceptance**: Verifies `UserScheme.status == "Accepted"` and dynamic minimum balance linking.
7. **Deposits & Transactions**: Verifies ledger recording and balance updates.
8. **Dynamic Minimum Balance Enforcement**: Asserts that withdrawals leaving balance below scheme minimum fail, while valid withdrawals succeed.
9. **Account Status Enforcement**: Verifies frozen account transaction blocking.
10. **Security Boundaries**: Verifies cross-role route access prevention (403/302).

---

## Future Improvements

* Two-Factor Authentication (2FA) for sensitive banking transfers.
* Transaction PDF Statement Generation.
* Real-time WebSocket notifications for scheme recommendations.
* RESTful API endpoints for mobile client integration.
