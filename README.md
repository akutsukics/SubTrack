# SubTrack - Modern Subscription Management Platform

A beautiful, modern web application for tracking and managing your subscriptions with a clean FinTech-inspired interface.

##  Design Features

- **Modern FinTech Aesthetic**: Clean, minimal design inspired by Rocket Money and modern SaaS platforms
- **Multi-Page Navigation**: Separate pages for Dashboard, Subscriptions, Statistics, and Profile
- **Strict Color Palette**: Primary Blue (#2563EB), Success Green (#10B981), Alert Red (#EF4444)
- **Card-Based Layout**: Clean grid system with rounded corners and soft shadows
- **Responsive Design**: Works beautifully on desktop, tablet, and mobile devices

##  Project Structure

```
SubTrack/
├── app.py                      # Main Flask application with all routes
├── models.py                   # Database models (User, Subscription)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── static/
│   └── css/
│       └── style.css          # Complete modern CSS design system
└── templates/
    ├── base.html              # Base template with navigation
    ├── dashboard.html         # Main dashboard page
    ├── subscriptions.html     # Subscription management page
    ├── statistics.html        # Charts and analytics page
    ├── profile.html           # User profile and settings
    ├── login.html             # Login page
    └── register.html          # Registration page
```

##  Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email (Optional)

Edit `config.py` to add your email settings:



**For Gmail:**
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'  # Generate from Google Account settings
```

### 3. Run the Application

```bash
python app.py
```

Visit: `http://127.0.0.1:5000`

##  Application Pages

### 1. Dashboard
- **Upcoming Payments**: Shows subscriptions due in the next 30 days with countdown
- **Monthly Summary**: Current month and yearly totals
- **Budget Status**: Visual budget tracking with alerts
- **Category Breakdown**: Spending analysis
- **Quick Actions**: Fast access to common tasks

### 2. Subscriptions
- **Add Subscription**: Modal form for adding new subscriptions
  - Service name
  - Monthly price
  - Billing day (1-31)
- **Subscriptions Table**: Full list with:
  - Monthly and annual costs
  - Next payment date
  - Quick delete action
- **Statistics**: Total count, average cost, min/max prices

### 3. Statistics
- **Monthly Spending Chart**: Line chart showing last 6 months (Chart.js)
- **Annual Cost Breakdown**: Ranked table with percentage bars
- **Key Insights**: Visual cards with important metrics
  - Total annual spending
  - Average monthly cost
  - Most expensive service
  - Potential savings

### 4. Profile
- **Account Information**: Email, join date, subscription count
- **Budget Settings**: Set monthly spending limit with visual progress bar
- **Notification Preferences**: Toggle switches for:
  - Payment reminders
  - Budget alerts
  - Monthly summary emails
  - New subscription confirmations
- **Spending Summary**: Quick overview cards
- **Account Actions**: Logout and account management

##  Design System

### Color Palette (Strict)
```css
Primary: #2563EB (Blue)
Primary Dark: #1E40AF
Success: #10B981 (Green)
Alert: #EF4444 (Red)
Background: #F8FAFC
Text Primary: #0F172A
Text Muted: #64748B
```

### Typography
- Font Family: Inter, Segoe UI, Roboto, system fonts
- Headings: 700 weight
- Body: 500 weight
- Muted text: 400 weight

### Components
- **Cards**: White background, soft shadows, rounded corners
- **Buttons**: Primary (blue), Secondary (outlined), Danger (red)
- **Forms**: Clean inputs with focus states
- **Tables**: Striped rows with hover effects
- **Modal**: Overlay with slide-up animation
- **Charts**: Chart.js with custom styling

## 🔧 Backend Features

### Authentication
- User registration with email validation
- Secure password hashing (Werkzeug)
- Session-based authentication
- Login/logout functionality

### Database (SQLite + SQLAlchemy)
- **Users Table**:
  - Email (unique)
  - Password hash
  - Monthly budget
  - Created timestamp
  
- **Subscriptions Table**:
  - Name
  - Monthly price
  - Billing date (1-31)
  - User relationship (foreign key)
  - Created timestamp

### Email Notifications
- Confirmation emails when adding subscriptions
- Flask-Mail integration
- HTML formatted emails
- SMTP configuration

### API Endpoints
- `/api/chart-data` - Pie chart data for expense distribution
- `/api/monthly-data` - Line chart data for monthly trends

## 📊 Key Features

### Dashboard
- ✅ Upcoming payments with days countdown
- ✅ Budget tracking with visual alerts
- ✅ Monthly and yearly spending totals
- ✅ Category breakdown analysis
- ✅ Quick action shortcuts

### Subscriptions
- ✅ Add subscriptions via modal form
- ✅ Full table view with sorting
- ✅ Monthly and annual cost calculations
- ✅ Next payment date calculation
- ✅ Delete functionality with confirmation
- ✅ Statistics summary cards

### Statistics
- ✅ Monthly spending line chart (Chart.js)
- ✅ Annual cost breakdown table
- ✅ Percentage visualization bars
- ✅ Ranked list by expense
- ✅ Key insights cards

### Profile
- ✅ Account information display
- ✅ Budget limit management
- ✅ Visual budget progress bar
- ✅ Notification preferences (UI ready)
- ✅ Spending summary cards

##  Security

- Password hashing with Werkzeug
- Session-based authentication
- `@login_required` decorator on protected routes
- SQL injection protection via SQLAlchemy ORM
- User ownership verification on CRUD operations

##  Navigation Highlights

The navigation bar automatically highlights the active page:
- Dashboard: 📊
- Subscriptions: 📋
- Statistics: 📈
- Profile: ⚙️

Clean, intuitive icons with clear labels for easy navigation.

##  Database Schema

```
users
├── id (Primary Key)
├── email (Unique, Indexed)
├── password_hash
├── monthly_budget
└── created_at

subscriptions
├── id (Primary Key)
├── name
├── monthly_price
├── billing_date (1-31)
├── user_id (Foreign Key → users.id)
└── created_at
```

##  Technologies Used

- **Backend**: Python 3.8+, Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Jinja2 templates
- **Charts**: Chart.js 4.4
- **Email**: Flask-Mail with SMTP
- **Security**: Werkzeug password hashing

##  Troubleshooting

### Database doesn't exist
The database is created automatically on first run. If you get errors:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### Email not sending
Email notifications will fail silently if not configured. Check:
1. SMTP settings in `config.py`
2. Network connectivity
3. Email credentials validity

### Port already in use
Change the port in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change port here
```

The codebase is structured for easy extension - add new features by:
1. Adding routes in `app.py`
2. Creating templates in `templates/`
3. Styling with existing CSS variables in `style.css`
