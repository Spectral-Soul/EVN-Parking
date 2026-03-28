# EVNPARK - Smart EV Parking System

EVNPARK is a production-grade EV smart parking built with Flask, SQLite, Vanilla HTML/JS, and Tailwind CSS. It supports dynamic pricing, interactive graph-based Map navigation, and Gemini AI.

## Project Architecture
- **Backend:** Flask / Python 3
- **Database:** SQLite (file-based `evnpark.db`)
- **Frontend:** Glassmorphism UI (Tailwind CSS, HTML Templates, Vanilla JS)
- **AI Integration:** Google Gemini
- **Scale:** Multi-floor logic handling 200+ distinct parking slots configured as an algorithmic routing graph.

## Step-by-Step Run Instructions

### 1. Requirements
- Python 3.8+
- pip (Python package manager)

### 2. Install Dependencies
Open your terminal in the `Anti park` directory and install the necessary Python packages:
```bash
pip install flask werkzeug
```
*(No need to install sqlite3 or json; they are built into Python).*

### 3. Start the Server
Run the Flask application directly:
```bash
python app.py
```
*Note: On the first run, the SQLite database (`evnpark.db`) will be automatically created and seeded with 2 admin/test users, 2 complete floor layouts, 200 parking slots, and an underlying navigation grid with weights.*

### 4. Access the Application
Open your modern web browser (Chrome, Firefox, Safari) and navigate to:
**http://127.0.0.1:5000**

### 5. Test Credentials
During initialization, the database seeds the following credentials:
- **Admin User:**
  - Username: `admin`
  - Password: `admin123`
- **Standard User:**
  - Username: `user`
  - Password: `user123`

You can also register a new account from the `/login` logic.

## Usage Guide
1. **Interactive Map:** Zoom with your mouse wheel and drag to pan around. Click on green (Available) slots to view details or book them.
2. **Booking:** Estimated pricing scales based on the current time (Dynamic Peak/Night pricing). Booking dynamically calculates the INR value.
3. **AI Assistant:** Click the floating indigo icon on the bottom right to open the AI Chat. It integrates Gemini to help answer questions.
4. **Admin Panel:** Login as `admin`, browse to the Admin Dashboard from the sidebar to view Chart.js revenue maps and current occupancy.
