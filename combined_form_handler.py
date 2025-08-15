def handle_combined_packaging_form(driver, submission_id):
    """Behandelt kombinierte Packaging-Form mit Company und Country Feldern"""
    try:
        print("🏢 KOMBINIERTE PACKAGING-FORM HANDLER")
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        
        # Analysiere alle verfügbaren Form-Felder
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        all_selects = driver.find_elements(By.TAG_NAME, "select")
        
        print(f"📝 Gefundene Inputs: {len(all_inputs)}")
        print(f"📋 Gefundene Selects: {len(all_selects)}")
        
        # Finde spezifische Felder
        company_field = None
        country_field = None
        email_field = None
        radio_buttons = []
        
        # Analysiere Input-Felder
        for inp in all_inputs:
            try:
                name = (inp.get_attribute('name') or '').lower()
                id_attr = (inp.get_attribute('id') or '').lower()
                placeholder = (inp.get_attribute('placeholder') or '').lower()
                inp_type = (inp.get_attribute('type') or 'text').lower()
                
                combined = f"{name} {id_attr} {placeholder}"
                print(f"🔍 Input: type={inp_type}, name={name}, id={id_attr}, placeholder={placeholder}")
                
                if inp_type == 'radio' and inp.is_displayed():
                    radio_buttons.append(inp)
                elif 'company' in combined and inp.is_displayed():
                    company_field = inp
                    print(f"✅ Company-Feld gefunden: {name}")
                elif 'email' in combined and inp.is_displayed():
                    email_field = inp
                    print(f"✅ Email-Feld gefunden: {name}")
                    
            except Exception as e:
                print(f"⚠️ Input-Analyse Fehler: {e}")
                continue
        
        # Analysiere Select-Felder
        for select in all_selects:
            try:
                name = (select.get_attribute('name') or '').lower()
                id_attr = (select.get_attribute('id') or '').lower()
                
                combined = f"{name} {id_attr}"
                print(f"🔍 Select: name={name}, id={id_attr}")
                
                if 'country' in combined and select.is_displayed():
                    country_field = select
                    print(f"✅ Country-Feld gefunden: {name}")
                    
            except Exception as e:
                print(f"⚠️ Select-Analyse Fehler: {e}")
                continue
        
        success_count = 0
        
        # 1. FÜLLE COMPANY-FELD
        if company_field:
            try:
                company_field.clear()
                company_field.send_keys("Test Company GmbH")
                print("✅ Company-Feld ausgefüllt: Test Company GmbH")
                success_count += 1
            except Exception as e:
                print(f"❌ Company-Feld Fehler: {e}")
        
        # 2. FÜLLE EMAIL-FELD
        if email_field:
            try:
                email_field.clear()
                email_field.send_keys("test@company.com")
                print("✅ Email-Feld ausgefüllt: test@company.com")
                success_count += 1
            except Exception as e:
                print(f"❌ Email-Feld Fehler: {e}")
        
        # 3. WÄHLE COUNTRY
        if country_field:
            try:
                options = country_field.find_elements(By.TAG_NAME, "option")
                print(f"🌍 {len(options)} Country-Optionen gefunden")
                
                # Suche nach Deutschland/Germany
                germany_found = False
                for option in options:
                    text = (option.text or '').lower()
                    value = (option.get_attribute('value') or '').lower()
                    
                    if any(keyword in f"{text} {value}" for keyword in ['germany', 'deutschland', 'de', 'ger']):
                        option.click()
                        print(f"✅ Country ausgewählt: {option.text}")
                        germany_found = True
                        success_count += 1
                        break
                
                # Fallback: Zweite Option
                if not germany_found and len(options) > 1:
                    options[1].click()
                    print(f"✅ Country Fallback: {options[1].text}")
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Country-Feld Fehler: {e}")
        
        # 4. WÄHLE RADIO-BUTTON für Packaging-Typ
        if radio_buttons:
            print(f"📻 {len(radio_buttons)} Radio-Buttons gefunden")
            
            packaging_radio = None
            for i, radio in enumerate(radio_buttons):
                try:
                    value = (radio.get_attribute('value') or '').lower()
                    name = (radio.get_attribute('name') or '').lower()
                    
                    # Finde Label-Text
                    label_text = ""
                    try:
                        radio_id = radio.get_attribute('id')
                        if radio_id:
                            label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                            label_text = label.text.lower()
                    except:
                        try:
                            parent = radio.find_element(By.XPATH, "..")
                            if parent.tag_name.lower() == 'label':
                                label_text = parent.text.lower()
                        except:
                            pass
                    
                    combined_text = f"{value} {name} {label_text}"
                    print(f"   Radio {i+1}: value={value}, name={name}, label={label_text}")
                    
                    # Suche nach Packaging-Keywords
                    if any(keyword in combined_text for keyword in ['packaging', 'paper', 'waste', 'material']):
                        packaging_radio = radio
                        print(f"✅ Packaging Radio-Button gefunden: {combined_text}")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Radio {i+1} Analyse Fehler: {e}")
                    continue
            
            # Klicke Packaging Radio-Button
            if packaging_radio:
                try:
                    driver.execute_script("arguments[0].click();", packaging_radio)
                    time.sleep(1)
                    if packaging_radio.is_selected():
                        print("✅ Packaging Radio-Button erfolgreich ausgewählt")
                        success_count += 1
                    else:
                        print("⚠️ Radio-Button nicht ausgewählt nach Klick")
                except Exception as e:
                    print(f"❌ Radio-Button Klick Fehler: {e}")
            else:
                # Fallback: Ersten Radio-Button wählen
                if radio_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", radio_buttons[0])
                        time.sleep(1)
                        print("✅ Fallback: Ersten Radio-Button ausgewählt")
                        success_count += 1
                    except Exception as e:
                        print(f"❌ Fallback Radio-Button Fehler: {e}")
        
        # 5. SUCHE UND KLICKE SUBMIT/NEXT BUTTON
        submit_clicked = False
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]', 
            'button:contains("Next")',
            'button:contains("Weiter")',
            'button:contains("Continue")',
            'button:contains("Submit")'
        ]
        
        for selector in submit_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        driver.execute_script("arguments[0].click();", button)
                        print(f"✅ Submit-Button geklickt: {button.text}")
                        submit_clicked = True
                        time.sleep(3)
                        break
                if submit_clicked:
                    break
            except Exception as e:
                print(f"⚠️ Submit {selector} Fehler: {e}")
                continue
        
        if not submit_clicked:
            print("⚠️ Kein Submit-Button gefunden - versuche andere Strategien")
        
        print(f"✅ KOMBINIERTE FORM: {success_count} Felder erfolgreich ausgefüllt")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Combined Form Handler Fehler: {e}")
        return False
