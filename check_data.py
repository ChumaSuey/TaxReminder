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

def check_json(json_path, label, outfile):
    outfile.write(f"\n--- Checking JSON: {label} ({json_path}) ---\n")
    if not os.path.exists(json_path):
        outfile.write("  ❌ JSON file not found\n")
        return

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        outfile.write(f"  > Total acknowledgements: {len(data)}\n")
        recent_keys = [k for k in data.keys() if k.startswith("2026_") or "2026" in k]
        
        if not recent_keys:
            outfile.write("    No 2026 acknowledgements found.\n")
        else:
            for k in recent_keys:
                outfile.write(f"    - {k}: Paid on {data[k]}\n")
                
    except Exception as e:
        outfile.write(f"  ❌ Error reading JSON: {e}\n")

def main():
    base_dir = os.getcwd()
    dist_dir = os.path.join(base_dir, 'dist')
    
    with open('result.txt', 'w', encoding='utf-8') as outfile:
        # Root
        check_db(os.path.join(base_dir, 'tax_reminder.db'), "ROOT", outfile)
        check_json(os.path.join(base_dir, 'acknowledgements.json'), "ROOT", outfile)
        
        # Dist
        check_db(os.path.join(dist_dir, 'tax_reminder.db'), "DIST", outfile)
        check_json(os.path.join(dist_dir, 'acknowledgements.json'), "DIST", outfile)

if __name__ == "__main__":
    main()
