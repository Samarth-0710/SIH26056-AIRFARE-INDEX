# How to Run the SIH26056 Backend Server

## 1. Open PowerShell in the backend folder

```powershell
cd "C:\Users\Admin\Desktop\Projects\SIH Real-Time Airfare Price Index\SIH26056-AIRFARE-INDEX\backend"
```

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install backend packages

```powershell
python -m pip install -r requirements.txt
```

## 4. Create the environment file

```powershell
Copy-Item .env.example .env
```

## 5. Configure the database connection

Open `.env` and update the PostgreSQL password:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/airfare_index
API_TITLE=SIH26056 Airfare Price Index API
ENVIRONMENT=development
```

Replace `YOUR_POSTGRES_PASSWORD` with the password used for PostgreSQL/pgAdmin.

## 6. Create the database tables

In pgAdmin, select the `airfare_index` database and open **Tools > Query Tool**.

Open this file, copy its contents into Query Tool, and execute it using **F5**:

`database/migrations/001_initial_schema.sql`

## 7. Start the backend server

From the `backend` folder, run:

```powershell
uvicorn app.main:app --reload
```

## 8. Open the API

- API check: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Swagger documentation: http://127.0.0.1:8000/docs

## Stop the server

In PowerShell, press `Ctrl + C`.
