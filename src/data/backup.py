# script to backup ../data.db to ./data_backup_{YY-MM-DD}.db

import os
import shutil
import datetime
import sys

print(os.path.dirname(__file__))

def backup_database():
    # Get the current date
    current_date = datetime.datetime.now().strftime("%y-%m-%d")

    # Define the source and destination paths
    source_path = os.path.join(os.path.dirname(__file__), '..', 'data.db')
    destination_path = os.path.join(os.path.dirname(__file__), f'data_abu_{current_date}.db')

    # Check if the source file exists
    if not os.path.exists(source_path):
        print(f"Source file {source_path} does not exist.")
        sys.exit(1)

    # Copy the file to the backup location
    shutil.copy2(source_path, destination_path)
    print(f"Backup of {source_path} created at {destination_path}")


if __name__ == "__main__":
    backup_database()
