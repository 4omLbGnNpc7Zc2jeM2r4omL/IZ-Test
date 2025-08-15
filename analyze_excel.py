#!/usr/bin/env python3
"""
📊 EXCEL SPALTEN ANALYSE
Analysiert die Excel-Datei um die verfügbaren Spalten zu identifizieren
"""

import pandas as pd
import sys

def analyze_excel_columns():
    """Analysiert die Excel-Spalten"""
    try:
        excel_file = "Beispieldaten Pascal.xlsx"
        print(f"📊 EXCEL-ANALYSE: {excel_file}")
        print("="*60)
        
        # Excel-Datei laden
        df = pd.read_excel(excel_file)
        
        print(f"📈 Anzahl Zeilen: {len(df)}")
        print(f"📊 Anzahl Spalten: {len(df.columns)}")
        print()
        
        print("📋 ALLE SPALTEN:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. '{col}'")
        print()
        
        print("🔍 ERSTE ZEILE DATEN:")
        if len(df) > 0:
            first_row = df.iloc[0]
            for col in df.columns:
                value = first_row[col]
                if pd.notna(value):
                    print(f"   {col}: '{value}'")
                else:
                    print(f"   {col}: (leer)")
        
        print()
        print("🎯 RELEVANTE SPALTEN FÜR RADIO-BUTTONS:")
        relevant_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in [
                'online', 'store', 'shop', 'ecommerce', 'e-commerce',
                'packaging', 'manufacturing', 'business', 'activity',
                'yes', 'no', 'ja', 'nein'
            ]):
                relevant_columns.append(col)
                print(f"   ✅ '{col}'")
                
                # Zeige unique Werte für diese Spalte
                unique_values = df[col].dropna().unique()
                print(f"      Werte: {list(unique_values)}")
        
        if not relevant_columns:
            print("   ⚠️ Keine offensichtlich relevanten Spalten gefunden")
            print("   💡 Alle Spalten prüfen:")
            for col in df.columns:
                unique_values = df[col].dropna().unique()
                if len(unique_values) <= 10:  # Nur Spalten mit wenigen unique Werten
                    print(f"      '{col}': {list(unique_values)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Excel-Datei: {e}")
        return None

if __name__ == "__main__":
    analyze_excel_columns()
