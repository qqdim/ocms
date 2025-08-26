# Online Course Management System (OCMS) API

This repository contains the backend API for an Online Course Management System, built with Django and Django REST Framework. It provides a full-featured, role-based system for managing courses, lectures, assignments, and grades.

## Features

  * **Role-Based Permissions:** Clear separation of capabilities for **Teachers** and **Students**.
  * **Authentication:** Secure user registration and JWT-based authentication.
  * **Course Management:** Full CRUD operations for courses, lectures, and homework assignments.
  * **Grading System:** Functionality for homework submission, grading, and commenting.
  * **API Documentation:** Auto-generated OpenAPI (Swagger) schema for easy API exploration.

-----

## Tech Stack

  * **Backend:** Django, Django REST Framework
  * **Database:** PostgreSQL
  * **Authentication:** `djangorestframework-simplejwt`
  * **API Schema:** `drf-spectacular`
  * **Dependency Management:** `uv` & `pyproject.toml`
  * **Code Quality:** `Ruff` linter and formatter

-----

## Getting Started

### Prerequisites

  * Python 3.12+
  * PostgreSQL
  * `uv` (recommended)

### Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/qqdim/ocms.git
    cd <project-folder>
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate # or .\.venv\Scripts\activate on Windows
    ```

3.  **Install dependencies:**
    The project uses `pyproject.toml` to manage dependencies.

    ```bash
    uv pip install -e .[dev]
    ```

4.  **Configure the environment:**

      - Set up a PostgreSQL database and user.
      - Create a `.env` file in the root directory (you can copy `.env.example` if provided).
      - Fill in your database credentials and a `SECRET_KEY`.

5.  **Run database migrations:**

    ```bash
    python src/manage.py migrate
    ```

6.  **Start the development server:**

    ```bash
    python src/manage.py runserver
    ```

The API will be available at `http://127.0.0.1:8000/`.

-----

## API Documentation

Once the server is running, the auto-generated API documentation can be accessed at:

  * **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
  * **Schema:** `http://127.0.0.1:8000/api/schema/`