# 📊 AI Data Analyst — Intelligent Desktop Analytics Platform

> **Author:** K Mohith Kannan | **Affiliation:** SRMIST Kattankulathur, Chennai (Batch 2025–2029)  
> **Degree:** B.Tech CSE (Artificial Intelligence & Machine Learning)  
> **Course:** Python Lab / Capstone Project  
> **Architecture:** Desktop Client (Python 3.12 + CustomTkinter + MySQL 8.0 + Scikit-Learn + Groq LLM Cloud)

---

## 🎯 Executive Summary & Purpose

Modern businesses sit on massive volumes of relational data stored across SQL databases and CSV reports, yet non-technical stakeholders (founders, managers, marketers) struggle with SQL syntax and complex statistical software.

**AI Data Analyst** bridges this divide by providing an elegant, Linear/Raycast-inspired dark desktop analytics environment where users can:
1. **Ingest & Normalize:** Upload raw CSV files, automatically profile dataset quality (completeness, missing cells, duplicates, IQR outliers), and persist them into a production MySQL engine with automated column name sanitization.
2. **Visualize:** Generate high-resolution, dark-themed statistical charts (Bar, Trend Line, Donut/Pie, Distribution Histogram) embedded natively via matplotlib with auto-downsampling on large datasets.
3. **Model & Predict:** Execute scikit-learn Machine Learning pipelines (Linear Regression with train/test splits & KMeans clustering with feature normalization).
4. **Autonomous AI Teacher & Analyst:** Chat with an AI data analyst powered by Groq's low-latency inference engine (OpenAI GPT-OSS 120B / Qwen 27B) that converts natural English questions into safe, optimized MySQL queries, executes them in real time, and synthesizes plain-English educational takeaways.
5. **Executive PDF Dossiers:** Generate multi-page executive briefing documents with clean layout separation and zero text-image collision.

---

## 🛠️ Complete Change Log & Architectural Problem-Solving

| Component | Root Cause / Issue Observed | Solution Implemented |
|---|---|---|
| **MySQL Ingestion (`db.py`)** | `Error 1166 (42000): Incorrect column name 'Unit_Cost '` due to trailing whitespace and special symbols in CSV headers. | Engineered `sanitize_column_name()` which strips leading/trailing spaces, quotes, backticks, and translates special characters into valid MySQL identifiers. |
| **Sequential CSV Loading (`ui/upload_tab.py`)** | Preview table disappeared after switching files due to widget destruction cycle. | Replaced frame teardown with persistent Treeview container; dynamically repopulates columns and rows on every selection. |
| **PDF Overlap (`report_generator.py`)** | Donut charts colliding and printing text over data tables. | Structured 2-page briefing flow: Page 1 holds Brief, SQL, Takeaway, and Table; Page 2 hosts the full-bleed high-res chart. |
| **PDF Encoding Crash (`report_generator.py`)** | `Character '—' outside range supported by helveticaB`. | Implemented `clean_unicode_for_pdf()` to normalize typographic quotes, bullets, and em-dashes to clean Latin-1 equivalents. |
| **AI Insight Mode (`ui/chat_tab.py`)** | User had to manually toggle switch; default text was confusing. | Transformed into **Permanent AI Teacher Mode**: every query automatically generates conversational takeaways explaining what the numbers mean. |
| **Visual Overcrowding (`charts.py`)** | Plotting 500+ rows generated messy, unreadable mesh of points. | Added smart downsampling and automatic metric histogram distribution binning for datasets exceeding 40 rows. |
| **Navigation & Ergonomics (`ui/app.py`)** | Top navigation bar squished vertical content. | Redesigned into a Linear/Raycast collapsible sidebar with `☰` toggle, maximizing canvas space. |

---

## 🎓 Viva Voce & Academic Evaluation Guide

### Q1: Why is an AI "Teacher / Insight" mode better than returning raw SQL alone?
> **Answer:** "A raw SQL query and data table show *what* the data is, but not *why* it matters. By adding an automated natural language synthesis step, the application acts as an intelligent co-pilot: it interprets trends, highlights anomalies, and explains statistical findings in plain English so non-technical stakeholders and students can learn from the data."

### Q2: How does the application handle corrupted or malformed CSV column names?
> **Answer:** "Raw CSV headers often contain trailing whitespace, parentheses, dollar signs, and slashes (`'Unit_Cost '`, `'Price ($)'`). In standard MySQL, identifiers with trailing whitespace cause fatal syntax errors (`Error 1166`). In `db.py`, our `sanitize_column_name()` pipeline strips quotes, trims whitespace, maps illegal characters to underscores, handles numeric prefixes, and tracks duplicate collisions before compiling the `CREATE TABLE` DDL."

### Q3: What is the Interquartile Range (IQR) rule used in Data Quality profiling?
> **Answer:** "The IQR rule identifies statistical outliers without assuming a normal distribution. 
> $$\text{IQR} = Q_3 - Q_1$$
> Any data point falling below $Q_1 - 1.5 \times \text{IQR}$ or above $Q_3 + 1.5 \times \text{IQR}$ is flagged as an outlier. This alerts the user to extreme values before running ML regression or clustering."

### Q4: Why use a 2-page structured flow for executive PDF generation?
> **Answer:** "Embedding large dynamic vector graphics and tabular records on a single unconstrained page leads to element collisions and awkward page cuts. Decoupling the narrative brief (Executive Insight, Query, Sample Rows) to Page 1 and centering the visual chart canvas on Page 2 ensures crisp, publication-grade document hierarchy."
