import os
import sqlite3
from datetime import date, datetime

from flask import Flask, flash, g, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "expenseflow-dev-key"
app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "database.db")

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def current_month_key():
    return date.today().strftime("%Y-%m")


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_budgets(
            month TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


def format_currency(amount):
    return f"₹{amount:,.2f}"


app.jinja_env.filters["currency"] = format_currency


def parse_date(value):
    if not value or not value.strip():
        return None, "Date is required."
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD."
    if parsed > date.today():
        return None, "Future dates are not allowed."
    return parsed.isoformat(), None


def validate_expense_form(form):
    errors = []

    title = (form.get("title") or "").strip()
    amount_raw = (form.get("amount") or "").strip()
    category = (form.get("category") or "").strip()
    date_raw = (form.get("date") or "").strip()
    note = (form.get("note") or "").strip()

    if not title:
        errors.append("Title is required.")

    amount = None
    if not amount_raw:
        errors.append("Amount is required.")
    else:
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be a positive number.")
        except ValueError:
            errors.append("Amount must be a valid number.")

    if not category:
        errors.append("Category is required.")
    elif category not in CATEGORIES:
        errors.append("Invalid category selected.")

    expense_date, date_error = parse_date(date_raw)
    if date_error:
        errors.append(date_error)

    return {
        "title": title,
        "amount": amount,
        "category": category,
        "date": expense_date,
        "note": note or None,
        "errors": errors,
    }


def validate_budget(amount_raw):
    errors = []
    amount = None

    if not amount_raw or not str(amount_raw).strip():
        errors.append("Budget cannot be empty.")
    else:
        try:
            amount = float(str(amount_raw).strip())
            if amount <= 0:
                errors.append("Budget must be a positive number.")
        except ValueError:
            errors.append("Budget must be a valid number.")

    return amount, errors


def get_monthly_budget(month_key=None):
    db = get_db()
    month_key = month_key or current_month_key()
    row = db.execute(
        "SELECT amount FROM monthly_budgets WHERE month = ?",
        (month_key,),
    ).fetchone()
    return row["amount"] if row else None


def set_monthly_budget(amount, month_key=None):
    db = get_db()
    month_key = month_key or current_month_key()
    db.execute(
        """
        INSERT INTO monthly_budgets (month, amount, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(month) DO UPDATE SET
            amount = excluded.amount,
            updated_at = CURRENT_TIMESTAMP
        """,
        (month_key, amount),
    )
    db.commit()


def get_monthly_summary():
    db = get_db()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end = today.isoformat()
    month_key = current_month_key()

    totals = db.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total_spent,
            COUNT(*) AS expense_count,
            COALESCE(MAX(amount), 0) AS highest_expense
        FROM expenses
        WHERE date >= ? AND date <= ?
        """,
        (month_start, month_end),
    ).fetchone()

    category_rows = db.execute(
        """
        SELECT category, COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE date >= ? AND date <= ?
        GROUP BY category
        """,
        (month_start, month_end),
    ).fetchall()

    category_totals = {cat: 0.0 for cat in CATEGORIES}
    for row in category_rows:
        category_totals[row["category"]] = row["total"]

    monthly_budget = get_monthly_budget(month_key)
    total_spent = totals["total_spent"]
    remaining_budget = None
    exceeded_by = None
    is_exceeded = False

    if monthly_budget is not None:
        remaining_budget = monthly_budget - total_spent
        if remaining_budget < 0:
            is_exceeded = True
            exceeded_by = abs(remaining_budget)
            remaining_budget = 0

    return {
        "total_spent": total_spent,
        "expense_count": totals["expense_count"],
        "highest_expense": totals["highest_expense"],
        "category_totals": category_totals,
        "month_label": today.strftime("%B %Y"),
        "month_key": month_key,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "is_exceeded": is_exceeded,
        "exceeded_by": exceeded_by,
    }


def build_expense_query(filters):
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    category = filters.get("category")
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    from_date = filters.get("from_date")
    if from_date:
        query += " AND date >= ?"
        params.append(from_date)

    to_date = filters.get("to_date")
    if to_date:
        query += " AND date <= ?"
        params.append(to_date)

    search = filters.get("search")
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY date DESC, id DESC"
    return query, params


@app.route("/budget", methods=["POST"])
def set_budget():
    init_db()
    amount_raw = request.form.get("budget", "")
    amount, errors = validate_budget(amount_raw)

    if errors:
        for message in errors:
            flash(message, "error")
    else:
        set_monthly_budget(amount)
        flash("Monthly budget updated successfully.", "success")

    return redirect(url_for("index"))


@app.route("/")
def index():
    init_db()
    db = get_db()

    filters = {
        "category": request.args.get("category", "All"),
        "from_date": (request.args.get("from_date") or "").strip(),
        "to_date": (request.args.get("to_date") or "").strip(),
        "search": (request.args.get("search") or "").strip(),
    }

    filter_errors = []
    if filters["from_date"]:
        _, err = parse_date(filters["from_date"])
        if err:
            filter_errors.append(f"From date: {err}")
    if filters["to_date"]:
        _, err = parse_date(filters["to_date"])
        if err:
            filter_errors.append(f"To date: {err}")
    if (
        filters["from_date"]
        and filters["to_date"]
        and not filter_errors
        and filters["from_date"] > filters["to_date"]
    ):
        filter_errors.append("From date cannot be after To date.")

    for message in filter_errors:
        flash(message, "error")

    expenses = []
    filters_applied = any(
        [
            filters["category"] != "All",
            filters["from_date"],
            filters["to_date"],
            filters["search"],
        ]
    )

    if not filter_errors:
        query, params = build_expense_query(filters)
        expenses = db.execute(query, params).fetchall()
        if filters_applied and not expenses:
            flash("No matching records found.", "info")

    summary = get_monthly_summary()
    today_str = date.today().isoformat()

    return render_template(
        "index.html",
        expenses=expenses,
        categories=CATEGORIES,
        filters=filters,
        summary=summary,
        today=today_str,
        filters_applied=filters_applied,
    )


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    init_db()
    today_str = date.today().isoformat()
    form_data = {
        "title": "",
        "amount": "",
        "category": "",
        "date": today_str,
        "note": "",
    }

    if request.method == "POST":
        validated = validate_expense_form(request.form)
        form_data = {
            "title": validated["title"],
            "amount": request.form.get("amount", ""),
            "category": validated["category"],
            "date": request.form.get("date", today_str),
            "note": validated["note"] or "",
        }

        if validated["errors"]:
            for message in validated["errors"]:
                flash(message, "error")
        else:
            db = get_db()
            db.execute(
                """
                INSERT INTO expenses (title, amount, category, date, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    validated["title"],
                    validated["amount"],
                    validated["category"],
                    validated["date"],
                    validated["note"],
                ),
            )
            db.commit()
            flash("Expense added successfully.", "success")
            return redirect(url_for("index"))

    return render_template(
        "add_expense.html",
        categories=CATEGORIES,
        form_data=form_data,
        today=today_str,
    )


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    init_db()
    db = get_db()
    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if expense is None:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    form_data = {
        "title": expense["title"],
        "amount": expense["amount"],
        "category": expense["category"],
        "date": expense["date"],
        "note": expense["note"] or "",
    }

    if request.method == "POST":
        validated = validate_expense_form(request.form)
        form_data = {
            "title": validated["title"],
            "amount": request.form.get("amount", ""),
            "category": validated["category"],
            "date": request.form.get("date", expense["date"]),
            "note": validated["note"] or "",
        }

        if validated["errors"]:
            for message in validated["errors"]:
                flash(message, "error")
        else:
            db.execute(
                """
                UPDATE expenses
                SET title = ?, amount = ?, category = ?, date = ?, note = ?
                WHERE id = ?
                """,
                (
                    validated["title"],
                    validated["amount"],
                    validated["category"],
                    validated["date"],
                    validated["note"],
                    expense_id,
                ),
            )
            db.commit()
            flash("Expense updated successfully.", "success")
            return redirect(url_for("index"))

    return render_template(
        "edit_expense.html",
        categories=CATEGORIES,
        form_data=form_data,
        expense_id=expense_id,
        today=date.today().isoformat(),
    )


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    init_db()
    db = get_db()
    expense = db.execute(
        "SELECT id FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if expense is None:
        flash("Expense not found.", "error")
    else:
        db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        db.commit()
        flash("Expense deleted successfully.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
