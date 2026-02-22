Run locally
1 Install Python 3.10 or newer
2 In a terminal, go to this folder
3 Run pip3 install -r requirements.txt
4 Run streamlit run app.py

User manual
1 Styled manual HTML: docs/hydraulic_resourcing_user_manual.html
2 Editable markdown: docs/hydraulic_resourcing_user_manual.md
3 To export PDF: open the HTML in a browser, then Print > Save as PDF

Login
1 This app uses a simple password gate
2 For local runs, edit .streamlit/secrets.toml and set APP_PASSWORD
3 For Streamlit Cloud, set APP_PASSWORD in the app Secrets

Supabase cloud save (proof of concept)
1 Add these secrets in Streamlit secrets:
   SUPABASE_URL
   SUPABASE_ANON_KEY
2 Create a table in Supabase SQL editor:
   create table if not exists public.app_state (
     id text primary key,
     payload jsonb not null default '{}'::jsonb,
     updated_at timestamptz not null default now()
   );
3 Enable RLS and add policies for anon key (POC only):
   alter table public.app_state enable row level security;
   create policy "anon_select_app_state" on public.app_state for select to anon using (true);
   create policy "anon_insert_app_state" on public.app_state for insert to anon with check (true);
   create policy "anon_update_app_state" on public.app_state for update to anon using (true) with check (true);
4 In the app sidebar, use Cloud sync:
   Save to cloud
   Reload from cloud

Security notes
1 Rotate any key or password already shared in chat/email/docs.
2 For production, do not allow open anon write policies; use authenticated users or a server-side key path.

Availability horizon
Workdays to show can be increased up to 3650
