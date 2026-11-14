import os
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()  # local development only; Vercel uses its own env vars
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

PRIORITIES = ["Low", "Medium", "High"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def get_quote():
    """Bonus: third-party API. Fails silently so the app never breaks."""
    try:
        r = requests.get("https://zenquotes.io/api/random", timeout=3)
        data = r.json()[0]
        return f'"{data["q"]}" — {data["a"]}'
    except Exception:
        return None


# ---------- Public pages ----------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


# ---------- Authentication ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html")

        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            flash("That email is already registered.", "error")
            return render_template("signup.html")

        result = supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
        }).execute()

        session["user_id"] = result.data[0]["id"]
        session["name"] = name
        flash("Welcome to DueDate!", "success")
        return redirect(url_for("dashboard"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        res = supabase.table("users").select("*").eq("email", email).execute()
        user = res.data[0] if res.data else None

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- CRUD: assignments ----------
@app.route("/dashboard")
@login_required
def dashboard():  # READ
    res = (supabase.table("assignments").select("*")
           .eq("user_id", session["user_id"])
           .order("done").order("due_date").execute())
    return render_template("dashboard.html", assignments=res.data, quote=get_quote())


@app.route("/assignments/new", methods=["GET", "POST"])
@login_required
def create_assignment():  # CREATE
    if request.method == "POST":
        supabase.table("assignments").insert({
            "user_id": session["user_id"],
            "title": request.form["title"].strip(),
            "course": request.form["course"].strip(),
            "due_date": request.form["due_date"],
            "priority": request.form["priority"],
            "notes": request.form.get("notes", "").strip(),
        }).execute()
        flash("Assignment added.", "success")
        return redirect(url_for("dashboard"))
    return render_template("form.html", a=None, priorities=PRIORITIES)


def get_owned(assignment_id):
    res = (supabase.table("assignments").select("*")
           .eq("id", assignment_id).eq("user_id", session["user_id"]).execute())
    return res.data[0] if res.data else None


@app.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_assignment(assignment_id):  # UPDATE
    a = get_owned(assignment_id)
    if not a:
        flash("Assignment not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        supabase.table("assignments").update({
            "title": request.form["title"].strip(),
            "course": request.form["course"].strip(),
            "due_date": request.form["due_date"],
            "priority": request.form["priority"],
            "notes": request.form.get("notes", "").strip(),
            "done": "done" in request.form,
        }).eq("id", assignment_id).eq("user_id", session["user_id"]).execute()
        flash("Assignment updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("form.html", a=a, priorities=PRIORITIES)


@app.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
def delete_assignment(assignment_id):  # DELETE
    supabase.table("assignments").delete() \
        .eq("id", assignment_id).eq("user_id", session["user_id"]).execute()
    flash("Assignment deleted.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
