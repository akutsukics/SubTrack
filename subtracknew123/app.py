"""
Main Flask application file for SubTrack.
Handles routing, authentication, and business logic.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from models import db, User, Subscription
from config import Config
from functools import wraps
from datetime import datetime, timedelta
from calendar import monthrange
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)


with app.app_context():
    db.create_all()



def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



def send_subscription_email(user_email, subscription_name, monthly_price):
    """
    Send confirmation email when a new subscription is added.
    Uses Flask-Mail to send via configured SMTP server.
    """
    try:
        msg = Message(
            subject='New Subscription Added - SubTrack',
            recipients=[user_email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #2563EB;">Subscription Confirmed!</h2>
                    <p>Hi there,</p>
                    <p>Your subscription to <strong>{subscription_name}</strong> has been successfully added to SubTrack.</p>
                    <p><strong>Monthly Cost:</strong> ${monthly_price:.2f}</p>
                    <p>We'll help you keep track of this subscription and notify you before upcoming payments.</p>
                    <br>
                    <p>Best regards,<br>The SubTrack Team</p>
                </body>
            </html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def send_payment_reminder(user, subscription, days_until):
    """
    Send payment reminder email to user.
    Called when a subscription payment is due in 3 days.
    """
    try:
        msg = Message(
            subject=f'Payment Reminder: {subscription.name} due in {days_until} days',
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #F8FAFC;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563EB; margin-bottom: 20px;">💳 Payment Reminder</h2>
                        <p style="color: #1E293B; font-size: 16px;">Hi there,</p>
                        <p style="color: #1E293B; font-size: 16px;">
                            Your subscription to <strong>{subscription.name}</strong> will renew in <strong>{days_until} days</strong>.
                        </p>
                        
                        <div style="background-color: #EFF6FF; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563EB;">
                            <p style="margin: 5px 0; color: #1E293B;"><strong>Service:</strong> {subscription.name}</p>
                            <p style="margin: 5px 0; color: #1E293B;"><strong>Amount:</strong> ${subscription.monthly_price:.2f}</p>
                            <p style="margin: 5px 0; color: #1E293B;"><strong>Payment Date:</strong> {subscription.get_next_payment_date()}</p>
                        </div>
                        
                        <p style="color: #64748B; font-size: 14px;">
                            Make sure you have sufficient funds in your account to avoid payment failures.
                        </p>
                        
                        <p style="color: #64748B; font-size: 14px; margin-top: 30px;">
                            Best regards,<br>
                            The SubTrack Team
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"✓ Payment reminder sent to {user.email} for {subscription.name}")
        return True
    except Exception as e:
        print(f"✗ Error sending payment reminder: {str(e)}")
        return False


def send_budget_alert(user, total_spending, budget_limit, overage):
    """
    Send budget alert email when user exceeds their monthly budget.
    """
    try:
        msg = Message(
            subject='⚠️ Budget Alert: You have exceeded your monthly limit',
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #F8FAFC;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h2 style="color: #EF4444; margin-bottom: 20px;">⚠️ Budget Alert</h2>
                        <p style="color: #1E293B; font-size: 16px;">Hi there,</p>
                        <p style="color: #1E293B; font-size: 16px;">
                            Your subscription spending has exceeded your monthly budget limit.
                        </p>
                        
                        <div style="background-color: #FEF2F2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #EF4444;">
                            <p style="margin: 5px 0; color: #1E293B;"><strong>Monthly Budget:</strong> ${budget_limit:.2f}</p>
                            <p style="margin: 5px 0; color: #1E293B;"><strong>Current Spending:</strong> ${total_spending:.2f}</p>
                            <p style="margin: 5px 0; color: #EF4444; font-size: 18px; font-weight: bold;">
                                <strong>Over Budget:</strong> ${overage:.2f}
                            </p>
                        </div>
                        
                        <p style="color: #64748B; font-size: 14px;">
                            Consider reviewing your subscriptions and canceling services you no longer use.
                        </p>
                        
                        <p style="color: #64748B; font-size: 14px; margin-top: 30px;">
                            Best regards,<br>
                            The SubTrack Team
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"✓ Budget alert sent to {user.email} (Over by ${overage:.2f})")
        return True
    except Exception as e:
        print(f"✗ Error sending budget alert: {str(e)}")
        return False


def send_monthly_summary(user, total_monthly, subscription_count, subscriptions_list):
    """
    Send monthly summary email with all subscription details and total spending.
    """
    try:
        subscription_rows = ""
        for sub in subscriptions_list:
            subscription_rows += f"""
                <tr style="border-bottom: 1px solid #E2E8F0;">
                    <td style="padding: 12px; color: #1E293B;">{sub.name}</td>
                    <td style="padding: 12px; color: #2563EB; font-weight: bold; text-align: right;">
                        ${sub.monthly_price:.2f}
                    </td>
                </tr>
            """
        
        msg = Message(
            subject=f'📊 Monthly Summary: ${total_monthly:.2f} in subscriptions',
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #F8FAFC;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563EB; margin-bottom: 20px;">📊 Monthly Subscription Summary</h2>
                        <p style="color: #1E293B; font-size: 16px;">Hi there,</p>
                        <p style="color: #1E293B; font-size: 16px;">
                            Here's your monthly subscription summary for {datetime.now().strftime('%B %Y')}.
                        </p>
                        
                        <div style="background-color: #EFF6FF; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                            <p style="color: #64748B; font-size: 14px; margin: 0;">Total Monthly Spending</p>
                            <p style="color: #2563EB; font-size: 36px; font-weight: bold; margin: 10px 0;">
                                ${total_monthly:.2f}
                            </p>
                            <p style="color: #64748B; font-size: 14px; margin: 0;">
                                {subscription_count} active subscription{'s' if subscription_count != 1 else ''}
                            </p>
                        </div>
                        
                        <h3 style="color: #1E293B; font-size: 18px; margin-top: 30px;">Your Subscriptions</h3>
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <thead>
                                <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                                    <th style="padding: 12px; text-align: left; color: #64748B; font-size: 12px; text-transform: uppercase;">Service</th>
                                    <th style="padding: 12px; text-align: right; color: #64748B; font-size: 12px; text-transform: uppercase;">Monthly Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                {subscription_rows}
                            </tbody>
                            <tfoot>
                                <tr style="background-color: #F8FAFC; font-weight: bold;">
                                    <td style="padding: 12px; color: #1E293B;">Total</td>
                                    <td style="padding: 12px; color: #2563EB; text-align: right; font-size: 18px;">
                                        ${total_monthly:.2f}
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                        
                        <div style="background-color: #ECFDF5; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10B981;">
                            <p style="color: #065F46; font-size: 14px; margin: 0;">
                                <strong>💡 Tip:</strong> Review unused subscriptions to save money. Even small savings add up!
                            </p>
                        </div>
                        
                        <p style="color: #64748B; font-size: 14px; margin-top: 30px;">
                            Best regards,<br>
                            The SubTrack Team
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"✓ Monthly summary sent to {user.email}")
        return True
    except Exception as e:
        print(f"✗ Error sending monthly summary: {str(e)}")
        return False



def check_payment_reminders():
    """
    Daily job: Check all subscriptions and send reminders for payments due in 3 days.
    This function should be called by the scheduler every day.
    """
    print(f"\n=== Running Payment Reminder Check at {datetime.now()} ===")
    
    with app.app_context():
        users = User.query.filter_by(payment_reminders=True).all()
        
        reminders_sent = 0
        
        for user in users:
            for subscription in user.subscriptions:
                now = datetime.now()
                current_year = now.year
                current_month = now.month
                billing_date = subscription.billing_date
                
                if now.day < billing_date:
                    next_month = current_month
                    next_year = current_year
                else:
                    if current_month == 12:
                        next_month = 1
                        next_year = current_year + 1
                    else:
                        next_month = current_month + 1
                        next_year = current_year
                
                max_day = monthrange(next_year, next_month)[1]
                actual_day = min(billing_date, max_day)
                
                next_date = datetime(next_year, next_month, actual_day)
                days_until = (next_date - now).days
                
                if days_until == 3:
                    if send_payment_reminder(user, subscription, days_until):
                        reminders_sent += 1
        
        print(f"✓ Payment reminder check complete. Sent {reminders_sent} reminder(s).\n")


def check_budget_alerts():
    """
    Daily job: Check all users' budgets and send alerts if spending exceeds limit.
    This function should be called by the scheduler every day.
    """
    print(f"\n=== Running Budget Alert Check at {datetime.now()} ===")
    
    with app.app_context():
        users = User.query.filter(
            User.budget_alerts == True,
            User.monthly_budget > 0
        ).all()
        
        alerts_sent = 0
        
        for user in users:
            total_spending = user.get_total_monthly_cost()
            budget_limit = user.monthly_budget
            
            if total_spending > budget_limit:
                overage = total_spending - budget_limit
                if send_budget_alert(user, total_spending, budget_limit, overage):
                    alerts_sent += 1
        
        print(f"✓ Budget alert check complete. Sent {alerts_sent} alert(s).\n")


def send_all_monthly_summaries():
    """
    Monthly job: Send summary email to all users with monthly_summary enabled.
    This function should be called by the scheduler once per month.
    """
    print(f"\n=== Running Monthly Summary Job at {datetime.now()} ===")
    
    with app.app_context():
        users = User.query.filter_by(monthly_summary=True).all()
        
        summaries_sent = 0
        
        for user in users:
            subscriptions = user.subscriptions
            total_monthly = user.get_total_monthly_cost()
            subscription_count = len(subscriptions)
            
            if send_monthly_summary(user, total_monthly, subscription_count, subscriptions):
                summaries_sent += 1
        
        print(f"✓ Monthly summary job complete. Sent {summaries_sent} summary email(s).\n")



def test_payment_reminders():
    """
    Manual trigger for testing payment reminders.
    Call this from a route or Python shell to test the email system.
    """
    with app.app_context():
        check_payment_reminders()


def test_budget_alerts():
    """
    Manual trigger for testing budget alerts.
    Call this from a route or Python shell to test the email system.
    """
    with app.app_context():
        check_budget_alerts()


def test_monthly_summary():
    """
    Manual trigger for testing monthly summaries.
    Call this from a route or Python shell to test the email system.
    """
    with app.app_context():
        send_all_monthly_summaries()


def get_days_until_payment(billing_date):
    """Calculate days until next payment based on billing date."""
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    if now.day < billing_date:
        next_month = current_month
        next_year = current_year
    else:
        if current_month == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = current_month + 1
            next_year = current_year
    
    max_day = monthrange(next_year, next_month)[1]
    actual_day = min(billing_date, max_day)
    
    next_date = datetime(next_year, next_month, actual_day)
    days_until = (next_date - now).days
    
    return days_until


def get_monthly_summary(user_id):
    """Get current month and year spending totals."""
    user = User.query.get(user_id)
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    
    monthly_total = sum(sub.monthly_price for sub in subscriptions)
    yearly_total = monthly_total * 12
    
    return {
        'monthly': monthly_total,
        'yearly': yearly_total,
        'count': len(subscriptions)
    }



@app.route('/')
def index():
    """Home page - redirects to dashboard if logged in, otherwise to login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        monthly_budget = request.form.get('monthly_budget', 0)
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))
        
        try:
            budget = float(monthly_budget) if monthly_budget else 0.0
            new_user = User(email=email, monthly_budget=budget)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Registration error: {str(e)}")
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash(f'Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Clear session and log out user."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))



@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - upcoming payments and monthly summary."""
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    
    upcoming = []
    for sub in subscriptions:
        days_until = get_days_until_payment(sub.billing_date)
        if days_until <= 30:
            upcoming.append({
                'subscription': sub,
                'days_until': days_until,
                'next_date': sub.get_next_payment_date()
            })
    
    upcoming.sort(key=lambda x: x['days_until'])
    
    summary = get_monthly_summary(user.id)
    
    budget_alert = summary['monthly'] > user.monthly_budget if user.monthly_budget > 0 else False
    
    return render_template(
        'dashboard.html',
        user=user,
        upcoming=upcoming,
        summary=summary,
        budget_alert=budget_alert
    )


@app.route('/subscriptions')
@login_required
def subscriptions():
    """Subscriptions management page - list, add, edit, delete."""
    user = User.query.get(session['user_id'])
    all_subscriptions = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.name).all()
    
    return render_template(
        'subscriptions.html',
        user=user,
        subscriptions=all_subscriptions
    )


@app.route('/subscription/add', methods=['POST'])
@login_required
def add_subscription():
    """Add a new subscription."""
    name = request.form.get('name', '').strip()
    monthly_price = request.form.get('monthly_price', '')
    billing_date = request.form.get('billing_date', '')
    
    if not name or not monthly_price or not billing_date:
        flash('All fields are required.', 'danger')
        return redirect(url_for('subscriptions'))
    
    try:
        price = float(monthly_price)
        day = int(billing_date)
        
        if price <= 0:
            flash('Price must be greater than 0.', 'danger')
            return redirect(url_for('subscriptions'))
        
        if day < 1 or day > 31:
            flash('Billing date must be between 1 and 31.', 'danger')
            return redirect(url_for('subscriptions'))
        
        new_subscription = Subscription(
            name=name,
            monthly_price=price,
            billing_date=day,
            user_id=session['user_id']
        )
        
        db.session.add(new_subscription)
        db.session.commit()
        
        user = User.query.get(session['user_id'])
        email_sent = send_subscription_email(user.email, name, price)
        
        if email_sent:
            flash(f'Subscription "{name}" added successfully!', 'success')
        else:
            flash(f'Subscription "{name}" added successfully!', 'success')
        
    except ValueError:
        flash('Invalid input. Please check your data.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        print(f"Add subscription error: {str(e)}")
    
    return redirect(url_for('subscriptions'))


@app.route('/subscription/delete/<int:subscription_id>', methods=['POST'])
@login_required
def delete_subscription(subscription_id):
    """Delete a subscription."""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    if subscription.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('subscriptions'))
    
    try:
        subscription_name = subscription.name
        db.session.delete(subscription)
        db.session.commit()
        flash(f'Subscription "{subscription_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the subscription.', 'danger')
        print(f"Delete subscription error: {str(e)}")
    
    return redirect(url_for('subscriptions'))


@app.route('/statistics')
@login_required
def statistics():
    """Statistics page - charts and annual cost breakdown."""
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    
    subscription_data = []
    for sub in subscriptions:
        subscription_data.append({
            'name': sub.name,
            'monthly': sub.monthly_price,
            'yearly': sub.monthly_price * 12
        })
    
    subscription_data.sort(key=lambda x: x['yearly'], reverse=True)
    
    monthly_totals = []
    total = sum(sub.monthly_price for sub in subscriptions)
    for i in range(6):
        date = datetime.now() - timedelta(days=30 * (5 - i))
        monthly_totals.append({
            'month': date.strftime('%b'),
            'total': total
        })
    
    return render_template(
        'statistics.html',
        user=user,
        subscription_data=subscription_data,
        monthly_totals=monthly_totals
    )


@app.route('/profile')
@login_required
def profile():
    """User profile page - settings and preferences."""
    user = User.query.get(session['user_id'])
    
    return render_template(
        'profile.html',
        user=user
    )


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile settings including budget and notification preferences."""
    user = User.query.get(session['user_id'])
    
    new_budget = request.form.get('monthly_budget', '')
    
    try:
        budget = float(new_budget) if new_budget else 0.0
        if budget < 0:
            flash('Budget cannot be negative.', 'danger')
            return redirect(url_for('profile'))
        
        user.monthly_budget = budget
        
        user.payment_reminders = 'payment_reminders' in request.form
        user.budget_alerts = 'budget_alerts' in request.form
        user.monthly_summary = 'monthly_summary' in request.form
        user.new_subscription = 'new_subscription' in request.form
        
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
    except ValueError:
        flash('Invalid budget amount.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating profile.', 'danger')
        print(f"Update profile error: {str(e)}")
    
    return redirect(url_for('profile'))



@app.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint for chart data."""
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    
    labels = [sub.name for sub in subscriptions]
    data = [sub.monthly_price for sub in subscriptions]
    
    return jsonify({
        'labels': labels,
        'data': data
    })


@app.route('/api/monthly-data')
@login_required
def monthly_data():
    """API endpoint for monthly spending data."""
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    
    total = sum(sub.monthly_price for sub in subscriptions)
    
    months = []
    totals = []
    
    for i in range(6):
        date = datetime.now() - timedelta(days=30 * (5 - i))
        months.append(date.strftime('%b'))
        totals.append(total)
    
    return jsonify({
        'months': months,
        'totals': totals
    })



def init_scheduler():
    """
    Initialize and start the background scheduler.
    Runs email notification jobs automatically.
    """
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        func=check_payment_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        id='payment_reminders',
        name='Send payment reminders',
        replace_existing=True
    )
    print("✓ Scheduled: Payment reminders (daily at 9:00 AM)")
    
    scheduler.add_job(
        func=check_budget_alerts,
        trigger=CronTrigger(hour=9, minute=0),
        id='budget_alerts',
        name='Send budget alerts',
        replace_existing=True
    )
    print("✓ Scheduled: Budget alerts (daily at 9:00 AM)")
    
    scheduler.add_job(
        func=send_all_monthly_summaries,
        trigger=CronTrigger(day=1, hour=9, minute=0),
        id='monthly_summary',
        name='Send monthly summaries',
        replace_existing=True
    )
    print("✓ Scheduled: Monthly summaries (1st of month at 9:00 AM)")
    
    scheduler.start()
    print("✓ Scheduler started successfully\n")
    
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler



@app.errorhandler(404)
def not_found(error):
    flash('Page not found.', 'warning')
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'danger')
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))



if __name__ == '__main__':
    init_scheduler()
    
    app.run(debug=True)
