import os
import json
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from models import Base, TaxTable, TaxDate, TaxPayment, DatabaseManager

def sync_dbs(db1_path, db2_path):
    """Syncs two database files bi-directionally."""
    print(f"🔄 Syncing databases:\n   Source: {db1_path}\n   Target: {db2_path}")
    
    if not os.path.exists(db1_path) or not os.path.exists(db2_path):
        print("⚠️ One of the databases is missing. Skipping DB sync.")
        return

    engine1 = sa.create_engine(f'sqlite:///{db1_path}')
    engine2 = sa.create_engine(f'sqlite:///{db2_path}')
    
    # Ensure tables exist in both
    Base.metadata.create_all(engine1)
    Base.metadata.create_all(engine2)
    
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
        
        # 2. Sync TaxDates (refresh to get IDs)
        dates1_list = session1.query(TaxDate).all()
        dates2_list = session2.query(TaxDate).all()
        dates1 = { (d.table_name, d.month, d.day): d for d in dates1_list }
        dates2 = { (d.table_name, d.month, d.day): d for d in dates2_list }
        
        all_date_keys = set(dates1.keys()).union(set(dates2.keys()))
        
        for key in all_date_keys:
            d1 = dates1.get(key)
            d2 = dates2.get(key)
            
            if d1 and not d2:
                session2.add(TaxDate(table_name=d1.table_name, month=d1.month, day=d1.day, description=d1.description))
            elif d2 and not d1:
                session1.add(TaxDate(table_name=d2.table_name, month=d2.month, day=d2.day, description=d2.description))
            elif d1 and d2:
                if not d1.description and d2.description:
                    d1.description = d2.description
                elif not d2.description and d1.description:
                    d2.description = d1.description
        
        session1.commit()
        session2.commit()

        # 3. Sync TaxPayments
        # We need to map tax_date_id correctly between DBs by matching natural keys
        # Natural key for TaxDate: (table_name, month, day)
        def get_payment_data(session):
            return {
                (d.table_name, d.month, d.day, p.year): p.payment_date 
                for p, d in session.query(TaxPayment, TaxDate).join(TaxDate).all()
            }
        
        pay1 = get_payment_data(session1)
        pay2 = get_payment_data(session2)
        
        all_pay_keys = set(pay1.keys()).union(set(pay2.keys()))
        
        # Reload maps to get new IDs if inserted
        d1_map = { (d.table_name, d.month, d.day): d.id for d in session1.query(TaxDate).all() }
        d2_map = { (d.table_name, d.month, d.day): d.id for d in session2.query(TaxDate).all() }

        for key in all_pay_keys:
            # key is (table_name, month, day, year)
            date_key = key[:3]
            year = key[3]
            date_str1 = pay1.get(key)
            date_str2 = pay2.get(key)
            
            if date_str1 and not date_str2:
                if date_key in d2_map:
                    session2.add(TaxPayment(tax_date_id=d2_map[date_key], year=year, payment_date=date_str1))
            elif date_str2 and not date_str1:
                if date_key in d1_map:
                    session1.add(TaxPayment(tax_date_id=d1_map[date_key], year=year, payment_date=date_str2))
        
        session1.commit()
        session2.commit()
        
        print("✅ Database sync completed (including payments).")
        
    except Exception as e:
        print(f"❌ Error during DB sync: {e}")
        session1.rollback()
        session2.rollback()
    finally:
        session1.close()
        session2.close()

def sync_json(file1, file2):
    """Merges two JSON files bi-directionally."""
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
    
    # Save back
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
    auth_name = 'authorized_users.json'
    
    root_db = os.path.join(base_dir, db_name)
    dist_db = os.path.join(dist_dir, db_name)
    
    root_auth = os.path.join(base_dir, auth_name)
    dist_auth = os.path.join(dist_dir, auth_name)
    
    # Sync Databases
    sync_dbs(root_db, dist_db)
    
    # Sync Authorized Users
    sync_json(root_auth, dist_auth)

if __name__ == "__main__":
    main()
