# 📊 Strategy Performance Dashboard

A professional-grade web application built with **Python** and **Streamlit** to analyze, visualize, and export financial strategy performance data directly from Excel.

## 🚀 Live Access
**URL:** https://speedlab-strategies-reports.streamlit.app/
**Security:** Password protected via Streamlit Secrets.

## ✨ Key Features
* **Automated Metrics:** Instantly calculates Cumulative Return, Annualized Return, Volatility, Sharpe Ratio, and Maximum Drawdown.
* **Interactive Visualization:** Dynamic "Growth of 100" (NAV) line charts with adjustable date ranges.
* **Excel Integration:** Directly processes the `Monthly_returns` sheet from the `All_strategies_monthly_percentages.xlsx` workbook.
* **Professional PDF Export:** One-click generation of a PDF factsheet including performance statistics, the NAV chart, and a full monthly returns history table.
* **Cloud Hosted:** Fully deployed on Streamlit Community Cloud with automated updates via GitHub.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **Data Science:** Pandas, NumPy
* **Charts:** Matplotlib
* **PDF Engine:** FPDF2
* **Data Source:** Microsoft Excel (`.xlsx`)

## 📂 Project Structure
The repository is organized into the following essential components:

* **`Factsheet_webapp.py`**: The core application logic. It handles the user interface, password authentication, financial calculations, and PDF generation.
* **`All_strategies_monthly_percentages.xlsx`**: The primary database. The app reads the `Monthly_returns` sheet from this file to populate all charts and tables.
* **`requirements.txt`**: A configuration file that tells the cloud server which Python libraries (Streamlit, Pandas, FPDF2, etc.) are required to run the application.
* **`README.md`**: This documentation file, providing an overview and instructions for the project.

## 📋 How to Use
1. **Login:** Enter the authorized access code on the landing page.
2. **Select Strategy:** Use the sidebar dropdown to choose between different investment strategies.
3. **Adjust Dates:** Fine-tune the "Start" and "End" dates to analyze specific performance periods.
4. **Download:** Click the **"Prepare PDF Report"** button to generate a snapshot, then click **"Download PDF"**.

## 🔄 Updating Data
To update the dashboard with new monthly returns:
1. Update the local `All_strategies_monthly_percentages.xlsx` file.
2. Upload/Commit the new version of the file to the GitHub repository.
3. The live app will automatically refresh with the new data.

Go to your GitHub repo: kkspeedlab/flex-strategy-dashboard.