# CivicConnect Render monolith

The project deploys as one Docker web service:

```text
Browser → Render Web Service → FastAPI
                              ├── /api/v1/* API
                              ├── /uploads/* complaint images
                              └── React/Vite SPA
```

## Deploy

1. Push the repository to GitHub.
2. In Render choose **New → Blueprint**.
3. Select the repository and branch `main`.
4. Render reads `render.yaml` and builds `Dockerfile`.
5. Set `DATABASE_URL` in Render to the Supabase PostgreSQL connection string.
6. Check `/health` after the deploy. It now verifies the database connection.

Production uses Supabase PostgreSQL for complaint data. The Render persistent disk at `/var/data` stores uploaded images only. A paid Render plan is required for that disk. Production refuses to start with SQLite, preventing a deploy from silently creating a new empty database.

## Local development

```powershell
# terminal 1
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# terminal 2
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/uploads` to FastAPI.

## Local Docker test

```powershell
docker build -t civicconnect .
docker run --rm -p 10000:10000 `
  -e SECRET_KEY="local-development-secret-change-me" `
  -e DATABASE_URL="sqlite:////var/data/civicconnect.db" `
  civicconnect
```
