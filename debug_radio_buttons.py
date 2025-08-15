#!/usr/bin/env python3
"""
🔍 DEBUG: Radio-Button-Problem Analyse
Testet warum Radio-Buttons nicht korrekt ausgewählt werden
"""

def debug_radio_button_logic():
    """Debug der Radio-Button-Auswahllogik"""
    print("🔍 DEBUG: Radio-Button-Problem Analyse")
    print("="*60)
    
    # Echte Excel-Daten
    excel_data = {
        'Does your client have an online store?': 'Yes ',
        'In their online store, my client sells…': 'Products they own'
    }
    
    # Bereinigung (wie im echten Code)
    online_store = str(excel_data.get('Does your client have an online store?', '') or '').lower().strip()
    online_store_sells = str(excel_data.get('In their online store, my client sells…', '') or '').strip()
    
    print(f"📊 BEREINIGTE EXCEL-DATEN:")
    print(f"   🛒 Online Store: '{online_store}'")
    print(f"   🛍️ Online Store Sells: '{online_store_sells}'")
    
    # Simulierte Radio-Buttons (basierend auf echtem Output)
    mock_radios = [
        {'value': 'yes', 'name': 'has_online_store', 'id': 'online_yes', 'label': 'Yes'},
        {'value': 'no', 'name': 'has_online_store', 'id': 'online_no', 'label': 'No'},
        # Diese kommen erst nach dem ersten Klick (Phase 2)
        {'value': 'own_products', 'name': 'sells_what', 'id': 'sells_own', 'label': 'Products they own'},
        {'value': 'vendor_products', 'name': 'sells_what', 'id': 'sells_vendor', 'label': 'Products owned by other vendors'},
        {'value': 'both', 'name': 'sells_what', 'id': 'sells_both', 'label': 'Both'}
    ]
    
    print(f"\n🎯 PHASE 1 TEST - ONLINE STORE JA/NEIN:")
    
    # Phase 1: Online Store
    for radio in mock_radios[:2]:  # Nur erste 2 (Phase 1)
        radio_text = f"{radio['value']} {radio['name']} {radio['id']} {radio['label']}"
        should_select = False
        reason = ""
        
        if online_store in ['yes', 'ja', 'true', '1', 'x', 'y']:
            if any(yes_keyword in radio_text for yes_keyword in ['yes', 'ja', 'true']):
                if not any(no_keyword in radio_text for no_keyword in ['no', 'nein', 'false', 'not', 'kein']):
                    should_select = True
                    reason = f"JA-Option für Online Store (Excel: '{online_store}')"
        
        print(f"   📻 {radio['label']}: {'✅ AUSWÄHLEN' if should_select else '❌ NICHT'}")
        if should_select:
            print(f"      📋 Grund: {reason}")
    
    print(f"\n🎯 PHASE 2 TEST - ONLINE STORE SELLS:")
    
    # Phase 2: Online Store Sells
    for radio in mock_radios[2:]:  # Phase 2 Radio-Buttons
        radio_text = f"{radio['value']} {radio['name']} {radio['id']} {radio['label']}"
        should_select = False
        reason = ""
        
        if online_store_sells:
            sells_keywords = online_store_sells.lower().split()
            for keyword in sells_keywords:
                if len(keyword) > 2:  # Ignoriere "they"
                    if keyword in radio_text:
                        should_select = True
                        reason = f"Online Store Sells Match: '{keyword}' (Excel: '{online_store_sells}')"
                        break
        
        print(f"   📻 {radio['label']}: {'✅ AUSWÄHLEN' if should_select else '❌ NICHT'}")
        if should_select:
            print(f"      📋 Grund: {reason}")
    
    print(f"\n🚨 MÖGLICHE PROBLEME:")
    print(f"   1. Phase 2 Radio-Buttons werden nicht gefunden")
    print(f"   2. DOM-Update dauert länger als 1 Sekunde")
    print(f"   3. CSS-Selector findet nicht alle Radio-Buttons")
    print(f"   4. Label-Text wird nicht korrekt extrahiert")
    print(f"   5. Keywords matchen nicht (case-sensitive?)")
    
    print(f"\n💡 LÖSUNGSANSÄTZE:")
    print(f"   1. Längere Wartezeit nach Phase 1 (2-3 Sekunden)")
    print(f"   2. Mehrere CSS-Selektoren verwenden")
    print(f"   3. Explizites Warten auf neue Elemente")
    print(f"   4. Debug-Output für alle gefundenen Radio-Buttons")

if __name__ == "__main__":
    debug_radio_button_logic()
