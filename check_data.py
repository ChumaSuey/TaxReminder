import os
import json
import sqlite3
import sys

def check_db(db_path, label, outfile):
    outfile.write(f"\n--- Checking DB: {label} ({db_path}) ---\n")
    if not os.path.exists(db_path):
        outfile.write("  ❌ Database file not found\n")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        outfile.write("  > Taxes for January:\n")
        cur.execute("""
            SELECT t.name, d.month, d.day, d.description 
            FROM tax_dates d 
            JOIN tables t ON d.table_name = t.name 
            WHERE d.month = 1 AND d.day >= 20
        """)
        rows = cur.fetchall()
        if not rows:
            outfile.write("    No taxes found for late Jan.\n")
        for row in rows:
            outfile.write(f"    - {row[0]}: Jan {row[2]} ({row[3]})\n")
            
        conn.close()
    except Exception as e:
        outfile.write(f"  ❌ Error reading DB: {e}\n")

def check_db_payments(db_path, label, outfile):
    outfile.write(f"\n--- Checking Payments DB: {label} ({db_path}) ---\n")
    if not os.path.exists(db_path):
        outfile.write("  ❌ Database file not found\n")
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM tax_payments")
        count = cur.fetchone()[0]
        outfile.write(f"  > Total payments recorded: {count}\n")
        
        cur.execute("""
            SELECT p.year, t.description, p.payment_date 
            FROM tax_payments p
            JOIN tax_dates d ON p.tax_date_id = d.id
            JOIN tables t ON d.table_name = t.name
            LIMIT 10
        """)
        rows = cur.fetchall()
        if not rows:
            outfile.write("    No payments recorded yet.\n")
        else:
            for row in rows:
                outfile.write(f"    - {row[1]} ({row[0]}): Paid on {row[2]}\n")
                
        conn.close()
    except Exception as e:
        outfile.write(f"  ❌ Error reading Payments DB: {e}\n")

def main():
    base_dir = os.getcwd()
    dist_dir = os.path.join(base_dir, 'dist')
    
    with open('result.txt', 'w', encoding='utf-8') as outfile:
        # Root
        check_db(os.path.join(base_dir, 'tax_reminder.db'), "ROOT", outfile)
        check_db_payments(os.path.join(base_dir, 'tax_reminder.db'), "ROOT", outfile)
        
        # Dist
        check_db(os.path.join(dist_dir, 'tax_reminder.db'), "DIST", outfile)
        check_db_payments(os.path.join(dist_dir, 'tax_reminder.db'), "DIST", outfile)

if __name__ == "__main__":
    main()
