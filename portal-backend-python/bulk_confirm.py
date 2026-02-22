#!/usr/bin/env python3
"""
Bulk confirm accepted applications from a txt file.
Only considers applications where form_key is "2026-cfg-application".
"""

import sys
import uuid
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.application import Application, ApplicationStatus

# Configuration from Environment
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_port = os.getenv("DB_PORT", "5432")

DB_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
FORM_KEY_FILTER = "2026-cfg-application"

def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def bulk_confirm(txt_file: str):
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    confirmed_count = 0
    not_found_count = 0
    not_accepted_count = 0

    try:
        with open(txt_file, 'r') as f:
            lines = f.readlines()

        for line in lines:
            identifier = line.strip()
            if not identifier:
                continue

            application = None

            # Base query with the specific form_key filter
            base_query = session.query(Application).filter(Application.form_key == FORM_KEY_FILTER)

            if is_valid_uuid(identifier):
                # Search by UUID + Form Key
                application = base_query.filter(Application.user_id == identifier).first()
            
            if not application:
                # Search by email inside submission_json + Form Key
                # PostgreSQL specific JSONB query; if using SQLite/other, you might need app.submission_json['email'].astext
                application = base_query.filter(
                    Application.submission_json['email'].astext.ilike(identifier)
                ).first()

            if not application:
                print(f"NOT FOUND or WRONG FORM: {identifier}")
                not_found_count += 1
                continue

            # Check status
            if application.status != ApplicationStatus.ACCEPTED:
                print(f"SKIPPED (status={application.status.value}): {identifier}")
                not_accepted_count += 1
                continue

            # Update status
            application.status = ApplicationStatus.CONFIRMED
            print(f"CONFIRMED: {identifier} (app_id: {application.id})")
            confirmed_count += 1

        session.commit()
        print(f"\n--- Summary ({FORM_KEY_FILTER}) ---")
        print(f"Confirmed: {confirmed_count}")
        print(f"Not found/Wrong form: {not_found_count}")
        print(f"Not accepted (skipped): {not_accepted_count}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bulk_confirm.py <input.txt>")
        sys.exit(1)

    bulk_confirm(sys.argv[1])