-- Run this in Supabase: SQL Editor > New query
create table users (
  id bigint generated always as identity primary key,
  name text not null,
  email text not null unique,
  password_hash text not null,
  created_at timestamptz default now()
);

create table assignments (
  id bigint generated always as identity primary key,
  user_id bigint not null references users(id) on delete cascade,
  title text not null,
  course text not null,
  due_date date not null,
  priority text not null default 'Medium',
  notes text default '',
  done boolean not null default false,
  created_at timestamptz default now()
);
