# TransactHub — Transaction Management System

TransactHub is a full-stack web application designed to manage user transactions, calculate net balances, and maintain a real-time leaderboard ranking based on transaction activity. It provides a simple, interactive frontend combined with a robust Django-based backend.

## 🚀 Features

- **Transaction Management**: Submit credit and debit transactions with an idempotency key to prevent duplicates.
- **User Summaries**: View a specific user's total credits, total debits, net balance, and transaction count.
- **Real-Time Leaderboard**: Track user rankings based on their computed rank scores dynamically.
- **Responsive UI**: A modern, sleek vanilla HTML/CSS/JS frontend powered by Inter fonts.
- **Robust Backend**: Built with Django and Django REST Framework for scalability and reliability.

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3 (Custom Styling)
- Vanilla JavaScript
- Inter Font Family

**Backend:**
- Python 3.x
- Django (v5.2+)
- Django REST Framework (v3.15+)
- SQLite3 (Default database, can be configured for PostgreSQL/MySQL)
- `django-cors-headers`

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your machine:
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd intern_assignment
```

### 2. Backend Setup
Navigate to the `backend` directory and set up a virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- On **Windows**:
  ```bash
  .venv\Scripts\activate
  ```
- On **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```

Install dependencies:
```bash
pip install -r ../requirements.txt
```

Run database migrations:
```bash
python manage.py migrate
```

*(Optional)* Seed the database with initial data:
```bash
python seed_data.py
```

Start the development server:
```bash
python manage.py runserver
```
The backend server should now be running at `http://127.0.0.1:8000/`.

### 3. Frontend Setup
The frontend files are located in the `frontend` folder and the root URL of the Django backend is configured to serve `index.html` natively. You have two options to view the frontend:

**Option A (Through Django):**
Simply navigate to `http://127.0.0.1:8000/` in your browser while the Django server is running.

**Option B (Standalone / Live Server):**
You can serve the `frontend` directory using any static file server like VS Code's "Live Server" extension, or Python's built-in `http.server`:
```bash
cd ../frontend
python -m http.server 3000
```
Then open `http://127.0.0.1:3000/` in your browser.

## 🔌 API Endpoints

The API is served under the `/api/` prefix.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/transaction/` | `POST` | Create a new transaction (credit or debit). |
| `/api/summary/<str:user_id>/` | `GET` | Retrieve the transaction summary and balance for a specific user. |
| `/api/ranking/` | `GET` | Retrieve the top users sorted by their rank score. |

---

*This project was created as an intern assignment. Feel free to explore the code!*
