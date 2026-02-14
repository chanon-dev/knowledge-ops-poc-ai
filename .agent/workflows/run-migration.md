---
description: Run database migrations for the backend
---
1. Navigate to the backend directory

   ```bash
   cd backend
   ```

2. Activate the virtual environment

   ```bash
   # Check if .venv exists, if not create it
   if [ ! -d ".venv" ]; then
       python3 -m venv .venv
   fi
   source .venv/bin/activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Run Alembic upgrade

   ```bash
   # Ensure DB is running first (docker-compose up -d)
   alembic upgrade head
   ```
