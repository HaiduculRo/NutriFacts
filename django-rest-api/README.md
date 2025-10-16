# Django REST API Project

This project is a Django REST API built using Django Rest Framework and PostgreSQL as the database. It provides a structured way to create and manage a RESTful API.

## Project Structure

```
django-rest-api
├── api                # Contains the API application
│   ├── __init__.py
│   ├── admin.py      # Admin site configuration
│   ├── apps.py       # Application configuration
│   ├── models.py     # Data models
│   ├── serializers.py # Serializers for converting models to JSON
│   ├── tests.py      # Tests for the API
│   ├── urls.py       # URL routing for the API
│   └── views.py      # View functions or classes
├── config             # Project configuration
│   ├── __init__.py
│   ├── asgi.py       # ASGI entry point
│   ├── settings.py   # Project settings and configuration
│   ├── urls.py       # URL routing for the entire project
│   └── wsgi.py       # WSGI entry point
├── core               # Core utilities and management commands
│   ├── __init__.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       └── __init__.py
│   └── utils.py      # Utility functions
├── manage.py          # Command-line utility for the project
├── requirements.txt   # Project dependencies
├── .env               # Environment variables
├── .gitignore         # Git ignore file
└── README.md          # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd django-rest-api
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your PostgreSQL database and update the `.env` file with your database credentials.

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Start the development server:
   ```
   python manage.py runserver
   ```

## Usage

You can access the API at `http://127.0.0.1:8000/api/`. Use tools like Postman or curl to interact with the API endpoints.

## Testing

To run the tests for the API, use the following command:
```
python manage.py test api
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.