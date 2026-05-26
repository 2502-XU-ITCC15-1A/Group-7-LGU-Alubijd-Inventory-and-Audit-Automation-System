from flask_mysqldb import MySQL

mysql = MySQL()


CREATE_AUDIT_LOGS_TABLE = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        item_id      INT NULL,
        user_id      INT NOT NULL,
        action_type  ENUM('CREATE', 'UPDATE', 'DELETE', 'QUANTITY_ADJUST') NOT NULL,
        old_value    TEXT,
        new_value    TEXT,
        change_reason VARCHAR(255),
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
"""

BACKFILL_AUDIT_LOGS = """
    INSERT INTO audit_logs (item_id, user_id, action_type, new_value, created_at)
    SELECT id, %s, 'CREATE', 'Initial inventory sync', date_created
    FROM inventory_items
"""


def ensure_audit_log_table(db, user_id):
    """Create the audit_logs table if absent, then backfill if empty."""
    cur = db.connection.cursor()

    cur.execute("SHOW TABLES LIKE 'audit_logs'")
    if not cur.fetchone():
        cur.execute(CREATE_AUDIT_LOGS_TABLE)
        cur.execute(BACKFILL_AUDIT_LOGS, (user_id or 1,))
        db.connection.commit()
        return

    cur.execute("SHOW COLUMNS FROM audit_logs LIKE 'change_reason'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE audit_logs ADD COLUMN change_reason VARCHAR(255)")
        db.connection.commit()

    cur.execute("SELECT COUNT(*) AS cnt FROM audit_logs")
    if cur.fetchone()["cnt"] == 0:
        cur.execute(BACKFILL_AUDIT_LOGS, (user_id or 1,))
        db.connection.commit()


def log_action(db, item_id, user_id, action_type, new_value=None, old_value=None, change_reason=None):
    """Insert a row into audit_logs."""
    cur = db.connection.cursor()
    cur.execute(
        """INSERT INTO audit_logs
               (item_id, user_id, action_type, old_value, new_value, change_reason)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (item_id, user_id, action_type, old_value, new_value, change_reason),
    )
    # Caller is responsible for committing
