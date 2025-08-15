#!/usr/bin/env python3
"""
🗃️ INTERZERO DATABASE - Minimale SQLite Database für Logging
"""
import sqlite3
import json
import os

class InterzeroDatabase:
    def __init__(self, db_path="interzero_automation.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialisiere Database-Tabellen"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    country TEXT,
                    email TEXT,
                    excel_file TEXT,
                    pdf_file TEXT,
                    row_index INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS http_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER,
                    url TEXT,
                    method TEXT,
                    page_title TEXT,
                    form_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER,
                    page_number INTEGER,
                    form_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id INTEGER,
                    evidence_type TEXT,
                    evidence_data TEXT,
                    data_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database initialisiert")
            
        except Exception as e:
            print(f"⚠️ Database-Fehler: {e}")
    
    def create_submission(self, record, excel_file, row_index, pdf_file=None):
        """Erstelle neue Submission"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            company_name = record.get('Company Name', '')
            country = record.get('Country', '')
            email = record.get('Email', '')
            
            cursor.execute('''
                SELECT id FROM submissions 
                WHERE company_name = ? AND row_index = ? AND excel_file = ?
            ''', (company_name, row_index, excel_file))
            
            existing = cursor.fetchone()
            if existing:
                submission_id = existing[0]
                print(f"📊 Submission bereits vorhanden: ID={submission_id}")
            else:
                cursor.execute('''
                    INSERT INTO submissions (company_name, country, email, excel_file, pdf_file, row_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (company_name, country, email, excel_file, pdf_file, row_index))
                submission_id = cursor.lastrowid
                print(f"📊 Neue Submission erstellt: ID={submission_id}")
            
            conn.commit()
            conn.close()
            return submission_id
            
        except Exception as e:
            print(f"❌ Database-Fehler: {e}")
            return 1
    
    def log_http_request(self, submission_id, url, method, page_title="", form_data=None):
        """Logge HTTP-Request"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            form_data_json = json.dumps(form_data) if form_data else None
            
            cursor.execute('''
                INSERT INTO http_requests (submission_id, url, method, page_title, form_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (submission_id, url, method, page_title, form_data_json))
            
            conn.commit()
            conn.close()
            print(f"🌐 HTTP-Request geloggt: {method} {url}")
            
        except Exception as e:
            print(f"⚠️ HTTP-Request Logging-Fehler: {e}")
    
    def log_form_fields(self, submission_id, page_number, form_data):
        """Logge Formularfelder"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            form_data_json = json.dumps(form_data)
            
            cursor.execute('''
                INSERT INTO form_fields (submission_id, page_number, form_data)
                VALUES (?, ?, ?)
            ''', (submission_id, page_number, form_data_json))
            
            conn.commit()
            conn.close()
            print(f"📝 ✅ {len(form_data)} Formularfelder für Seite {page_number} geloggt")
            
        except Exception as e:
            print(f"⚠️ Form-Fields Logging-Fehler: {e}")
    
    def log_evidence(self, submission_id, evidence_type, evidence_data, data_type="text"):
        """Logge Evidence"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO evidence (submission_id, evidence_type, evidence_data, data_type)
                VALUES (?, ?, ?, ?)
            ''', (submission_id, evidence_type, evidence_data, data_type))
            
            conn.commit()
            conn.close()
            print(f"📸 Evidence geloggt: {evidence_type}")
            
        except Exception as e:
            print(f"⚠️ Evidence Logging-Fehler: {e}")
