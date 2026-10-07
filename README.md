# CivicAI

Smart civic complaint management MVP built from the provided product requirements. Citizens submit reports manually with a photo, location, title, description, category, and severity.

## Run locally

Backend (FastAPI + Supabase PostgreSQL):

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`.

Create a citizen account from the registration page. No demo credentials are shipped with the application.

Set `DATABASE_URL` to your Supabase PostgreSQL connection string before starting the backend. Docker Compose includes a PostgreSQL service for local container testing.

AI is intentionally not part of this MVP. The citizen enters and reviews all complaint details manually.
