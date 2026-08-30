# Deploying MenuMate (TableTap) to Render + Neon (Free)

## 1. Create a free Postgres database on Neon
1. Go to https://neon.tech and sign up.
2. Create a new project.
3. Copy the connection string shown (starts with `postgresql://...`).

## 2. Push this project to GitHub
Make sure these changed/added files are committed:
- `Pipfile` (now includes dj-database-url, psycopg2-binary, gunicorn, whitenoise, pillow)
- `tabletap/settings.py` (now reads SECRET_KEY, DEBUG, DATABASE_URL from environment)
- `build.sh` (new)
- `.env.example` (new, for reference only — do not commit a real `.env`)

Run locally once to refresh the lockfile before pushing:
```bash
pipenv lock
```

## 3. Create the Web Service on Render
1. Go to https://render.com, sign up, connect your GitHub account.
2. New + -> Web Service -> select this repo.
3. Settings:
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn tabletap.wsgi:application`
4. Add Environment Variables:
   - `SECRET_KEY` — generate a fresh one (e.g. https://djecrety.ir/), don't reuse the old exposed one
   - `DEBUG` — `False`
   - `DATABASE_URL` — the Neon connection string from step 1
   - `PYTHON_VERSION` — `3.13.0`
5. Click **Create Web Service**.

Render will run `build.sh` (installs deps, runs collectstatic, runs migrations) and then start the app with gunicorn. You'll get a live URL like `https://menumate.onrender.com`.

## 4. Create a superuser (to log into the staff dashboard)
From Render's dashboard, open a **Shell** for your service and run:
```bash
python manage.py createsuperuser
```

## Important security note
The original `settings.py` had a real MySQL database password committed in plaintext
(`315f3949fcc64540c4152878`) and a hardcoded Django `SECRET_KEY`. Both have been moved to
environment variables in this update. If that MySQL database is still live and using that
password, you should rotate/change it, since it was exposed in this repository.
