# Render Deployment Instructions

## 1. Push your code to a public Git repository (e.g., GitHub)

If not already done:
```bash
git init
git remote add origin https://github.com/yourusername/volby2025.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

## 2. Create a Render account
- Go to https://render.com and sign up (free tier is enough).

## 3. Create a new Web Service
- Click "New +" > "Web Service"
- Connect your GitHub repo and select `volby2025`
- For build and start commands, Render will use `render.yaml` automatically
- Set environment variables if needed (see `render.yaml`)

## 4. Deploy
- Click "Create Web Service"
- Wait for build and deployment to finish
- Visit the provided URL to see your app live

## Notes
- The backend (Flask app) will serve the frontend static files from `frontend/static` and templates from `frontend/templates`.
- The SQLite database (`database/volby.db`) will be ephemeral on Render free tier. For persistent data, use a managed database.
- Logs are available in the Render dashboard.

## Troubleshooting
- If you see errors, check the Render build logs and make sure all dependencies are in `requirements.txt`.
- For custom domains, follow Render's documentation.

---

For more info, see https://render.com/docs/deploy-flask
