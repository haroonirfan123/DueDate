# DueDate — Student Assignment Tracker

Flask + Supabase web app that lets students log in and manage their assignments.

## Run locally
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your values
3. Run `schema.sql` in the Supabase SQL Editor
4. `python app.py`

## Deploy (Vercel)
Push to GitHub, import the repo in Vercel, and add `SECRET_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` under Settings > Environment Variables.

## Submission form description
**Problem:** Students juggle assignments across many courses and often forget deadlines because they track them in scattered notes, chats, and memory.
**Audience:** University and college students managing multiple courses.
**Database logic:** Supabase (PostgreSQL) has two tables: `users` (name, unique email, hashed password) and `assignments` (title, course, due date, priority, notes, done), linked by `user_id` with cascade delete. Every query filters by the logged-in user's id, so each student only sees and edits their own data.
