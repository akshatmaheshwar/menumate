# TableTap — Restaurant Menu & Ordering System

A full-stack web application built with Django that allows restaurants to manage their menus and lets customers place orders by scanning a QR code at their table. Built as a university project for INFS7202 at UQ.

## What It Does

**For restaurant owners (staff dashboard):**
- Register and manage your restaurant profile
- Create menus, categories, and menu items with images and prices
- View incoming orders in real time and update their status (Received → Processing → Completed)

**For customers (guest-facing ordering page):**
- Access the menu by visiting a URL tied to their table (e.g. `/order/<restaurant_id>/<table_number>/`)
- Browse menu items by category, add to cart, and place an order
- No login required for customers

## Tech Stack

- **Backend:** Python, Django
- **Database:** SQLite (via Django ORM)
- **Frontend:** HTML, CSS, JavaScript (Django templates)
- **Auth:** Django's built-in authentication with a custom User model
- **Image uploads:** Pillow

## Data Models

- `Restaurant` — name, description, contact info, number of tables
- `Menu` → `Category` → `MenuItem` (name, description, price, image)
- `Order` → `OrderItem` — linked to a restaurant and table number, with status tracking

## Project Structure

```
tabletap/              # Django project settings and URL config
tabletapapp/
├── models.py          # Restaurant, Menu, Category, MenuItem, Order, OrderItem
├── views.py           # REST-style views returning JSON + page views
├── urls.py            # URL routing
└── templates/
    ├── home.html      # Login / signup page
    ├── dashboard.html # Order management dashboard
    ├── menu.html      # Menu management (admin)
    ├── restaurant.html # Restaurant profile management
    └── order.html     # Customer-facing ordering page
```

## Setup

```bash
# Clone the repo
git clone https://github.com/akshatmaheshwar/tabletap.git
cd tabletap

# Install dependencies
pip install pipenv
pipenv install

# Run migrations
pipenv run python manage.py migrate

# Start the server
pipenv run python manage.py runserver
```

Then visit `http://localhost:8000/tabletapapp/` to get started.
