# alx_travel_app_0x00

This project is part of the **ALX Backend Specialization**.

## 📌 **Project Description**

A Django REST API for a travel app that manages listings, bookings, and reviews. It also includes database seeding functionality for development and testing.

---

## 🚀 **Features**

✅ Defines database models for:
- Listings
- Bookings
- Reviews

✅ Serializers for API data representation:
- ListingSerializer
- BookingSerializer

✅ Management command:
- `seed`: seeds the database with sample listings data

✅ Uses Django REST Framework for serialization and API support.

---

## 💻 **Setup Instructions**

1. **Clone the repository**

```bash
git clone <repository-url>
cd alx_travel_app_0x00/alx_travel_app

    Create a virtual environment and activate it

python3 -m venv venv
source venv/bin/activate

    Install dependencies

pip install -r requirements.txt

    Run migrations

python manage.py makemigrations
python manage.py migrate

    Seed the database with sample data

python manage.py seed

    Run the development server

python manage.py runserver

🗃️ Project Structure

alx_travel_app_0x00/
└── alx_travel_app/
    ├── manage.py
    ├── alx_travel_app/
    │   └── settings.py
    └── listings/
        ├── models.py
        ├── serializers.py
        └── management/
            └── commands/
                └── seed.py

📝 Models Overview
Listing

    title

    description

    price

Booking

    listing (ForeignKey to Listing)

    user

    start_date

    end_date

Review

    listing (ForeignKey to Listing)

    user

    rating

    comment

🔧 Management Commands

    seed: seeds the database with dummy listings data for testing.

Example:

python manage.py seed

✨ Author

    ALX Backend Engineering

    Implemented by [Brian Name]

📜 License
