# 📊 AI Data Analyst — Intelligent Desktop Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter%206.0-1f538d?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Groq](https://img.shields.io/badge/Inference-Groq%20Cloud-F55036?style=for-the-badge)](https://groq.com)

A modern, macOS glass-inspired desktop analytics platform built with Python. Upload datasets, inspect schemas, persist to MySQL, visualize with customized Matplotlib charts, fit explainable Scikit-Learn Machine Learning models, and converse with an autonomous AI Analyst powered by Groq's high-speed inference engine.

---

## ✨ Features

- 📂 **Smart Ingestion:** Pick any CSV, preview in high-contrast data table, inspect RAM usage, and ingest directly into MySQL with automatic datatype inference.
- 📊 **Visual Analytics Studio:** High-res dark-themed charts (Bar, Trend Line, Donut, Distribution Histogram) embedded seamlessly in the GUI.
- 🤖 **Machine Learning Workbench:**
  - **Linear Regression:** 80/20 train/test evaluation, $R^2$ score, Mean Absolute Error, dynamic equation formula, and fitted regression visualization.
  - **K-Means Clustering:** Feature scaling via `StandardScaler`, configurable cluster counts ($K \in [2, 10]$), centroid calculation, and cluster dispersion plot.
- 💬 **Natural Language AI Analyst:**
  - **Text-to-SQL:** Ask natural language questions in English $\rightarrow$ AI compiles safe MySQL 8.0 `SELECT` queries.
  - **Data Privacy:** Only schema definitions are sent to the LLM; your raw records never leave your local database.
  - **Natural Language Insight Mode:** Synthesizes actionable business takeaways directly from query results.
  - **Automated Visualization:** Dynamically chooses and renders the best visual chart matching query dimensions.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.12 or newer
- MySQL Server 8.0+ running on port `3306`

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/Mohith535/ai-data-analyst.git
cd ai-data-analyst

# Install dependencies
pip install customtkinter mysql-connector-python pandas matplotlib scikit-learn groq python-dotenv
```

### 3. Configure Secrets
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_free_groq_api_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=analyst_db
```

### 4. Run Application
```powershell
python main.py
```

---

## 🏛️ Project Architecture

```
ai_data_analyst/
├── main.py                     # Entry point & DB connection check
├── db.py                       # MySQL schema & batch ingestion driver
├── charts.py                   # Matplotlib chart helpers (Agg backend)
├── ml.py                       # Linear Regression & KMeans pipelines
├── ai_chat.py                  # Groq API client & AST validation
├── sample_data/
│   └── sales_data.csv          # Sample dataset for instant test runs
├── ui/
│   ├── app.py                  # Main window with macOS pill styling
│   ├── upload_tab.py           # Ingestion & table preview tab
│   ├── charts_tab.py           # Visualization studio tab
│   ├── ml_tab.py               # Machine Learning workbench tab
│   └── chat_tab.py             # Dual-pane AI chat tab
├── PROJECT.md                  # Detailed engineering dossier & Viva Q&A
└── README.md                   # Repository overview
```

---

## 👨‍💻 Author

**K Mohith Kannan**  
B.Tech CSE (AI & ML) — SRMIST Kattankulathur, Chennai  
*Aspiring AI & Software Engineer / Entrepreneur*

