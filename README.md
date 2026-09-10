# GrainLab: Food Science Compiler for Home Bakers

GrainLab is an AI-powered, fail-safe food-science compiler and Baker's Math recipe scaling engine optimized for home bakers using fresh-milled whole grains.

## ✨ Features

- **AI-Powered Recipe Generation:** Powered by a local Gemma AI integration to dynamically generate precise timelines, sensory cues, and step-by-step instructions.
- **Hierarchical Yield Scaling:** Sophisticated yield management engine with archetype-specific terminology (e.g., Bagels, Pretzels, Cookies, Loaves, Pastries).
- **Detailed Preparatory Instructions:** Intelligent processing pipeline to inject precise physical preparatory requirements (size, shape, temperature constraints) for ingredients.
- **Baker's Math Engine:** Fully scales recipes cleanly based on target dough/batter weight limits and exact hydration calculations.

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

## 💾 Backup & Recovery

### Automated Backups
To generate a compressed, timestamped database backup, run the following Django command:
```bash
python manage.py backup_db
```
Backups are saved to the `backups/` directory (automatically git-ignored) and pruned automatically after 30 days.

### Database Restoration

#### SQLite (Default)
To restore a local SQLite database from a backup:
1. Locate your compressed backup file in `backups/` (e.g. `backup-20260622-235427.sql.gz`).
2. Decompress the backup file:
   ```bash
   # On Windows (PowerShell)
   Expand-Archive backups/backup-20260622-235427.sql.gz -DestinationPath .
   # On Linux/macOS
   gunzip -c backups/backup-20260622-235427.sql.gz > db.sqlite3
   ```
3. If using Windows/PowerShell without gzip extraction tools, you can rename the `.gz` target or extract it via standard tools like 7-Zip, replacing the root `db.sqlite3` file.

#### PostgreSQL
To restore a PostgreSQL database backup:
1. Decompress the sql backup file:
   ```bash
   gunzip -k backups/backup-20260622-235427.sql.gz
   ```
2. Run pg_restore (for custom format backups) or standard psql:
   ```bash
   pg_restore -h localhost -p 5432 -U grainlab_user -d grainlab backups/backup-20260622-235427.sql
   ```

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. 
See the [LICENSE](LICENSE) file for full details. This means you are free to share and modify the code, provided that any modified versions (including those provided as a service over a network) are also made open-source under the same terms.
