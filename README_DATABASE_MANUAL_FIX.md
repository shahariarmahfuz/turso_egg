# Manual Database Schema Fix Guide

## 1. When to Use This Document

This guide is intended for **emergency production recovery only**. It serves as a temporary workaround to unblock the application when a deployment fails due to schema desynchronization (e.g., the code expects a column that Alembic has not yet created). 

**Important:** This is only a stopgap measure. You must still formally fix the Alembic migration history and commit the changes to the repository afterward to ensure consistency across environments.

---

## 2. Accessing the Turso Dashboard

To manually apply a schema fix in production:
1. Log in to your [Turso Dashboard](https://turso.tech/).
2. Locate and select the affected production database from your databases list.
3. Click on the **SQL Editor** tab to open the interactive SQL console.

---

## 3. Inspect the Current Table Schema

Before making any changes, confirm the exact state of the table. You can inspect the schema and see all existing columns by executing:

```sql
PRAGMA table_info([table_name]);
```

**Example:**
```sql
PRAGMA table_info(businesses);
```

---

## 4. Check for Column Existence

Review the output from the `PRAGMA` command. Look at the `name` column in the result set to determine if the column you are attempting to add already exists. 
- If it **does not** exist, proceed to step 5.
- If it **does** exist, the issue may lie elsewhere (e.g., incorrect column type, or application caching).

---

## 5. Add the Missing Column

Use standard SQL `ALTER TABLE` syntax to apply additive schema changes.

**Example:**
```sql
ALTER TABLE businesses
ADD COLUMN dashboard_baseline_date DATE;
```
*(Replace `businesses` and `dashboard_baseline_date DATE` with your specific table and column definitions).*

---

## 6. Verify the Execution

Once the command succeeds, verify that the schema has been properly updated by running the inspection command again:

```sql
PRAGMA table_info([table_name]);
```

**Example:**
```sql
PRAGMA table_info(businesses);
```
Ensure the new column appears in the output with the correct data type.

---

## 7. Restart or Redeploy the Application

After the database schema has been corrected:
1. Go to your hosting provider (e.g., Render, Railway, VPS).
2. Manually trigger a **Restart** or **Redeploy** of the application.
3. Monitor the application logs during startup to confirm the previous crash (e.g., `no such column`) is fully resolved.

---

## 8. ⚠️ Critical Warnings

Please adhere to the following rules when executing manual SQL in production:

- **Always Create a Backup:** Take a database snapshot or backup before executing manual SQL.
- **Additive Changes Only:** Use only additive schema changes (e.g., `ADD COLUMN`, `CREATE TABLE`).
- **Never Modify Existing Data:** Do not run `UPDATE` or `DELETE` statements on business records during emergency schema fixes.
- **Never Drop Tables:** Do not use `DROP TABLE` or drop critical columns.
- **Never Modify Alembic Version Tables:** Do not manually edit the `alembic_version` table. Let the migration tools handle version tracking.

---

## 9. Troubleshooting

If you encounter errors during the manual fix, refer to the following common issues:

- **`duplicate column name`**: You attempted to add a column that already exists. No action is required for this specific alter command.
- **`no such table`**: You misspelled the table name, or you are connected to the wrong database environment. Verify the table name using `SELECT name FROM sqlite_master WHERE type='table';`.
- **`syntax error`**: There is a typo in your SQL command. Ensure you are using correct SQLite syntax (e.g., SQLite has limited `ALTER TABLE` capabilities compared to PostgreSQL/MySQL).
- **Migration Version Mismatch**: If you manually add a column and subsequently run an Alembic migration that attempts to add the same column, the migration will crash. You must ensure your Alembic migrations include idempotency checks (e.g., `if column_exists: return`) or use `--autogenerate` carefully after fixing the manual state.
