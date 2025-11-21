# UNJobAtlas

A Django application built with Django 4.2 LTS.

## Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for PostgreSQL)

### Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL with Docker:
```bash
docker compose up -d
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:  
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see your application.

## Database

The project uses PostgreSQL 17 running in Docker. The database data is stored in `postgres_data/` directory (gitignored).

### Docker Commands

- Start database: `docker compose up -d`
- Stop database: `docker compose down`
- View logs: `docker compose logs -f db`
- Reset database: `docker compose down -v` (warning: deletes all data)

### Database Connection

Default connection settings (defined in `.env.example`):
- Host: localhost
- Port: 5432
- Database: unjobatlas
- User: unjobatlas
- Password: unjobatlas

## Project Structure

- `config/` - Project settings and configuration
- `core/` - Main application
- `manage.py` - Django management script
- `docker-compose.yml` - PostgreSQL database configuration
