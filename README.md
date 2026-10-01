# Honor Board — لوحة الشرف

Public honor board for **مركز الوهاب لتحفيظ القرآن الكريم**. One public page
shows the honored students of each branch; the center's staff manage branches
and students from the Django admin (fully in Arabic).

Stack: Python 3.12 · Django 5.2 LTS · PostgreSQL (Neon) · Gunicorn ·
WhiteNoise · Cloudinary (student photos) · plain Django templates + one CSS file.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit the values
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo    # 3 branches + 8 obviously fake students (local only)
python manage.py runserver
```

Open <http://127.0.0.1:8000/> (the board) and <http://127.0.0.1:8000/admin/>
(staff area). Run the tests with `python manage.py test`.

Without `DATABASE_URL` the app uses local SQLite. Without `CLOUDINARY_URL`
uploaded photos are stored in `media/`. Both are git-ignored.

## Getting the Neon DATABASE_URL

1. Sign up / log in at <https://neon.tech> and create a project.
2. Open the project dashboard and copy the **Connection string**, e.g.
   `postgresql://user:password@ep-xxxx-123456.eu-central-1.aws.neon.tech/neondb?sslmode=require`
3. Use it as the `DATABASE_URL` environment variable (the app also forces SSL
   on its own, keeps connections warm and health-checks them, which is what
   Neon's sleeping compute needs).

## Push to GitHub

```bash
git init
git add .
git commit -m "Honor Board: initial release"
git remote add origin git@github.com:USERNAME/honor-board.git
git push -u origin main
```

`.env`, `db.sqlite3`, `media/` and `staticfiles/` are git-ignored — no secrets
end up in the repository.

## Deploy on SnapDeploy

1. In SnapDeploy create a new app from the GitHub repository (Docker container).
2. Set the container port to **8000**.
3. Add the environment variables:

| Variable | Example | Notes |
|---|---|---|
| `SECRET_KEY` | `x8K...long random string...` | required |
| `DEBUG` | `False` | required in production |
| `ALLOWED_HOSTS` | `honor-board-xxxx.snapdeploy.app,yourdomain.com` | recommended (defaults to `*.snapdeploy.app`) |
| `CSRF_TRUSTED_ORIGINS` | `https://honor-board-xxxx.snapdeploy.app` | recommended (defaults to `https://*.snapdeploy.app`) |
| `DATABASE_URL` | `postgresql://...neon.tech/neondb?sslmode=require` | required (Neon) |
| `CLOUDINARY_URL` | `cloudinary://123456789012345:secret@cloud-name` | required for student photos |
| `DJANGO_SUPERUSER_USERNAME` | `admin` | optional (first deploy creates the user once) |
| `DJANGO_SUPERUSER_EMAIL` | `admin@example.com` | optional |
| `DJANGO_SUPERUSER_PASSWORD` | `strong password` | optional |

4. Deploy. During the build the image runs `collectstatic`; on startup the
   entrypoint runs `migrate`, creates the superuser (only if it does not exist
   yet) and starts Gunicorn (2 workers) on `0.0.0.0:8000`.
5. Open the app URL to see the board and `/admin/` to manage it.
6. Optionally point the platform's health check at `/health/` — it answers
   `200 ok` without touching the database.

Notes: free containers sleep when idle; the first request also wakes Neon's
database, which may add a second or two. Student photos live on Cloudinary
because the container filesystem is ephemeral.
