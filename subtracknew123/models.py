"""
Database models for SubTrack application.
Defines User and Subscription tables with relationships.
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    User model for authentication and profile management.
    Stores user credentials and budget information.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_reminders = db.Column(db.Boolean, default=True)
    budget_alerts = db.Column(db.Boolean, default=True)
    monthly_summary = db.Column(db.Boolean, default=False)
    new_subscription = db.Column(db.Boolean, default=True)
    
    # Relationship: one user can have many subscriptions
    subscriptions = db.relationship('Subscription', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the provided password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_total_monthly_cost(self):
        """Calculate total monthly subscription costs for this user."""
        return sum(sub.monthly_price for sub in self.subscriptions)
    
    def get_remaining_budget(self):
        """Calculate remaining budget after subscriptions."""
        return self.monthly_budget - self.get_total_monthly_cost()
    
    def __repr__(self):
        return f'<User {self.email}>'


class Subscription(db.Model):
    """
    Subscription model for tracking paid services.
    Each subscription belongs to one user.
    """
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monthly_price = db.Column(db.Float, nullable=False)
    billing_date = db.Column(db.Integer, nullable=False)  # Day of month (1-31)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_next_payment_date(self):
        """
        Calculate the next payment date based on billing_date.
        Returns a formatted string.
        """
        from datetime import datetime, timedelta
        from calendar import monthrange
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # If billing date hasn't occurred this month yet
        if now.day < self.billing_date:
            next_month = current_month
            next_year = current_year
        else:
            # Move to next month
            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year
        
        # Handle months with fewer days (e.g., Feb 30 -> Feb 28/29)
        max_day = monthrange(next_year, next_month)[1]
        actual_day = min(self.billing_date, max_day)
        
        next_date = datetime(next_year, next_month, actual_day)
        return next_date.strftime('%B %d, %Y')
    
    def __repr__(self):
        return f'<Subscription {self.name} - ${self.monthly_price}>'
