"""
setup.py — Automated Setup, Diagnostic & Environment Configuration Wizard
==========================================================================
Author: K Mohith Kannan (SRMIST Kattankulathur, Chennai)
Repository: https://github.com/Mohith535/ai-data-analyst

This script automates the complete first-time configuration:
  1. Validates Python version (>= 3.10)
  2. Installs required Python dependencies from requirements.txt
  3. Interactively guides the user to obtain and verify their free Groq API Key
  4. Configures and tests MySQL server connection (creates database if missing)
  5. Pre-populates the database with the bundled sample sales dataset
  6. Securely writes credentials into .env
  7. Offers 1-click launch of the AI Data Analyst application
"""

import sys
import os
import subprocess
import getpass
import webbrowser

# Enable ANSI escape sequences on Windows cmd
if os.name == 'nt':
    os.system('')

# ANSI terminal colors for a modern CLI experience
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("=" * 72)
    print("   📊 AI DATA ANALYST — SETUP & CONFIGURATION WIZARD")
    print("   SRMIST Chennai | B.Tech CSE (AI & ML) Capstone Platform")
    print("   Author: K Mohith Kannan | GitHub: @Mohith535")
    print("=" * 72)
    print(f"{RESET}")


def check_python_version():
    print(f"{BOLD}[1/5] Checking Python environment...{RESET}")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 10):
        print(f"{RED}❌ Python 3.10 or higher is required. Found Python {major}.{minor}.{RESET}")
        print("Please download Python from: https://www.python.org/downloads/")
        sys.exit(1)
    print(f"{GREEN}✓ Python {major}.{minor}.{sys.version_info.micro} detected.{RESET}\n")


def install_dependencies():
    print(f"{BOLD}[2/5] Verifying & installing dependencies...{RESET}")
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_file):
        print(f"{RED}❌ requirements.txt not found at {req_file}{RESET}")
        sys.exit(1)

    try:
        print(f"{BLUE}Running: pip install -r requirements.txt{RESET}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print(f"{GREEN}✓ All dependencies are installed and up to date.{RESET}\n")
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Failed to install dependencies. Error code: {e.returncode}{RESET}")
        print("Please run manually: pip install -r requirements.txt")
        sys.exit(1)


def configure_groq_api_key():
    print(f"{BOLD}[3/5] Configuring Groq AI Inference Engine...{RESET}")
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    existing_key = None

    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    val = line.strip().split("=", 1)[1]
                    if val and val != "your_groq_api_key_here":
                        existing_key = val
                        break

    if existing_key:
        print(f"{GREEN}✓ Existing Groq API Key found in .env ({existing_key[:8]}...{existing_key[-4:]}){RESET}")
        reuse = input("Do you want to keep this key? [Y/n]: ").strip().lower()
        if reuse not in ('n', 'no'):
            return existing_key

    print(f"""
{YELLOW}┌──────────────────────────────────────────────────────────────────┐
│  🔑 HOW TO GET YOUR 100% FREE GROQ API KEY:                      │
│                                                                  │
│  1. Visit: https://console.groq.com/keys                         │
│  2. Sign in with your Google or GitHub account                   │
│  3. Click '+ Create API Key', give it a name                     │
│  4. Copy the key (starts with 'gsk_') and paste it below         │
└──────────────────────────────────────────────────────────────────┘{RESET}
""")

    open_browser = input("Press [Enter] to open console.groq.com in your browser (or 's' to skip): ").strip().lower()
    if open_browser != 's':
        try:
            webbrowser.open("https://console.groq.com/keys")
        except Exception:
            pass

    while True:
        key = input(f"{BOLD}Paste your Groq API Key (starts with gsk_): {RESET}").strip()
        if not key:
            print(f"{RED}API key cannot be empty. Please enter a valid key.{RESET}")
            continue
        if not key.startswith("gsk_"):
            print(f"{YELLOW}Warning: Groq API keys usually start with 'gsk_'.{RESET}")
            confirm = input("Are you sure this is the correct key? [y/N]: ").strip().lower()
            if confirm not in ('y', 'yes'):
                continue

        # Test the key against Groq API
        print(f"{BLUE}Testing API key with Groq Cloud...{RESET}")
        try:
            from groq import Groq
            client = Groq(api_key=key)
            models = client.models.list()
            print(f"{GREEN}✓ Groq API Key verified! Connected to Groq LPU Cloud.{RESET}\n")
            return key
        except Exception as e:
            print(f"{RED}❌ Groq API connection test failed: {e}{RESET}")
            retry = input("Try entering the key again? [Y/n]: ").strip().lower()
            if retry in ('n', 'no'):
                print(f"{YELLOW}Saving key anyway without live verification.{RESET}\n")
                return key


def configure_mysql():
    print(f"{BOLD}[4/5] Configuring MySQL Database Connection...{RESET}")
    print("Ensure MySQL Server 8.0+ is installed and running on your machine.")

    host = input("MySQL Host [default: localhost]: ").strip() or "localhost"
    user = input("MySQL User [default: root]: ").strip() or "root"
    password = getpass.getpass("MySQL Password (hidden, press Enter if no password): ")
    db_name = input("Database Name [default: analyst_db]: ").strip() or "analyst_db"

    # Test MySQL connection
    print(f"{BLUE}Connecting to MySQL at {host} as '{user}'...{RESET}")
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"{GREEN}✓ Connected to MySQL successfully! Database `{db_name}` is ready.{RESET}\n")
    except Exception as e:
        print(f"{YELLOW}⚠️ Could not connect to MySQL: {e}{RESET}")
        print("Please check that MySQL Server is running. The configuration will be saved anyway.")
        cont = input("Continue anyway? [Y/n]: ").strip().lower()
        if cont in ('n', 'no'):
            sys.exit(1)

    return host, user, password, db_name


def write_env_file(groq_key, host, user, password, db_name):
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    content = f"""# ==============================================================================
# AI Data Analyst — Local Environment Configuration
# Generated automatically by setup.py
# DO NOT COMMIT THIS FILE TO GITHUB / PUBLIC SOURCE CONTROL
# ==============================================================================

# Groq Cloud API Key (Get free key at https://console.groq.com/keys)
GROQ_API_KEY={groq_key}

# MySQL Database Configuration
DB_HOST={host}
DB_USER={user}
DB_PASSWORD={password}
DB_NAME={db_name}
"""
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{GREEN}✓ Credentials saved to .env (isolated from Git source control).{RESET}\n")


def pre_populate_sample_dataset(host, user, password, db_name):
    print(f"{BOLD}[5/5] Pre-populating sample dataset for instant testing...{RESET}")
    csv_path = os.path.join(os.path.dirname(__file__), "sample_data", "sales_data.csv")
    if not os.path.exists(csv_path):
        print(f"{YELLOW}Sample dataset not found at {csv_path}, skipping.{RESET}\n")
        return

    try:
        import pandas as pd
        import db
        
        # Reload env in db module
        os.environ["DB_HOST"] = host
        os.environ["DB_USER"] = user
        os.environ["DB_PASSWORD"] = password
        os.environ["DB_NAME"] = db_name

        df = pd.read_csv(csv_path)
        success, msg = db.load_dataframe_to_mysql(df, "sales_data")
        if success:
            print(f"{GREEN}✓ Sample table `sales_data` ({len(df)} rows) loaded into `{db_name}`.{RESET}\n")
        else:
            print(f"{YELLOW}Sample dataset pre-population skipped: {msg}{RESET}\n")
    except Exception as e:
        print(f"{YELLOW}Note: Could not pre-populate sample dataset ({e}). You can upload it via the GUI.{RESET}\n")


def main():
    print_banner()
    check_python_version()
    install_dependencies()
    groq_key = configure_groq_api_key()
    host, user, password, db_name = configure_mysql()
    write_env_file(groq_key, host, user, password, db_name)
    pre_populate_sample_dataset(host, user, password, db_name)

    print(f"{CYAN}{BOLD}")
    print("=" * 72)
    print("   🎉 SETUP COMPLETE! AI DATA ANALYST IS READY TO USE.")
    print("=" * 72)
    print(f"{RESET}")
    print(f"""
Quick Start Commands:
  - Windows: run.bat   or   python main.py
  - Mac/Linux: ./run.sh or python3 main.py
""")

    launch = input(f"{BOLD}Launch AI Data Analyst now? [Y/n]: {RESET}").strip().lower()
    if launch not in ('n', 'no'):
        print(f"{GREEN}Launching AI Data Analyst...{RESET}")
        try:
            subprocess.call([sys.executable, os.path.join(os.path.dirname(__file__), "main.py")])
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
