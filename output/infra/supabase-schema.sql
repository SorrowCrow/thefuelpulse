-- Fuel Prices Latvia — Supabase subscriber schema
-- Double opt-in: confirmed_at is NULL until user clicks confirmation link.
-- token (UUID) is used for confirm + unsubscribe links — not guessable.
-- Price alert emails are only sent to rows where confirmed_at IS NOT NULL.

-- Enable UUID extension
create extension if not exists "pgcrypto";

create table if not exists subscribers (
  id           uuid        primary key default gen_random_uuid(),
  email        text        not null unique,
  token        uuid        not null default gen_random_uuid(),
  language     text        not null default 'lv' check (language in ('lv', 'en', 'ru')),
  confirmed_at timestamptz,               -- NULL = pending; set on email confirmation click
  created_at   timestamptz not null default now()
);

-- Row Level Security
alter table subscribers enable row level security;

-- Service role gets full access (used by Vercel API routes server-side)
create policy "Service role full access" on subscribers
  for all
  using (auth.role() = 'service_role');

-- Anon role: INSERT only (subscribe form)
create policy "Anon insert" on subscribers
  for insert
  to anon
  with check (true);
