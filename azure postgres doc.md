**# Azure PostgreSQL End-to-End Documentation - Aegis Phase 2**

**## 1. Overview**

The Aegis Phase 2 project uses ****Azure Database for PostgreSQL Flexible Server**** as its core persistent storage layer. This enterprise-grade infrastructure provides the scalability and security required for director data, insider trading logs, and stock exchange notifications.

The project is architected with a  ****Multi-Database Strategy**** , where data is logically separated into four distinct databases on the same Azure host.

---

**## 2. Connection Infrastructure**

All connections use the `psycopg2` library with  ****SSL Required**** .

**### Common Connectivity Parameters**

* ****Host:**** `az10psqldmrcbtp01.postgres.database.azure.com`
* ****User:**** `psqladmin`
* ****Password:**** `1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar`
* ****Port:**** `5432`
* ****SSL Mode:**** `require`

---

**## 3. Detailed Data Dictionary (Schemas, Tables, Columns & Types)**

This section provides a granular definition of every table across the four dedicated databases.

**### A. Database: `director_disclosure_system`**

****Environment Variable:**** `POSTGRES_DATABASE_DIRECTOR`

**#### Schema: `directors_master`**

| Table Name | Column Name | Data Type | Constraint/Role |

| :--- | :--- | :--- | :--- |

| ****`directors`**** | `id` | SERIAL | PRIMARY KEY |

| | `name` | TEXT | NOT NULL |

| | `din` | TEXT | UNIQUE, INDEXED |

| | `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() |

**#### Schema: `directors_profile`**

| Table Name | Column Name | Data Type | Constraint/Role |

| :--- | :--- | :--- | :--- |

| ****`directors_profile`**** | `id` | SERIAL | PRIMARY KEY |

| | `din` | TEXT | UNIQUE, FK to `directors_master.directors(din)` |

| | `pan` | TEXT | INDEXED |

| | `name_of_director`| TEXT | |

| | `address` | TEXT | |

| | `date_of_birth` | DATE | |

| | `qualification` | TEXT | |

| | `experience` | TEXT | Nature of experience |

| | `created_at` | TIMESTAMP WITH TIME ZONE | |

| | `updated_at` | TIMESTAMP WITH TIME ZONE | |

**#### Schema: `directors_data`**

| Table Name | Column Name | Data Type | Constraint/Role |

| :--- | :--- | :--- | :--- |

| ****`document_summaries`**** | `id` | SERIAL | PRIMARY KEY |

| | `director_name` | TEXT | NOT NULL |

| | `din` | TEXT | INDEXED |

| | `file_path` | TEXT | NOT NULL, INDEXED |

| | `full_text` | TEXT | Extracted content |

| | `summary` | TEXT | AI-generated summary |

| | `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() |

| | `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() |

| ****`directors`**** | `din` | TEXT | PRIMARY KEY |

| | `name` | TEXT | |

| | `source_file` | TEXT | CSV/Excel origin |

| ****`companies`**** | `id` | SERIAL | PRIMARY KEY |

| | `name` | TEXT | UNIQUE |

| | `type` | TEXT | Private/Public |

| ****`directorships`**** | `id` | SERIAL | PRIMARY KEY |

| | `din` | TEXT | FK to `directors` |

| | `company_id` | INTEGER | FK to `companies` |

| | `position` | TEXT | Designation |

| | `appointment_date`| DATE | |

**#### Schema: `family_information`**

| Table Name | Column Name | Data Type | Description |

| :--- | :--- | :--- | :--- |

| ****`director_family`**** | `id` | SERIAL | PRIMARY KEY |

| | `director_name` | TEXT | NOT NULL, INDEXED |

| | `section_2_77_i` | TEXT | Legal declaration |

| | `section_2_77_ii` | TEXT | Legal declaration |

| | `section_2_77_iii`| TEXT | Legal declaration |

| | `father`, `mother` | TEXT | Parent names |

| | `son`, `daughter` | TEXT | Child names |

| | `brother`, `sister`| TEXT | Sibling names |

| | `father_pan` | TEXT | PAN details |

| | `mother_pan` | TEXT | PAN details |

| | `is_submitted` | INTEGER | Flag (0/1) |

---

**### B. Database: `aegis_insider_trading`**

****Environment Variable:**** `DB_NAME`

| Table Name | Column Name | Data Type | Description |

| :--- | :--- | :--- | :--- |

| ****`companies`**** | `id` | SERIAL | PRIMARY KEY |

| | `company_name` | TEXT | Corporate entity name |

| | `created_at` | TIMESTAMP | |

| ****`result_batches`**** | `id` | SERIAL | PRIMARY KEY |

| | `batch_name` | TEXT | Month/Quarter label |

| | `older_date` | DATE | Compliance period start |

| | `latest_date` | DATE | Compliance period end |

|  ****`depository_types`**** | `id` | SERIAL | PRIMARY KEY |

| | `type_name` | TEXT | NSDL / CDSL |

|  ****`shareholder_records`**** | `id` | SERIAL | PRIMARY KEY |

| | `company_id` | INTEGER | FK to `companies` |

| | `batch_id` | INTEGER | FK to `result_batches` |

| | `depository_id` | INTEGER | FK to `depository_types` |

| | `pangir` | TEXT | PAN/GIR Reference |

| | `name` | TEXT | Shareholder name |

| | `position_latest` | BIGINT | Current holding count |

| | `position_older` | BIGINT | Previous holding count |

| | `status` | TEXT | ADDED / REMOVED / CHANGED |

| ****`summary`**** | `id` | SERIAL | PRIMARY KEY |

| | `added_count` | INTEGER | |

| | `removed_count` | INTEGER | |

| | `total_count` | INTEGER | Aggregate total |

---

**### C. Database: `aegis_bse_notification`**

****Environment Variable:**** `POSTGRES_DATABASE_BSE`

| Table Name | Column Name | Data Type | Description |

| :--- | :--- | :--- | :--- |

| ****`daily_logs`**** | `id` | SERIAL | PRIMARY KEY |

| | `sr_no` | VARCHAR(50) | Serial number |

| | `entity_name` | VARCHAR(255) | Listed Company Name |

| | `link` | TEXT | Direct PDF redirect URL |

| | `nature` | VARCHAR(255) | intimation Category |

| | `summary` | TEXT | LLM-generated output |

| | `record_date` | DATE | Filing Date |

| | `processed_at` | DATE | ingestion Date |

---

**### D. Database: `visit_tracking_system`**

****Environment Variable:**** `POSTGRES_DATABASE`

| Table Name | Column Name | Data Type | Description |

| :--- | :--- | :--- | :--- |

| ****`visits`**** | `id` | SERIAL | PRIMARY KEY (usually ID=1) |

| | `count` | INTEGER | Visits counter |

| | `last_updated` | TIMESTAMP | Timestamp of last hit |

---

**## 4. Logical Integration & Architecture**

**### Backend Threading Model**

Since `psycopg2` is a synchronous driver, all FastAPI route operations use a ****Thread Pool Executor**** to prevent blocking the async event loop:

```python

# Standard Pattern used in Routes

loop = asyncio.get_event_loop()

result = await loop.run_in_executor(thread_pool, database_function)

```

**### Best Practices & Security**

1. ****Parameterized Queries:**** All SQL calls use `%s` placeholder syntax to prevent SQL injection.
2. ****Dictionary Cursors:**** Uses `RealDictCursor` for JSON-ready data output.
3. ****Encapsulation:**** Database credentials are strictly loaded from `.env` files.
4. ****Resource Lifecycle:**** Each DB operation opens its own connection and ensures it is closed via `finally` blocks.

---

**## 5. Maintenance & Troubleshooting**

* ****Connectivity Verification:**** Run `scripts/check_env_vars.py` to ensure all 4 DB strings are correctly configured in the local environment.
* ****Logging:**** All failed connection attempts are captured in the server's audit logs with specific database identifiers.

---

**Generated for the Aegis Phase 2 Project - Architecture Documentation**
