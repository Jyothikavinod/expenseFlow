# ExpenseFlow – Personal Finance Command Center

A local personal expense tracker built with Flask and SQLite. ExpenseFlow lets you add, view, edit, and delete expenses, filter records, and review a monthly spending summary — all without authentication or external services.

## Project Overview

ExpenseFlow is a lightweight web application for tracking daily spending. It stores data in a local SQLite database and runs entirely on your machine. The focus is on reliable CRUD operations, filtering, monthly analytics, and clear validation messages.

## Features

- **Add expenses** with title, amount, category, date, and optional note
- **View expenses** in a sortable table (newest first)
- **Edit expenses** with pre-filled forms and validation
- **Delete expenses** with a JavaScript confirmation dialog
- **Monthly summary dashboard** showing total spent, expense count, highest expense, and category breakdown
- **Combined filtering** by category, date range, and title search
- **Monthly budget tracker** — set a budget, view remaining amount, and get warnings when exceeded
- **Flash messages** for success, validation errors, and empty search results
- **Edge case handling** for empty inputs, invalid dates, future dates, SQL injection attempts, and more

## Technology Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python Flask            |
| Database  | SQLite                  |
| Frontend  | HTML, CSS, JavaScript   |

## Folder Structure

```text
expenseflow/
│
├── app.py
├── requirements.txt
├── README.md
├── database.db              # Created automatically on first run
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── add_expense.html
│   └── edit_expense.html
│
├── static/
│   ├── style.css
│   └── script.js
```

## Installation

1. Navigate to the project folder:

```bash
cd expenseflow
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the application:

```bash
python app.py
```

4. Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Assumptions

- Single-user local usage; no authentication is required.
- Currency is displayed in Indian Rupees (₹) for readability.
- Expense dates cannot be in the future.
- The monthly summary reflects the current calendar month based on the system date.
- SQLite is sufficient for local personal expense tracking.

## Design Decisions

- **Flask with server-rendered templates** keeps the stack simple and easy to evaluate.
- **Parameterized SQL queries** prevent SQL injection and keep database access straightforward.
- **Combined filters on the dashboard** allow category, date range, and title search to work together in one query.
- **Validation on both client and server** improves UX while ensuring data integrity.
- **Category list is centralized in Python** so forms, filters, and summaries stay consistent.

## Tradeoffs

- No user accounts means no multi-user support, but setup is instant.
- Server-side rendering was chosen over a SPA to stay within the 1.5-hour assessment scope.
- Monthly summary uses SQL aggregates rather than caching for simplicity and correctness on small datasets.
- Client-side validation uses basic alerts instead of inline field errors to reduce frontend complexity.

## Future Improvements

- Export expenses to CSV
- Charts for category and monthly trends
- Recurring expense support
- Budget history across previous months
- Budget limits per category
- Dark mode
- Pagination for large expense lists
