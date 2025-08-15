#!/usr/bin/env python3
"""
🖥️ GUI für Dateiauswahl - Interzero Automation
Erweiterte tkinter GUI mit Excel-Validierung und Mehrfach-Durchlauf-Unterstützung
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
from excel_validator import validate_excel_file, get_excel_row_count, get_detailed_excel_validation

class FileSelectionGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Interzero Automation - Dateiauswahl")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Variablen für gewählte Dateien
        self.excel_file = None
        self.pdf_file = None
        self.cancelled = False
        self.excel_valid = False
        self.excel_row_count = 0
        self.excel_validation_details = []
        self.validation_details = None  # Für detaillierte Validierung
        
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titel
        title_label = ttk.Label(main_frame, text="🚀 Interzero Automation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="Wählen Sie die Dateien für die Automation aus:",
                                  font=("Arial", 10))
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Excel-Datei Sektion
        excel_frame = ttk.LabelFrame(main_frame, text="📊 Excel-Datei (Erforderlich)", padding="10")
        excel_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.excel_label = ttk.Label(excel_frame, text="Keine Datei ausgewählt", 
                                    foreground="red")
        self.excel_label.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))
        
        excel_btn = ttk.Button(excel_frame, text="Excel wählen...", 
                              command=self.select_excel_file)
        excel_btn.grid(row=0, column=1)
        
        # Excel-Validierung Anzeige
        self.excel_validation_frame = ttk.Frame(excel_frame)
        self.excel_validation_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.validation_label = ttk.Label(self.excel_validation_frame, text="", font=("Arial", 9))
        self.validation_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.row_count_label = ttk.Label(self.excel_validation_frame, text="", font=("Arial", 9, "bold"))
        self.row_count_label.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Details Button für Validierung
        self.details_btn = ttk.Button(self.excel_validation_frame, text="📋 Details anzeigen", 
                                     command=self.show_validation_details, state="disabled")
        self.details_btn.grid(row=2, column=0, pady=(5, 0), sticky=(tk.W))
        
        # Variablen für Validierungsdetails
        self.validation_details = None
        
        # PDF-Datei Sektion
        pdf_frame = ttk.LabelFrame(main_frame, text="📄 PDF-Datei (Optional)", padding="10")
        pdf_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.pdf_label = ttk.Label(pdf_frame, text="Keine Datei ausgewählt", 
                                  foreground="gray")
        self.pdf_label.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))
        
        pdf_btn = ttk.Button(pdf_frame, text="PDF wählen...", 
                            command=self.select_pdf_file)
        pdf_btn.grid(row=0, column=1)
        
        pdf_clear_btn = ttk.Button(pdf_frame, text="Entfernen", 
                                  command=self.clear_pdf_file)
        pdf_clear_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Aktionsbuttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(20, 0))
        
        self.start_btn = ttk.Button(button_frame, text="🚀 Automation starten", 
                                   command=self.start_automation, state="disabled",
                                   style="Accent.TButton")
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Abbrechen", 
                               command=self.cancel)
        cancel_btn.grid(row=0, column=1)
        
        # Statusleiste
        self.status_label = ttk.Label(main_frame, text="Bitte wählen Sie eine Excel-Datei aus",
                                     foreground="blue")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(20, 0))
        
        # Grid-Konfiguration
        main_frame.columnconfigure(0, weight=1)
        excel_frame.columnconfigure(0, weight=1)
        pdf_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def select_excel_file(self):
        """Excel-Datei auswählen und validieren"""
        file_path = filedialog.askopenfilename(
            title="Excel-Datei auswählen",
            filetypes=[
                ("Excel-Dateien", "*.xlsx *.xls"),
                ("Alle Dateien", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.excel_file = file_path
            filename = os.path.basename(file_path)
            self.excel_label.config(text=filename, foreground="blue")
            
            # Excel validieren
            self.validate_excel()
            
    def validate_excel(self):
        """Validiert die ausgewählte Excel-Datei mit detaillierten Informationen"""
        if not self.excel_file:
            return
            
        try:
            # Detaillierte Validierung durchführen
            self.validation_details = get_detailed_excel_validation(self.excel_file)
            
            is_valid = self.validation_details['is_valid']
            row_count = self.validation_details['row_count']
            
            self.excel_valid = is_valid
            self.excel_row_count = row_count
            
            if is_valid:
                self.validation_label.config(text="✅ Excel-Validierung erfolgreich", foreground="green")
                self.excel_label.config(foreground="green")
                self.start_btn.config(state="normal")
                self.details_btn.config(state="normal")
                
                if row_count > 1:
                    self.row_count_label.config(
                        text=f"🔄 {row_count} Zeilen gefunden → {row_count} Automation-Durchläufe", 
                        foreground="orange"
                    )
                    self.status_label.config(
                        text=f"Bereit für {row_count} Automation-Durchläufe!", 
                        foreground="green"
                    )
                else:
                    self.row_count_label.config(text="📋 1 Zeile → 1 Automation-Durchlauf", foreground="green")
                    self.status_label.config(text="Excel validiert. Optional: PDF-Datei wählen", foreground="green")
                    
            else:
                self.validation_label.config(text="❌ Excel-Validierung fehlgeschlagen", foreground="red")
                self.excel_label.config(foreground="red")
                self.row_count_label.config(text="", foreground="black")
                self.start_btn.config(state="disabled")
                self.details_btn.config(state="normal")  # Details auch bei Fehlern anzeigen
                self.status_label.config(text="Excel-Validierung fehlgeschlagen - Details anzeigen", foreground="red")
                
        except Exception as e:
            self.validation_label.config(text=f"❌ Validierungsfehler: {str(e)}", foreground="red")
            self.excel_label.config(foreground="red")
            self.row_count_label.config(text="", foreground="black")
            self.start_btn.config(state="disabled")
            self.details_btn.config(state="disabled")
            self.status_label.config(text="Fehler bei Excel-Validierung", foreground="red")
            
            messagebox.showerror(
                "Validierungsfehler",
                f"Fehler bei der Excel-Validierung:\n\n{str(e)}"
            )
            
    def select_pdf_file(self):
        """PDF-Datei auswählen"""
        file_path = filedialog.askopenfilename(
            title="PDF-Datei auswählen",
            filetypes=[
                ("PDF-Dateien", "*.pdf"),
                ("Alle Dateien", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        if file_path:
            self.pdf_file = file_path
            filename = os.path.basename(file_path)
            self.pdf_label.config(text=filename, foreground="green")
            self.status_label.config(text="Excel und PDF ausgewählt. Bereit zum Start!",
                                   foreground="green")
            
    def show_validation_details(self):
        """Zeigt detaillierte Validierungsinformationen in einem neuen Fenster"""
        if not self.validation_details:
            messagebox.showwarning("Keine Details", "Keine Validierungsdetails verfügbar")
            return
        
        # Neues Fenster erstellen
        details_window = tk.Toplevel(self.root)
        details_window.title("📋 Excel-Validierung Details")
        details_window.geometry("800x600")
        details_window.resizable(True, True)
        
        # Hauptframe mit Scrollbar
        main_frame = ttk.Frame(details_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas und Scrollbar für scrollbaren Inhalt
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Titel
        title_label = ttk.Label(scrollable_frame, 
                               text=f"📊 Excel-Validierung: {os.path.basename(self.excel_file)}", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Übersicht
        overview_frame = ttk.LabelFrame(scrollable_frame, text="📈 Übersicht", padding="10")
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        overview_text = f"""✅ Gültig: {'Ja' if self.validation_details['is_valid'] else 'Nein'}
📋 Anzahl Zeilen: {self.validation_details['row_count']}
📊 Gefundene Spalten: {len(self.validation_details['found_columns'])}
❌ Fehlende Pflichtfelder: {len(self.validation_details['missing_required'])}
⚠️ Fehlende optionale Felder: {len(self.validation_details['missing_optional'])}
🚨 Zeilen mit Fehlern: {len(self.validation_details['row_errors'])}"""
        
        overview_label = ttk.Label(overview_frame, text=overview_text, font=("Courier New", 10))
        overview_label.pack(anchor="w")
        
        # Gefundene Spalten
        if self.validation_details['found_columns']:
            columns_frame = ttk.LabelFrame(scrollable_frame, text="✅ Gefundene Spalten", padding="10")
            columns_frame.pack(fill=tk.X, pady=(0, 10))
            
            columns_text = ""
            for i, col in enumerate(self.validation_details['found_columns'], 1):
                columns_text += f"{i:2d}. '{col}'\n"
            
            columns_label = ttk.Label(columns_frame, text=columns_text.strip(), 
                                    font=("Courier New", 9), justify="left")
            columns_label.pack(anchor="w")
        
        # Fehlende Pflichtfelder
        if self.validation_details['missing_required']:
            missing_frame = ttk.LabelFrame(scrollable_frame, text="❌ Fehlende Pflichtfelder", padding="10")
            missing_frame.pack(fill=tk.X, pady=(0, 10))
            
            missing_text = ""
            for missing in self.validation_details['missing_required']:
                missing_text += f"• {missing}\n"
            
            missing_label = ttk.Label(missing_frame, text=missing_text.strip(), 
                                    font=("Courier New", 9), foreground="red", justify="left")
            missing_label.pack(anchor="w")
        
        # Fehlende optionale Felder
        if self.validation_details['missing_optional']:
            optional_frame = ttk.LabelFrame(scrollable_frame, text="⚠️ Fehlende optionale Felder", padding="10")
            optional_frame.pack(fill=tk.X, pady=(0, 10))
            
            optional_text = ""
            for optional in self.validation_details['missing_optional']:
                optional_text += f"• {optional}\n"
            
            optional_label = ttk.Label(optional_frame, text=optional_text.strip(), 
                                     font=("Courier New", 9), foreground="orange", justify="left")
            optional_label.pack(anchor="w")
        
        # Zeilen-Fehler
        if self.validation_details['row_errors']:
            errors_frame = ttk.LabelFrame(scrollable_frame, text="🚨 Fehler in Datensätzen", padding="10")
            errors_frame.pack(fill=tk.X, pady=(0, 10))
            
            for error_info in self.validation_details['row_errors']:
                if error_info.get('row', -1) >= 0:  # Zeilen-spezifische Fehler
                    row_text = f"🔸 Zeile {error_info['row']} ({error_info.get('company', 'Unbekannt')}):\n"
                    for error in error_info['errors']:
                        row_text += f"   • {error}\n"
                    row_text += "\n"
                    
                    row_label = ttk.Label(errors_frame, text=row_text.strip(), 
                                        font=("Courier New", 9), foreground="red", justify="left")
                    row_label.pack(anchor="w", pady=(0, 5))
                else:  # Allgemeine Fehler
                    general_text = f"🚨 {error_info['error']}\n"
                    general_label = ttk.Label(errors_frame, text=general_text.strip(), 
                                            font=("Courier New", 9), foreground="red", justify="left")
                    general_label.pack(anchor="w", pady=(0, 5))
        
        # Preview Daten
        if self.validation_details['preview_data']:
            preview_frame = ttk.LabelFrame(scrollable_frame, text="👁️ Vorschau (erste Zeile)", padding="10")
            preview_frame.pack(fill=tk.X, pady=(0, 10))
            
            preview_text = ""
            for key, value in self.validation_details['preview_data'].items():
                preview_text += f"{key}: {value}\n"
            
            preview_label = ttk.Label(preview_frame, text=preview_text.strip(), 
                                    font=("Courier New", 9), justify="left")
            preview_label.pack(anchor="w")
        
        # Schließen Button
        close_btn = ttk.Button(scrollable_frame, text="Schließen", 
                              command=details_window.destroy)
        close_btn.pack(pady=20)
        
        # Canvas und Scrollbar packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mausrad-Unterstützung
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

    def clear_pdf_file(self):
        """PDF-Datei entfernen"""
        self.pdf_file = None
        self.pdf_label.config(text="Keine Datei ausgewählt", foreground="gray")
        if self.excel_file:
            self.status_label.config(text="Excel-Datei ausgewählt. Optional: PDF-Datei wählen",
                                   foreground="green")
            
    def start_automation(self):
        """Automation starten"""
        if not self.excel_file:
            messagebox.showerror("Fehler", "Bitte wählen Sie eine Excel-Datei aus!")
            return
            
        if not self.excel_valid:
            messagebox.showerror("Fehler", "Die Excel-Datei ist nicht gültig! Bitte wählen Sie eine andere Datei.")
            return
            
        # Bestätigung mit Durchlauf-Information
        pdf_text = f"\nPDF: {os.path.basename(self.pdf_file)}" if self.pdf_file else "\nPDF: Keine"
        
        if self.excel_row_count > 1:
            message = (f"Automation starten mit:\n"
                      f"Excel: {os.path.basename(self.excel_file)}{pdf_text}\n\n"
                      f"⚠️ WICHTIG: {self.excel_row_count} Zeilen gefunden!\n"
                      f"Es werden {self.excel_row_count} separate Automation-Durchläufe ausgeführt.\n"
                      f"Jede Zeile = 1 Durchlauf = 1 Submission in der Datenbank.\n\n"
                      f"Möchten Sie fortfahren?")
        else:
            message = f"Automation starten mit:\nExcel: {os.path.basename(self.excel_file)}{pdf_text}\n\n1 Zeile → 1 Automation-Durchlauf"
        
        if messagebox.askyesno("Automation starten", message):
            self.root.destroy()
            
    def cancel(self):
        """Abbrechen"""
        self.cancelled = True
        self.root.destroy()
        
    def run(self):
        """GUI anzeigen und auf Auswahl warten"""
        self.root.mainloop()
        
        if self.cancelled:
            return None, None
        else:
            return self.excel_file, self.pdf_file

def select_files_gui():
    """Hauptfunktion für GUI-Dateiauswahl"""
    try:
        gui = FileSelectionGUI()
        excel_file, pdf_file = gui.run()
        
        if excel_file is None:
            print("❌ Dateiauswahl abgebrochen")
            return None, None
            
        print(f"✅ Dateien gewählt:")
        print(f"   📊 Excel: {os.path.basename(excel_file)}")
        print(f"   📄 PDF: {os.path.basename(pdf_file) if pdf_file else 'Keine'}")
        
        return excel_file, pdf_file
        
    except Exception as e:
        print(f"❌ GUI-Fehler: {e}")
        print("📝 Fallback zur Konsolen-Auswahl...")
        return None, None

if __name__ == "__main__":
    # Test der GUI
    excel, pdf = select_files_gui()
    if excel:
        print(f"Test erfolgreich: Excel={excel}, PDF={pdf}")
    else:
        print("Test abgebrochen oder fehlgeschlagen")
