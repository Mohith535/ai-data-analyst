# 🎓 AI Data Analyst — Viva Voce Master Preparation Manual
### 30 Technical Questions & Concise Answers for Academic Evaluation
**Author:** K Mohith Kannan | **Institution:** SRMIST Chennai | **Degree:** B.Tech CSE (AI & ML)

---

## 📑 Table of Contents
1. [SQL Security, Injection Defense & AST Parsing](#1-sql-security-injection-defense--ast-parsing) (Q1 – Q6)
2. [Database Architecture & Data Ingestion](#2-database-architecture--data-ingestion) (Q7 – Q11)
3. [Asynchronous Concurrency & Thread Safety](#3-asynchronous-concurrency--thread-safety) (Q12 – Q16)
4. [Visual Analytics & Memory Optimization](#4-visual-analytics--memory-optimization) (Q17 – Q20)
5. [Machine Learning Pipelines & Diagnostics](#5-machine-learning-pipelines--diagnostics) (Q21 – Q24)
6. [LLM Inference, Privacy & Context Memory](#6-llm-inference-privacy--context-memory) (Q25 – Q27)
7. [UI Architecture, Modern Treeview & Open Source](#7-ui-architecture-modern-treeview--open-source) (Q28 – Q30)

---

## 1. SQL Security, Injection Defense & AST Parsing

### Q1: Why did you replace regex-based SQL validation with AST parsing using `sqlglot`?
> **Answer:** Regex pattern matching operates purely on raw characters and can be easily bypassed by string obfuscation, nested subqueries, comments, or quotes containing SQL keywords (e.g. `WHERE note = '; DROP TABLE users;'` falsely triggers a regex ban on `DROP`). An **Abstract Syntax Tree (AST)** parses the query according to MySQL grammatical formal grammar rules into a syntactic tree hierarchy. This allows structural validation: ensuring the root expression node is strictly a `Select` or CTE, verifying that no DDL/DML nodes exist anywhere in the syntax tree, and manipulating AST attributes (such as injecting or capping `LIMIT`) reliably.

### Q2: How does `sqlglot` parse a query, and why did you specify `read="mysql"`?
> **Answer:** `sqlglot.parse(sql, read="mysql")` uses the MySQL tokenizer and recursive-descent parser to transform raw SQL text into an interconnected node graph of `Expression` objects. Specifying the `mysql` dialect is mandatory because SQL dialects differ in quoting conventions (e.g., MySQL uses backticks `` `table` `` and allows specific clauses like `LIMIT count` or `LOCK IN SHARE MODE` which other dialects would fail to parse).

### Q3: Why and how do you block locking reads like `FOR UPDATE` and `LOCK IN SHARE MODE`?
> **Answer:** Locking reads acquire exclusive or shared row-level locks in InnoDB tables. In a multi-threaded analytics client using a connection pool, an uncommitted locking read can stall concurrent reads or cause deadlocks on the database server. We inspect `ast.args.get("locks")` on the parsed `exp.Select` node; if truthy, the query is rejected immediately with an explicit security error before execution.

### Q4: Why are clauses like `SELECT ... INTO OUTFILE` dangerous, and how are they blocked?
> **Answer:** `INTO OUTFILE` and `INTO DUMPFILE` allow an attacker to write query results directly to files on the host file system, enabling arbitrary web shell injection or data exfiltration. We enforce a two-tier defense: first, a fast regex guard detecting `\bINTO\s+(OUTFILE|DUMPFILE)\b`, and second, an AST inspection checking `ast.find(exp.Into)` to ensure no file export nodes exist in the query tree.

### Q5: Why do you enforce `LIMIT <= 1000` programmatically in the AST rather than trusting the LLM?
> **Answer:** LLMs are probabilistic models and can fail to include a `LIMIT` clause or hallucinate massive limits like `LIMIT 500000`. Executing uncapped queries could flood desktop RAM and freeze the GUI. In `validate_sql()`, we locate the `exp.Limit` node: if missing, we append `.limit(1000)`; if present and exceeding 1,000, we overwrite its expression literal to `1000`.

### Q6: What is the purpose of `SET SESSION TRANSACTION READ ONLY` and session execution timeouts?
> **Answer:** This implements **Defense-in-Depth**. Even if an adversarial SQL string somehow bypassed application-level AST validation, setting the database session to `TRANSACTION READ ONLY` forces MySQL's storage engine to reject any state-modifying operations at the server level. Setting `max_execution_time = 5000` automatically kills runaway queries after 5 seconds to prevent server CPU exhaustion.

---

## 2. Database Architecture & Data Ingestion

### Q7: Why did you implement a MySQL connection pool (`MySQLConnectionPool`), and why is `pool_reset_session=True` critical?
> **Answer:** Establishing a new TCP handshake and authenticating with MySQL on every ad-hoc query adds 50–150ms of latency per query. A connection pool (`pool_size=5`) maintains pre-authenticated, reusable connection objects in memory. Setting `pool_reset_session=True` ensures that when a connection is returned to the pool, temporary session variables, lock states, and uncommitted transactions are cleanly wiped before the connection is handed to another thread.

### Q8: How does your two-gate date sniffing heuristic in `db.py` work, and why is it superior to blind datetime parsing?
> **Answer:** Blindly attempting `pd.to_datetime` on every text column under 5,000 rows causes false positives on addresses, serial numbers, or error messages, while generating severe terminal warnings. Our two-gate heuristic checks:
> 1. **Gate 1 (Name Hint):** Column name contains keywords like `date`, `time`, `created`, `timestamp`, `year`, `month`, `day`.
> 2. **Gate 2 (Value Regex):** A 5-row sample matches ISO (`YYYY-MM-DD`) or slash (`DD/MM/YYYY`) date formats.
> Datetime conversion is only attempted on columns satisfying Gate 1 or Gate 2, and is only committed if $\ge 75\%$ of non-null values parse cleanly.

### Q9: Why did pandas throw a `UserWarning` during database queries, and how did you resolve it?
> **Answer:** Pandas `pd.read_sql()` expects an SQLAlchemy engine or an explicit SQLite DBAPI2 connection; passing a raw `mysql.connector` connection object triggers a warning that the DBAPI2 object is untested. We resolved this by querying MySQL directly using `cursor.fetchall()`, extracting column descriptions from `cursor.description`, and constructing `pd.DataFrame(rows, columns=cols)`. This eliminates the warning and runs faster by avoiding SQLAlchemy introspection overhead.

### Q10: Why is column identifier sanitization necessary during CSV ingestion into MySQL?
> **Answer:** Real-world CSV headers often contain trailing spaces, quotes, dollar signs, and slashes (e.g. `'Unit Price ($) '`). In MySQL, unescaped special characters or trailing whitespaces trigger **MySQL Error 1166: Incorrect column name**. `sanitize_column_name()` strips quotes, converts non-alphanumeric characters to underscores, collapses consecutive underscores, and prepends `c_` if the column starts with a digit.

### Q11: Why are CSV rows inserted in batches of 1,000 using `cursor.executemany`?
> **Answer:** Inserting rows one-by-one via individual `INSERT` calls causes $N$ roundtrips across the network/socket, taking minutes for large datasets. Inserting all rows in a single query can exceed MySQL's `max_allowed_packet` size. Chunking into batches of 1,000 rows balances socket I/O efficiency with memory safety, ingesting thousands of rows in milliseconds.

---

## 3. Asynchronous Concurrency & Thread Safety

### Q12: Why can't long-running database queries or Groq API calls run directly on Tkinter's main thread?
> **Answer:** Tkinter runs on a single-threaded event loop (`mainloop()`) that handles OS window messages, mouse clicks, rendering, and keyboard inputs. If a network request or database query blocks that thread for 2 seconds, the GUI stops responding to window manager events, Windows marks the window as *"Not Responding"*, and animations freeze.

### Q13: How does `run_async` work, and why is `widget.after(0, callback)` mandatory?
> **Answer:** `run_async()` spawns a daemon `threading.Thread` to execute the heavy I/O or mathematical calculation in the background. Tkinter is **not thread-safe**; modifying UI widgets directly from a background thread causes race conditions or crashes. When the worker finishes, it posts the result back to the main GUI thread using `widget.after(0, lambda: on_success(result))`, which schedules the UI update safely on the next tick of Tkinter's event loop.

### Q14: What is Python's Global Interpreter Lock (GIL), and why does multi-threading still help in this application?
> **Answer:** The GIL ensures only one native thread executes Python bytecode at a time. However, during network I/O (calling Groq API via HTTP) and database socket operations (MySQL queries), Python releases the GIL. This allows the GUI thread to run at full frame rate while the background thread waits on socket responses.

### Q15: How do you prevent thread deadlocks or racing when switching tables or running simultaneous queries?
> **Answer:** UI trigger buttons (e.g., `btn_ask`, `btn_run`, `btn_select`) are immediately put into a `"disabled"` state upon click, disabling re-entry. Furthermore, database operations draw independent connection instances from the pool, preventing shared-state corruption between threads.

### Q16: Why are background worker threads marked as `daemon=True`?
> **Answer:** In Python, a process will not exit when the window closes if non-daemon threads are still alive. Setting `daemon=True` ensures that if the user closes the application window, all background worker threads terminate immediately without leaving orphaned Python processes running in the background.

---

## 4. Visual Analytics & Memory Optimization

### Q17: Why was Matplotlib causing memory leaks when rendering charts in Tkinter, and how did you fix it?
> **Answer:** When Matplotlib figures are created via `plt.subplots()`, they are registered in the global figure manager. If new figures are generated repeatedly without calling `plt.close()`, memory consumption continually increases. We fixed this by storing `self.current_fig`, explicitly calling `plt.close(self.current_fig)` before generating a new chart, destroying the previous `FigureCanvasTkAgg` widget, and binding `WM_DELETE_WINDOW` to `plt.close('all')`.

### Q18: What is `matplotlib.use('Agg')` and why is it declared before importing `pyplot`?
> **Answer:** `'Agg'` (Anti-Grain Geometry) is a non-interactive raster backend that renders figures into memory buffers rather than opening standalone OS windows. Specifying `'Agg'` prevents Matplotlib from launching default Tk/Qt popup windows, allowing figures to be embedded directly into CustomTkinter frames via `FigureCanvasTkAgg`.

### Q19: How does `mplcursors` provide interactive hover inspection on Matplotlib canvases without a JavaScript runtime?
> **Answer:** `mplcursors` connects directly to Matplotlib's native event manager (`fig.canvas.mpl_connect("motion_notify_event", ...)`). When the mouse hovers over an artist (bar, line, scatter marker), `mplcursors` calculates the nearest data index, interpolates coordinates, and dynamically renders an annotated tooltip box with custom dark styling (`#121316` card, `#5E6AD2` border) directly on the canvas.

### Q20: When auto-charting a dataset with over 40 records for two numeric columns, why do you choose a histogram over a line plot?
> **Answer:** Plotting more than 40 unordered discrete points on a line chart produces a crowded "sawtooth" jagged line that conveys no actionable trend. A distribution histogram groups the dependent variable into frequency bins, revealing whether the distribution is Gaussian, bimodal, or right-skewed—providing far greater statistical value.

---

## 5. Machine Learning Pipelines & Diagnostics

### Q21: What is the mathematical meaning of $R^2$ (Coefficient of Determination), and why can it be negative?
> **Answer:** $R^2$ measures the proportion of variance in the dependent variable $y$ explained by the independent features $X$:
> $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2} = 1 - \frac{SS_{\text{res}}}{SS_{\text{tot}}}$$
> While $R^2$ is bounded in $[0, 1]$ on the training set with an intercept, it can become **negative** on an unseen test set if the fitted model makes predictions worse than simply guessing the mean value $\bar{y}$ ($SS_{\text{res}} > SS_{\text{tot}}$).

### Q22: How does your system detect and diagnose a negative $R^2$ score?
> **Answer:** In `ml.py`, after evaluating test set performance, if $R^2 < 0$, the system generates an explicit diagnostic warning: `"Negative R² indicates model fits worse than horizontal mean line. Features may be uncorrelated or non-linear."` This warns the user that their chosen feature does not share a linear relationship with the target.

### Q23: How does `suggest_best_features()` automatically rank feature candidates for regression?
> **Answer:** It computes the Pearson correlation coefficient $r \in [-1, 1]$ between every numeric candidate feature and the target column:
> $$r = \frac{\sum (x - \bar{x})(y - \bar{y})}{\sqrt{\sum (x - \bar{x})^2 \sum (y - \bar{y})^2}}$$
> Features are ranked by absolute correlation $|r|$ in descending order, guiding the user to select the most predictive predictors first.

### Q24: Why is `StandardScaler` mandatory before fitting a K-Means clustering algorithm?
> **Answer:** K-Means uses Euclidean distance ($d = \sqrt{\sum (x_i - y_i)^2}$) to assign points to cluster centroids. If one feature is measured in thousands (e.g. Annual Income: $\$50,000$) and another in single digits (e.g. Age: $35$), the larger scale feature will mathematically dominate the distance metric. `StandardScaler` standardizes each feature to mean $\mu = 0$ and variance $\sigma^2 = 1$ ($z = \frac{x - \mu}{\sigma}$), ensuring all dimensions contribute equally.

---

## 6. LLM Inference, Privacy & Context Memory

### Q25: How does the Privacy Toggle in Settings preserve data confidentiality during AI summaries?
> **Answer:** By default (`send_data_sample=False`), **zero raw data rows** leave the local machine. The system computes column names, row counts, and descriptive aggregates (Min, Mean, Max) and transmits only this statistical metadata to Groq. Users must explicitly opt-in via Settings if they want up to 8 sample preview rows sent for qualitative context.

### Q26: How does multi-turn conversation memory work in `generate_sql()`, and why is it capped at 3 turns?
> **Answer:** We maintain a rolling FIFO buffer of the last 3 user questions and generated SQL queries (`MAX_MEMORY_TURNS = 3`). These turns are prepended as alternating `user` and `assistant` messages in the Groq API payload. This provides the LLM sufficient context to resolve relative pronouns (e.g. *"filter that to North region"* or *"sort those descending"*) while avoiding token bloat and latency.

### Q27: What is the "Self-Healing Fallback" mechanism in `ai_chat.py`?
> **Answer:** If a user submits an ambiguous or conversational prompt (e.g. *"give me an overview"*) and the LLM responds with conversational text or invalid SQL that fails AST validation, the application catches the failure and automatically executes a clean default overview query (`SELECT * FROM table LIMIT 25`) with a yellow user notification, preventing query crashes.

---

## 7. UI Architecture, Modern Treeview & Open Source

### Q28: How do you implement zebra row striping, header-click sorting, and row hover highlight in `ttk.Treeview`?
> **Answer:**
> 1. **Zebra Striping:** Define tags `tree.tag_configure("even", background="#14161B")` and `"odd"` (`#181A22`), applying alternating tags upon row insertion.
> 2. **Header Sorting:** Bind each column heading command to a sorting function that parses numerical vs string values, moves items with `tree.move()`, appends `▲`/`▼` to the heading, and re-stripes the tags so zebra colors remain intact.
> 3. **Hover Highlighting:** Bind `<Motion>` to identify the row under the cursor with `tree.identify_row(event.y)` and assign a `"hover"` tag (`#282D3D`), restoring original zebra tags on `<Leave>`.

### Q29: How do global keyboard shortcuts (`Ctrl+1..6`, `Ctrl+Enter`, `Esc`) integrate into Tkinter's event-driven loop?
> **Answer:** We bind keys at the root `App` window using `self.bind("<Control-1>", handler)` so the event fires regardless of which sub-frame has focus. For input-specific actions in `ChatTab`, `<Control-Return>` is bound to `ask_ai()` and `<Escape>` is bound to clear the text box via `entry.delete(0, 'end')`.

### Q30: What rights and protections does the MIT License provide to users and creators of this software?
> **Answer:** The MIT License is a permissive free software license. It grants anyone the right to use, copy, modify, merge, publish, distribute, and sell copies of the software without restriction, requiring only that the original copyright notice and permission notice are preserved. Crucially for the author, it includes an absolute **Disclaimer of Warranty and Limitation of Liability**, protecting the author from any legal liability or damages.
