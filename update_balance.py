from app import app
from application.database import db
from application.models import BankAccount

with app.app_context():
    BankAccount.query.update(
        {BankAccount.minimum_balance: 1000.0}
    )
    db.session.commit()

print("Minimum balances updated successfully.")