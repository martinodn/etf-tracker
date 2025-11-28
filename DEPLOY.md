# Deployment Guide: Streamlit Cloud 🚀

Follow these steps to deploy your ETF Tracker to Streamlit Cloud.

## 1. Prepare your Repository

1.  **Create a GitHub Repository**: Go to GitHub and create a new repository (e.g., `etf-tracker`).
2.  **Push your code**:
    ```bash
    cd /path/to/etf_tracker
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/etf-tracker.git
    git push -u origin main
    ```
    *(Note: The `.gitignore` file ensures your secrets are NOT uploaded)*

## 2. Deploy on Streamlit Cloud

1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your repository (`etf-tracker`), branch (`main`), and main file (`app.py`).
4.  Click **"Deploy!"**.

## 3. Configure Secrets (Crucial!) 🔑

Your app will fail initially because it doesn't have the secrets (Google credentials, password, etc.). You need to add them manually in the Streamlit Cloud dashboard.

1.  In your deployed app, click the **Settings** menu (three dots in top right) -> **Settings**.
2.  Go to the **"Secrets"** tab.
3.  Copy the content of your local `.streamlit/secrets.toml` file.
4.  Paste it into the text area. It should look like this:

```toml
PORTFOLIO_SHEET_URL = "https://docs.google.com/spreadsheets/d/..."
APP_PASSWORD = "your_secure_password"

[gcp_service_account]
type = "service_account"
project_id = "..."
...
```

5.  Click **"Save"**.

The app should automatically restart and work! 🎉
