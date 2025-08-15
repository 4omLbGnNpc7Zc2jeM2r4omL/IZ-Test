#!/usr/bin/env python3
"""
📊 EXCEL VALIDATOR - Validierung von Excel-Dateien
"""
import pandas as pd
import os

def validate_excel_file(excel_file):
    """Einfache Excel-Validierung"""
    try:
        if not os.path.exists(excel_file):
            return False
        
        df = pd.read_excel(excel_file)
        return not df.empty
        
    except Exception as e:
        print(f"❌ Excel-Validierung fehlgeschlagen: {e}")
        return False

def get_excel_row_count(excel_file):
    """Hole Anzahl der Zeilen aus Excel-Datei"""
    try:
        if not os.path.exists(excel_file):
            return 0
        
        df = pd.read_excel(excel_file)
        clean_df = df.dropna(how='all')
        return len(clean_df)
        
    except Exception as e:
        print(f"❌ Excel Row Count Fehler: {e}")
        return 0

def get_detailed_excel_validation(excel_file):
    """Detaillierte Excel-Validierung"""
    try:
        if not os.path.exists(excel_file):
            return {
                'is_valid': False,
                'error': 'Datei nicht gefunden',
                'row_count': 0,
                'found_columns': [],
                'missing_required': []
            }
        
        df = pd.read_excel(excel_file)
        
        if df.empty:
            return {
                'is_valid': False,
                'error': 'Excel-Datei ist leer',
                'row_count': 0,
                'found_columns': [],
                'missing_required': []
            }
        
        required_columns = ['Company Name', 'Country']
        found_columns = df.columns.tolist()
        missing_required = [col for col in required_columns if col not in found_columns]
        
        clean_df = df.dropna(how='all')
        row_count = len(clean_df)
        
        return {
            'is_valid': True,
            'error': None,
            'row_count': row_count,
            'found_columns': found_columns,
            'missing_required': missing_required
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': str(e),
            'row_count': 0,
            'found_columns': [],
            'missing_required': []
        }
