Hydraulic Resourcing App v7

This build supports
1 Shared admin login
2 Supabase database persistence
3 Streamlit Cloud deployment
4 Local run for testing

Local run
1 Unzip folder
2 Open Terminal in the folder
3 Create venv
python3 -m venv .venv
4 Activate venv
source .venv/bin/activate
5 Install requirements
python3 -m pip install -r requirements.txt
6 Create secrets file
Copy .streamlit/secrets.example.toml to .streamlit/secrets.toml
Fill in SUPABASE_URL and SUPABASE_ANON_KEY
7 Run app
streamlit run app.py

Streamlit Cloud deployment
1 Push this folder to GitHub
2 In Streamlit Cloud, deploy from that repo
3 In Streamlit Cloud settings, add secrets
APP_PASSWORD
SUPABASE_URL
SUPABASE_ANON_KEY
4 Reboot app

Supabase setup
1 In Supabase, open SQL editor
2 Run supabase_setup.sql once
3 Use API Keys page to copy publishable key only, starts with sb_publishable

Notes
1 Never paste or commit the secret key
2 If secrets are missing, the app will show an error with what to set
