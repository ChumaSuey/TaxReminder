import os
import shutil
import sys

def copy_db_to_dist():
    """
    Copies the tax_reminder.db file from the project root to the dist folder.
    This ensures the executable has the latest version of the database.
    """
    # Determine base directory
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths
    source_db = os.path.join(base_dir, 'tax_reminder.db')
    dist_dir = os.path.join(base_dir, 'dist')
    dest_db = os.path.join(dist_dir, 'tax_reminder.db')

    # Check if source DB exists
    if not os.path.exists(source_db):
        print(f"❌ Error: Source database not found at {source_db}")
        return False

    # Check if dist directory exists, create if not
    if not os.path.exists(dist_dir):
        print(f"⚠️ 'dist' directory not found. Creating it at {dist_dir}...")
        os.makedirs(dist_dir)

    try:
        # Perform the copy
        shutil.copy2(source_db, dest_db)
        print(f"✅ Successfully copied database to: {dest_db}")
        return True
    except Exception as e:
        print(f"❌ Error copying database: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting database copy process...")
    copy_db_to_dist()
    input("\nPress Enter to exit...")
