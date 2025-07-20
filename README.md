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
```

2. **Create a virtual environment and activate it**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Seed the database with sample data**

```bash
python manage.py seed
```

6. **Run the development server**

```bash
python manage.py runserver
```

---

## 🗃️ **Project Structure**

```
alx_travel_app_0x00/
├── README.md
└── alx_travel_app/
    ├── manage.py
    ├── alx_travel_app/
    │   └── alx_travel_app/
    │       ├── settings.py
    │       ├── urls.py
    │       ├── wsgi.py
    │       └── listings/
    │           ├── models.py
    │           ├── serializers.py
    │           ├── views.py
    │           ├── urls.py
    │           └── management/
    │               └── commands/
    │                   └── seed.py
    ├── static/
    └── media/
```

---

## 📝 **Models Overview**

### Listing
- `title` - String field for listing title
- `description` - Text field for detailed description  
- `price_per_night` - Decimal field for pricing
- `location` - String field for location

### Booking
- `listing` - ForeignKey to Listing
- `user` - String field for user identification
- `start_date` - Date field for booking start
- `end_date` - Date field for booking end

### Review
- `listing` - ForeignKey to Listing
- `user` - String field for user identification
- `rating` - Integer field for rating (1-5)
- `comment` - Text field for review comments

---

## 🔧 **Management Commands**

### seed
Seeds the database with dummy listings data for testing.

**Usage:**
```bash
python manage.py seed
```

---

## ✨ **Author**

- **ALX Backend Engineering**
- **Implemented by:** [Your Name]

---

## 📜 **License**

This project is part of the ALX Backend Specialization program.
