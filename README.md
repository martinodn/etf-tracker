# ETF Tracker & Portfolio 📈

A Streamlit application to track ETF values, visualize historical data, and manage a personal portfolio.

## Features

- **Portfolio Management**: Track your ETF purchases (Date, Price, Quantity).
- **Google Sheets Integration**: Data is stored securely in your private Google Sheet.
- **Real-time Data**: Uses Yahoo Finance API for current prices and historical data.
- **Interactive Dashboard**:
    - Comparative performance charts.
    - Daily/Monthly/Yearly change metrics.
    - Zoomable interactive charts (Plotly).
- **Security**: Password protected access.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - Create a `.streamlit/secrets.toml` file (see `secrets.toml.example` or deployment guide).
    - Add your Google Sheet URL and Service Account credentials.
    - Set an `APP_PASSWORD`.

3.  **Run Locally**:
    ```bash
    streamlit run app.py
    ```
