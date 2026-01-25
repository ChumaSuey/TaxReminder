import os
import json
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from models import TaxTable, TaxDate, DatabaseManager

def sync_dbs(db1_path, db2_path):
    """Syncs two database files bi-directionally."""
    print(f"🔄 Syncing databases:\n   Source: {db1_path}\n   Target: {db2_path}")
    
    if not os.path.exists(db1_path) or not os.path.exists(db2_path):
        print("⚠️ One of the databases is missing. Skipping DB sync.")
        return

    engine1 = sa.create_engine(f'sqlite:///{db1_path}')
    engine2 = sa.create_engine(f'sqlite:///{db2_path}')
    
    Session1 = sessionmaker(bind=engine1)
    Session2 = sessionmaker(bind=engine2)
    
    session1 = Session1()
    session2 = Session2()
    
    try:
        # 1. Sync TaxTables
        tables1 = {t.name: t for t in session1.query(TaxTable).all()}
        tables2 = {t.name: t for t in session2.query(TaxTable).all()}
        
        all_table_names = set(tables1.keys()).union(set(tables2.keys()))
        
        for name in all_table_names:
            t1 = tables1.get(name)
            t2 = tables2.get(name)
            
            if t1 and not t2:
                session2.add(TaxTable(name=t1.name, description=t1.description))
            elif t2 and not t1:
                session1.add(TaxTable(name=t2.name, description=t2.description))
        
        session1.commit()
        session2.commit()
        
        # 2. Sync TaxDates
        dates1 = { (d.table_name, d.month, d.day): d for d in session1.query(TaxDate).all() }
        dates2 = { (d.table_name, d.month, d.day): d for d in session2.query(TaxDate).all() }
        
        all_date_keys = set(dates1.keys()).union(set(dates2.keys()))
        
        for key in all_date_keys:
            d1 = dates1.get(key)
            d2 = dates2.get(key)
            
            if d1 and not d2:
                session2.add(TaxDate(table_name=d1.table_name, month=d1.month, day=d1.day, description=d1.description))
            elif d2 and not d1:
                session1.add(TaxDate(table_name=d2.table_name, month=d2.month, day=d2.day, description=d2.description))
            elif d1 and d2:
                # Merge descriptions if one is missing but the other has it
                if not d1.description and d2.description:
                    d1.description = d2.description
                elif not d2.description and d1.description:
                    d2.description = d1.description
        
        session1.commit()
        session2.commit()
        print("✅ Database sync completed.")
        
    except Exception as e:
        print(f"❌ Error during DB sync: {e}")
        session1.rollback()
        session2.rollback()
    finally:
        session1.close()
        session2.close()

def sync_json(file1, file2):
    """Merges two acknowledgement JSON files bi-directionally."""
    print(f"🔄 Syncing JSON files:\n   File 1: {file1}\n   File 2: {file2}")
    
    data1 = {}
    data2 = {}
    
    if os.path.exists(file1):
        with open(file1, 'r') as f:
            try:
                data1 = json.load(f)
            except: pass
            
    if os.path.exists(file2):
        with open(file2, 'r') as f:
            try:
                data2 = json.load(f)
            except: pass
            
    # Merge
    merged = {**data1, **data2}
    
    # Save back to both if they were different or new data was found
    for f_path in [file1, file2]:
        folder = os.path.dirname(f_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with open(f_path, 'w') as f:
            json.dump(merged, f, indent=4)
            
    print("✅ JSON sync completed.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, 'dist')
    
    db_name = 'tax_reminder.db'
    ack_name = 'acknowledgements.json'
    auth_name = 'authorized_users.json'
    
    root_db = os.path.join(base_dir, db_name)
    dist_db = os.path.join(dist_dir, db_name)
    
    root_ack = os.path.join(base_dir, ack_name)
    dist_ack = os.path.join(dist_dir, ack_name)

    root_auth = os.path.join(base_dir, auth_name)
    dist_auth = os.path.join(dist_dir, auth_name)
    
    # Sync Databases
    sync_dbs(root_db, dist_db)
    
    # Sync Acknowledgements
    sync_json(root_ack, dist_ack)

    # Sync Authorized Users
    sync_json(root_auth, dist_auth)

if __name__ == "__main__":
    main()
