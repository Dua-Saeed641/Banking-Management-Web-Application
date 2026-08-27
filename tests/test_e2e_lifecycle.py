import os
import sys
import unittest
from werkzeug.security import generate_password_hash

# Ensure application root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from application.database import db
from application.models import Admin, User, PRO, BankAccount, BankingScheme, UserScheme, Transaction


class TestE2ELifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure isolated test database
        cls.test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_database.db'))
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{cls.test_db_path}"
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test_secret_key'

        cls.app_ctx = app.app_context()
        cls.app_ctx.push()

        db.create_all()

        # Seed initial admin account
        admin = Admin(
            admin_name="System Admin",
            admin_email="admin@bank.com",
            admin_password=generate_password_hash("Admin@123"),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_ctx.pop()
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def test_01_full_banking_lifecycle(self):
        """
        Executes complete end-to-end banking lifecycle:
        User Reg -> PRO Reg -> Admin Approval -> PRO Assignment -> Deposit -> Scheme Rec ->
        Scheme Accept -> Dynamic Min Balance Withdrawal -> Transaction Verification ->
        Account Freezing -> Access Controls.
        """
        # Create distinct test clients for different user roles
        admin_client = app.test_client()
        pro_client = app.test_client()
        user_client = app.test_client()
        anonymous_client = app.test_client()

        # Test Unauthenticated Access Guard at the very start
        res_anon_initial = anonymous_client.get('/user/dashboard', follow_redirects=False)
        self.assertEqual(res_anon_initial.status_code, 302)

        # Step 1: Register User
        res_user_reg = user_client.post('/register/user', data={
            'name': 'Dua Saeed',
            'email': 'dua@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res_user_reg.status_code, 200)

        # DB Assertion: User and BankAccount created with default minimum balance
        user = User.query.filter_by(email='dua@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Dua Saeed')
        
        account = BankAccount.query.filter_by(user_id=user.user_id).first()
        self.assertIsNotNone(account)
        self.assertEqual(account.balance, 0.0)
        self.assertEqual(account.status, 'Active')
        self.assertEqual(account.minimum_balance, 1000.0) # Default minimum

        # Step 2: Register PRO
        res_pro_reg = pro_client.post('/register/pro', data={
            'name': 'Alex Officer',
            'email': 'alex@bank.com',
            'password': 'Password@123',
            'contact_number': '9876543210',
            'experience': '5'
        }, follow_redirects=True)
        self.assertEqual(res_pro_reg.status_code, 200)

        pro = PRO.query.filter_by(email='alex@bank.com').first()
        self.assertIsNotNone(pro)
        self.assertFalse(pro.is_approved)

        # Unapproved PRO cannot access dashboard
        res_unapproved_pro_dash = pro_client.get('/pro/dashboard')
        self.assertIn(res_unapproved_pro_dash.status_code, [403, 302])

        # Step 3: Admin Login & PRO Approval
        res_admin_login = admin_client.post('/login/admin', data={
            'email': 'admin@bank.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(res_admin_login.status_code, 200)

        res_approve = admin_client.post(f'/admin/pro-requests/{pro.pro_id}/approve', follow_redirects=True)
        self.assertEqual(res_approve.status_code, 200)

        # DB Assertion: PRO is approved and employee code generated
        db.session.refresh(pro)
        self.assertTrue(pro.is_approved)
        self.assertIsNotNone(pro.employee_code)
        self.assertTrue(pro.employee_code.startswith('EMP'))

        # Step 4: Admin assigns PRO to User
        res_assign = admin_client.post(f'/admin/users/{user.user_id}/assign-pro', data={
            'pro_id': str(pro.pro_id)
        }, follow_redirects=True)
        self.assertEqual(res_assign.status_code, 200)

        # DB Assertion: User assigned PRO updated
        db.session.refresh(user)
        self.assertEqual(user.assigned_pro_id, pro.pro_id)

        # Step 5: Admin creates a Banking Scheme requiring ₹3,000 min balance
        scheme = BankingScheme(
            scheme_name="Wealth Premium Plan",
            description="High yield savings with priority banking support.",
            minimum_balance_required=3000.0,
            interest_rate=6.5,
            status="Active"
        )
        db.session.add(scheme)
        db.session.commit()

        # Step 6: User Deposits ₹10,000 so account balance satisfies scheme minimum
        res_user_login = user_client.post('/login/user', data={
            'email': 'dua@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res_user_login.status_code, 200)

        res_deposit = user_client.post('/user/deposit', data={
            'amount': '10000.00'
        }, follow_redirects=True)
        self.assertEqual(res_deposit.status_code, 200)

        # DB Assertion: Balance updated & Transaction recorded
        db.session.refresh(account)
        self.assertEqual(account.balance, 10000.0)

        txn_deposit = Transaction.query.filter_by(account_id=account.account_id, transaction_type='Deposit').first()
        self.assertIsNotNone(txn_deposit)
        self.assertEqual(txn_deposit.amount, 10000.0)
        self.assertEqual(txn_deposit.balance_after_transaction, 10000.0)
        self.assertIsNotNone(txn_deposit.transaction_date)

        # Step 7: PRO Login & Recommend Scheme to Customer
        res_pro_login = pro_client.post('/login/pro', data={
            'email': 'alex@bank.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res_pro_login.status_code, 200)

        res_recommend = pro_client.post(f'/pro/customers/{user.user_id}/recommend-scheme', data={
            'scheme_id': str(scheme.scheme_id)
        }, follow_redirects=True)
        self.assertEqual(res_recommend.status_code, 200)

        # DB Assertion: Recommendation created with status Pending
        rec = UserScheme.query.filter_by(user_id=user.user_id, scheme_id=scheme.scheme_id).first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.status, 'Pending')

        # Duplicate recommendation should be blocked
        res_dup_rec = pro_client.post(f'/pro/customers/{user.user_id}/recommend-scheme', data={
            'scheme_id': str(scheme.scheme_id)
        }, follow_redirects=True)
        self.assertIn(b"already", res_dup_rec.data.lower())

        # Step 8: User Accept Scheme
        user_client.post('/login/user', data={
            'email': 'dua@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)

        res_accept = user_client.post(f'/user/schemes/{rec.user_scheme_id}/accept', follow_redirects=True)
        self.assertEqual(res_accept.status_code, 200)

        # DB Assertion: UserScheme status == Accepted & BankAccount.scheme_id linked
        db.session.refresh(rec)
        db.session.refresh(account)
        self.assertEqual(rec.status, 'Accepted')
        self.assertEqual(account.scheme_id, scheme.scheme_id)

        # Step 9: Attempt invalid withdrawal (leaving balance < scheme minimum requirement of ₹3,000)
        # 10,000 - 8,000 = 2,000 (< 3,000 min) -> MUST FAIL
        res_withdraw_invalid = user_client.post('/user/withdraw', data={
            'amount': '8000.00'
        }, follow_redirects=True)
        self.assertIn(b"minimum balance", res_withdraw_invalid.data.lower())
        db.session.refresh(account)
        self.assertEqual(account.balance, 10000.0) # Balance unchanged

        # Step 10: Perform valid withdrawal (10,000 - 5,000 = 5,000 >= 3,000 min) -> MUST SUCCEED
        res_withdraw_valid = user_client.post('/user/withdraw', data={
            'amount': '5000.00'
        }, follow_redirects=True)
        self.assertEqual(res_withdraw_valid.status_code, 200)

        # DB Assertion: Balance updated & Transaction ledger verified
        db.session.refresh(account)
        self.assertEqual(account.balance, 5000.0)

        txn_withdraw = Transaction.query.filter_by(account_id=account.account_id, transaction_type='Withdrawal').first()
        self.assertIsNotNone(txn_withdraw)
        self.assertEqual(txn_withdraw.amount, 5000.0)
        self.assertEqual(txn_withdraw.balance_after_transaction, 5000.0)

        # Step 11: Admin freezes User account
        admin_client.post('/login/admin', data={
            'email': 'admin@bank.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        res_freeze = admin_client.post(f'/admin/users/{user.user_id}/account-status', data={
            'status': 'Frozen'
        }, follow_redirects=True)
        self.assertEqual(res_freeze.status_code, 200)

        # DB Assertion: Account status Frozen
        db.session.refresh(account)
        self.assertEqual(account.status, 'Frozen')

        # Frozen account cannot deposit or withdraw
        user_client.post('/login/user', data={
            'email': 'dua@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)

        res_frozen_dep = user_client.post('/user/deposit', data={'amount': '500.00'}, follow_redirects=True)
        self.assertIn(b"frozen", res_frozen_dep.data.lower())

        res_frozen_with = user_client.post('/user/withdraw', data={'amount': '500.00'}, follow_redirects=True)
        self.assertIn(b"frozen", res_frozen_with.data.lower())

        # Step 12: Security & Authorization Verification
        # User -> Admin route -> Blocked (403)
        res_user_to_admin = user_client.get('/admin/dashboard')
        self.assertEqual(res_user_to_admin.status_code, 403)

        # User -> PRO route -> Blocked (403)
        res_user_to_pro = user_client.get('/pro/dashboard')
        self.assertEqual(res_user_to_pro.status_code, 403)

        # PRO -> Admin route -> Blocked (403)
        res_pro_to_admin = pro_client.get('/admin/dashboard')
        self.assertEqual(res_pro_to_admin.status_code, 403)


        # Step 13: Admin edits user balance and profile
        admin_client.post('/login/admin', data={
            'email': 'admin@bank.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        res_admin_edit = admin_client.post(f'/admin/users/{user.user_id}/edit', data={
            'name': 'Dua Saeed Updated',
            'email': 'dua_updated@example.com',
            'balance': '15000.00'
        }, follow_redirects=True)
        self.assertEqual(res_admin_edit.status_code, 200)
        db.session.refresh(user)
        db.session.refresh(account)
        self.assertEqual(user.name, 'Dua Saeed Updated')
        self.assertEqual(account.balance, 15000.0)

        # Unfreeze account for transactions
        admin_client.post(f'/admin/users/{user.user_id}/account-status', data={'status': 'Active'}, follow_redirects=True)
        db.session.refresh(account)
        self.assertEqual(account.status, 'Active')

        # Sequential withdrawals test
        user_client.post('/login/user', data={'email': 'dua_updated@example.com', 'password': 'Password@123'}, follow_redirects=True)
        user_client.post('/user/withdraw', data={'amount': '1000.00'}, follow_redirects=True)
        db.session.refresh(account)
        self.assertEqual(account.balance, 14000.0)

        user_client.post('/user/withdraw', data={'amount': '500.00'}, follow_redirects=True)
        db.session.refresh(account)
        self.assertEqual(account.balance, 13500.0)

        # Step 14: Over-limit transaction rejection
        res_over_deposit = user_client.post('/user/deposit', data={'amount': '200000000.00'}, follow_redirects=True)
        self.assertIn(b"maximum", res_over_deposit.data.lower())


if __name__ == '__main__':
    unittest.main()
