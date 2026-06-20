# GrainLab: Food Science Compiler for Home Bakers

GrainLab is a fail-safe, outcome-driven food-science compiler and Baker's Math recipe scaling engine optimized for home bakers using fresh-milled whole grains.

## 🚀 Quick Start

To run the application locally in 1-click using Docker Compose:
```bash
docker compose up --build
```

Alternatively, to run it natively using Python:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
3. Seed the database and bootstrap the default superuser:
   ```bash
   python manage.py seed_db
   ```
4. Run the development server:
   ```bash
   python manage.py runserver 8000
   ```

## 🌐 Local URL & Port
* Docker Compose local address: [http://localhost:8005](http://localhost:8005) (configured dynamically via `LOCAL_PORT` in `.env`)
* Native local address: [http://localhost:8000](http://localhost:8000)

## 🔑 Default Developer Credentials
* Username: `admin`
* Password: `adminpass123` (or customize via `SUPERUSER_PASSWORD` in `.env`)
