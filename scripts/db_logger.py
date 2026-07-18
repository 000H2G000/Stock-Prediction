import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "decisions.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            product TEXT NOT NULL,
            region TEXT NOT NULL,
            predicted_demand REAL NOT NULL,
            safety_stock REAL NOT NULL,
            current_stock REAL NOT NULL,
            reserved_stock REAL NOT NULL,
            avg_sales_30d REAL NOT NULL,
            lead_time REAL NOT NULL,
            reliability REAL NOT NULL,
            max_capacity REAL NOT NULL,
            reorder_quantity REAL NOT NULL,
            status TEXT NOT NULL, -- 'Pending', 'Approved', 'Rejected', 'No Action Needed'
            explanation TEXT,
            supplier_action TEXT,
            approved_by TEXT
        )
    """)

    # Migrate older tables that may not include new columns
    try:
        cursor.execute("SELECT supplier_action FROM decisions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE decisions ADD COLUMN supplier_action TEXT")
    try:
        cursor.execute("SELECT approved_by FROM decisions LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE decisions ADD COLUMN approved_by TEXT")

    conn.commit()
    conn.close()
    print("SQLite Database initialized at:", DB_PATH)

def log_decision(product, region, predicted_demand, safety_stock, current_stock, reserved_stock, avg_sales_30d, lead_time, reliability, max_capacity, reorder_quantity, status, explanation, supplier_action=None, approved_by=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO decisions (
            timestamp, product, region, predicted_demand, safety_stock, current_stock,
            reserved_stock, avg_sales_30d, lead_time, reliability, max_capacity,
            reorder_quantity, status, explanation, supplier_action, approved_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, product, region, predicted_demand, safety_stock, current_stock,
        reserved_stock, avg_sales_30d, lead_time, reliability, max_capacity,
        reorder_quantity, status, explanation, supplier_action, approved_by
    ))
    decision_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return decision_id

def update_decision_status(decision_id, status, approved_by=None, supplier_action=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if supplier_action is not None:
        cursor.execute("UPDATE decisions SET status = ?, approved_by = ?, supplier_action = ? WHERE id = ?", (status, approved_by, supplier_action, decision_id))
    else:
        cursor.execute("UPDATE decisions SET status = ?, approved_by = ? WHERE id = ?", (status, approved_by, decision_id))
    conn.commit()
    conn.close()

def get_decision_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM decisions ORDER BY timestamp DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

if __name__ == "__main__":
    init_db()
