# SSO Database Exploration Report

**Generated at:** `2026-04-21 22:47:05`
**Host:** `az10psqldmrcbtp01.postgres.database.azure.com`
**Database:** `visit_tracking_system`
**Schema:** `rbac`
**SSL:** `require`

---

## 1. PostgreSQL Server Info

| Field      | Value                                                                         |
| ---------- | ----------------------------------------------------------------------------- |
| Version    | PostgreSQL 16.12 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 13.2.0, 64-bit |
| Database   | visit_tracking_system                                                         |
| User       | psqladmin                                                                     |
| Started At | 2026-04-19 02:49:21.972312+00:00                                              |
| Server IP  | 10.212.154.132                                                                |
| Port       | 5432                                                                          |


## 2. All Schemas in Database

| Schema Name        | Owner          |
| ------------------ | -------------- |
| information_schema | azuresu        |
| minutes            | psqladmin      |
| pg_catalog         | azuresu        |
| pg_toast           | azuresu        |
| public             | azure_pg_admin |
| rbac               | psqladmin      |
| visit_tracking     | psqladmin      |


## 3. All Tables in `rbac` Schema

| Table Name        | Size on Disk |
| ----------------- | ------------ |
| access_requests   | 32 kB        |
| admin_credentials | 24 kB        |
| allowed_emails    | 24 kB        |
| auth_audit_logs   | 32 kB        |
| route_definitions | 16 kB        |
| route_permissions | 48 kB        |
| user_roles        | 48 kB        |


## 4. Table-by-Table Deep Dive

---

### 4.x `rbac.access_requests`

**Total Rows:** `4`


#### Columns & Types

| #  | Column Name          | Data Type                   | Nullable | Default                                          |
| -- | -------------------- | --------------------------- | -------- | ------------------------------------------------ |
| 1  | id                   | integer                     | NO       | nextval('rbac.access_requests_id_seq'::regclass) |
| 2  | email                | text                        | NO       | _NULL_                                           |
| 3  | name                 | text                        | NO       | _NULL_                                           |
| 4  | requested_route      | text                        | NO       | _NULL_                                           |
| 5  | requested_permission | text                        | NO       | _NULL_                                           |
| 6  | justification        | text                        | YES      | _NULL_                                           |
| 7  | status               | text                        | YES      | 'pending'::text                                  |
| 8  | requested_at         | timestamp without time zone | YES      | CURRENT_TIMESTAMP                                |
| 9  | reviewed_by          | text                        | YES      | _NULL_                                           |
| 10 | reviewed_at          | timestamp without time zone | YES      | _NULL_                                           |
| 11 | review_notes         | text                        | YES      | _NULL_                                           |


#### Primary Key(s)

`id`


#### Indexes

| Index Name           | Definition                                                                       |
| -------------------- | -------------------------------------------------------------------------------- |
| access_requests_pkey | CREATE UNIQUE INDEX access_requests_pkey ON rbac.access_requests USING btree ... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause                     |
| ---------------------- | -------------------------------- |
| 29002_29042_1_not_null | id IS NOT NULL                   |
| 29002_29042_2_not_null | email IS NOT NULL                |
| 29002_29042_3_not_null | name IS NOT NULL                 |
| 29002_29042_4_not_null | requested_route IS NOT NULL      |
| 29002_29042_5_not_null | requested_permission IS NOT NULL |


#### Sample Data (up to 4 rows)

| id | email                          | name                  | requested_route  | requested_permission | justification | status  | requested_at               | reviewed_by | reviewed_at | review_notes |
| -- | ------------------------------ | --------------------- | ---------------- | -------------------- | ------------- | ------- | -------------------------- | ----------- | ----------- | ------------ |
| 1  | abhishek.mahadevmane@adani.com | Abhishek Mahadev Mane | /bse-alerts      | view                 | testing       | pending | 2026-04-21 15:48:02.722866 | _NULL_      | _NULL_      | _NULL_       |
| 2  | abhishek.mahadevmane@adani.com | Abhishek Mahadev Mane | /rbi-dashboard   | admin                | Hi            | pending | 2026-04-21 15:56:21.157409 | _NULL_      | _NULL_      | _NULL_       |
| 3  | abhishek.mahadevmane@adani.com | Abhishek Mahadev Mane | /sebi-dashboard  | view                 | hi            | pending | 2026-04-21 16:03:11.096623 | _NULL_      | _NULL_      | _NULL_       |
| 4  | abhishek.mahadevmane@adani.com | Abhishek Mahadev Mane | /insider-trading | view                 | Hi            | pending | 2026-04-21 16:56:31.110420 | _NULL_      | _NULL_      | _NULL_       |


#### Unique Value Counts (key columns)

| Column | Distinct Values |
| ------ | --------------- |
| email  | 1               |
| status | 1               |

---

### 4.x `rbac.admin_credentials`

**Total Rows:** `0`


#### Columns & Types

| # | Column Name | Data Type                   | Nullable | Default                                            |
| - | ----------- | --------------------------- | -------- | -------------------------------------------------- |
| 1 | id          | integer                     | NO       | nextval('rbac.admin_credentials_id_seq'::regclass) |
| 2 | username    | text                        | NO       | _NULL_                                             |
| 3 | password    | text                        | NO       | _NULL_                                             |
| 4 | created_at  | timestamp without time zone | YES      | CURRENT_TIMESTAMP                                  |


#### Primary Key(s)

`id`


#### Indexes

| Index Name                     | Definition                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------- |
| admin_credentials_pkey         | CREATE UNIQUE INDEX admin_credentials_pkey ON rbac.admin_credentials USING bt... |
| admin_credentials_username_key | CREATE UNIQUE INDEX admin_credentials_username_key ON rbac.admin_credentials ... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause         |
| ---------------------- | -------------------- |
| 29002_29053_1_not_null | id IS NOT NULL       |
| 29002_29053_2_not_null | username IS NOT NULL |
| 29002_29053_3_not_null | password IS NOT NULL |


#### Sample Data (up to 4 rows)

_Table is empty — no data yet._


#### Unique Value Counts (key columns)

_Not applicable._

---

### 4.x `rbac.allowed_emails`

**Total Rows:** `0`


#### Columns & Types

| # | Column Name | Data Type                   | Nullable | Default                                         |
| - | ----------- | --------------------------- | -------- | ----------------------------------------------- |
| 1 | id          | integer                     | NO       | nextval('rbac.allowed_emails_id_seq'::regclass) |
| 2 | email       | text                        | NO       | _NULL_                                          |
| 3 | added_at    | timestamp without time zone | YES      | CURRENT_TIMESTAMP                               |


#### Primary Key(s)

`id`


#### Indexes

| Index Name               | Definition                                                                       |
| ------------------------ | -------------------------------------------------------------------------------- |
| allowed_emails_pkey      | CREATE UNIQUE INDEX allowed_emails_pkey ON rbac.allowed_emails USING btree (id)  |
| allowed_emails_email_key | CREATE UNIQUE INDEX allowed_emails_email_key ON rbac.allowed_emails USING btr... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause      |
| ---------------------- | ----------------- |
| 29002_29065_1_not_null | id IS NOT NULL    |
| 29002_29065_2_not_null | email IS NOT NULL |


#### Sample Data (up to 4 rows)

_Table is empty — no data yet._


#### Unique Value Counts (key columns)

_Not applicable._

---

### 4.x `rbac.auth_audit_logs`

**Total Rows:** `9`


#### Columns & Types

| # | Column Name   | Data Type                   | Nullable | Default                                          |
| - | ------------- | --------------------------- | -------- | ------------------------------------------------ |
| 1 | id            | integer                     | NO       | nextval('rbac.auth_audit_logs_id_seq'::regclass) |
| 2 | email         | text                        | NO       | _NULL_                                           |
| 3 | event_type    | text                        | NO       | _NULL_                                           |
| 4 | event_details | jsonb                       | YES      | _NULL_                                           |
| 5 | ip_address    | text                        | YES      | _NULL_                                           |
| 6 | user_agent    | text                        | YES      | _NULL_                                           |
| 7 | application   | text                        | YES      | _NULL_                                           |
| 8 | timestamp     | timestamp without time zone | YES      | CURRENT_TIMESTAMP                                |


#### Primary Key(s)

`id`


#### Indexes

| Index Name           | Definition                                                                       |
| -------------------- | -------------------------------------------------------------------------------- |
| auth_audit_logs_pkey | CREATE UNIQUE INDEX auth_audit_logs_pkey ON rbac.auth_audit_logs USING btree ... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause           |
| ---------------------- | ---------------------- |
| 29002_29004_1_not_null | id IS NOT NULL         |
| 29002_29004_2_not_null | email IS NOT NULL      |
| 29002_29004_3_not_null | event_type IS NOT NULL |


#### Sample Data (up to 4 rows)

| id | email                          | event_type | event_details                       | ip_address | user_agent | application | timestamp                  |
| -- | ------------------------------ | ---------- | ----------------------------------- | ---------- | ---------- | ----------- | -------------------------- |
| 1  | Abhishek.MahadevMane@adani.com | login      | {'routes': [], 'status': 'success'} | _NULL_     | _NULL_     | _NULL_      | 2026-04-21 15:38:18.909801 |
| 2  | Abhishek.MahadevMane@adani.com | login      | {'routes': [], 'status': 'success'} | _NULL_     | _NULL_     | _NULL_      | 2026-04-21 15:41:05.128927 |
| 3  | Abhishek.MahadevMane@adani.com | login      | {'routes': [], 'status': 'success'} | _NULL_     | _NULL_     | _NULL_      | 2026-04-21 15:52:42.460015 |
| 4  | Abhishek.MahadevMane@adani.com | login      | {'routes': [], 'status': 'success'} | _NULL_     | _NULL_     | _NULL_      | 2026-04-21 15:55:47.240253 |


#### Unique Value Counts (key columns)

| Column      | Distinct Values |
| ----------- | --------------- |
| email       | 1               |
| event_type  | 2               |
| application | 0               |

---

### 4.x `rbac.route_definitions`

**Total Rows:** `0`


#### Columns & Types

| # | Column Name  | Data Type                   | Nullable | Default           |
| - | ------------ | --------------------------- | -------- | ----------------- |
| 1 | route_path   | text                        | NO       | _NULL_            |
| 2 | route_name   | text                        | NO       | _NULL_            |
| 3 | description  | text                        | YES      | _NULL_            |
| 4 | application  | text                        | YES      | _NULL_            |
| 5 | is_active    | boolean                     | YES      | true              |
| 6 | created_at   | timestamp without time zone | YES      | CURRENT_TIMESTAMP |
| 7 | display_name | text                        | YES      | _NULL_            |
| 8 | module_name  | text                        | YES      | _NULL_            |


#### Primary Key(s)

`route_path`


#### Indexes

| Index Name             | Definition                                                                       |
| ---------------------- | -------------------------------------------------------------------------------- |
| route_definitions_pkey | CREATE UNIQUE INDEX route_definitions_pkey ON rbac.route_definitions USING bt... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause           |
| ---------------------- | ---------------------- |
| 29002_29013_1_not_null | route_path IS NOT NULL |
| 29002_29013_2_not_null | route_name IS NOT NULL |


#### Sample Data (up to 4 rows)

_Table is empty — no data yet._


#### Unique Value Counts (key columns)

_Not applicable._

---

### 4.x `rbac.route_permissions`

**Total Rows:** `0`


#### Columns & Types

| # | Column Name     | Data Type                   | Nullable | Default                                            |
| - | --------------- | --------------------------- | -------- | -------------------------------------------------- |
| 1 | id              | integer                     | NO       | nextval('rbac.route_permissions_id_seq'::regclass) |
| 2 | email           | text                        | NO       | _NULL_                                             |
| 3 | route_path      | text                        | YES      | _NULL_                                             |
| 4 | permission_type | text                        | NO       | _NULL_                                             |
| 5 | assigned_at     | timestamp without time zone | YES      | CURRENT_TIMESTAMP                                  |
| 6 | assigned_by     | text                        | YES      | _NULL_                                             |
| 7 | notes           | text                        | YES      | _NULL_                                             |
| 8 | is_active       | boolean                     | YES      | true                                               |
| 9 | updated_at      | timestamp without time zone | YES      | CURRENT_TIMESTAMP                                  |


#### Primary Key(s)

`id`


#### Indexes

| Index Name                             | Definition                                                                       |
| -------------------------------------- | -------------------------------------------------------------------------------- |
| route_permissions_pkey                 | CREATE UNIQUE INDEX route_permissions_pkey ON rbac.route_permissions USING bt... |
| route_permissions_email_route_path_key | CREATE UNIQUE INDEX route_permissions_email_route_path_key ON rbac.route_perm... |


#### Foreign Keys

| Column     | References Table       | References Column |
| ---------- | ---------------------- | ----------------- |
| route_path | rbac.route_definitions | route_path        |


#### Check Constraints

| Constraint Name        | Check Clause                |
| ---------------------- | --------------------------- |
| 29002_29023_1_not_null | id IS NOT NULL              |
| 29002_29023_2_not_null | email IS NOT NULL           |
| 29002_29023_4_not_null | permission_type IS NOT NULL |


#### Sample Data (up to 4 rows)

_Table is empty — no data yet._


#### Unique Value Counts (key columns)

_Not applicable._

---

### 4.x `rbac.user_roles`

**Total Rows:** `1`


#### Columns & Types

| # | Column Name | Data Type                   | Nullable | Default                                     |
| - | ----------- | --------------------------- | -------- | ------------------------------------------- |
| 1 | id          | integer                     | NO       | nextval('rbac.user_roles_id_seq'::regclass) |
| 2 | email       | text                        | NO       | _NULL_                                      |
| 3 | role        | text                        | NO       | _NULL_                                      |
| 4 | assigned_at | timestamp without time zone | YES      | CURRENT_TIMESTAMP                           |


#### Primary Key(s)

`id`


#### Indexes

| Index Name                | Definition                                                                       |
| ------------------------- | -------------------------------------------------------------------------------- |
| user_roles_pkey           | CREATE UNIQUE INDEX user_roles_pkey ON rbac.user_roles USING btree (id)          |
| user_roles_email_role_key | CREATE UNIQUE INDEX user_roles_email_role_key ON rbac.user_roles USING btree ... |


#### Foreign Keys

_No foreign keys._


#### Check Constraints

| Constraint Name        | Check Clause      |
| ---------------------- | ----------------- |
| 29002_29077_1_not_null | id IS NOT NULL    |
| 29002_29077_2_not_null | email IS NOT NULL |
| 29002_29077_3_not_null | role IS NOT NULL  |


#### Sample Data (up to 4 rows)

| id | email                | role  | assigned_at                |
| -- | -------------------- | ----- | -------------------------- |
| 1  | cogn206112@adani.com | admin | 2026-03-26 13:09:33.108585 |


#### Unique Value Counts (key columns)

| Column | Distinct Values |
| ------ | --------------- |
| email  | 1               |


---

## 5. Summary

| Table                    | Row Count |
| ------------------------ | --------- |
| `rbac.access_requests`   | 4         |
| `rbac.admin_credentials` | 0         |
| `rbac.allowed_emails`    | 0         |
| `rbac.auth_audit_logs`   | 9         |
| `rbac.route_definitions` | 0         |
| `rbac.route_permissions` | 0         |
| `rbac.user_roles`        | 1         |


**Exploration completed at:** `2026-04-21 22:47:05`
