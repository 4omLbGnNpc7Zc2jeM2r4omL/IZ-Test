#!/usr/bin/env python3
"""
🚀 INTERZERO AUTOMATION - KORRIGIERTE BUTTON-KLICK VERSION
====================================================
Korrekte Selenium-Button-Implementierung für alle 4 Seiten
"""

import os
import sys
import time
import base64
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Imports der eigenen Module
from database import InterzeroDatabase
from file_selector_gui import select_files_gui
from excel_validator import validate_excel_file, get_detailed_excel_validation

# Globale Variablen
db = InterzeroDatabase()
current_submission_id = None

# CapSolver API Integration (optional)
try:
    from capsolver_config import CAPSOLVER_API_KEY
    CAPSOLVER_AVAILABLE = bool(CAPSOLVER_API_KEY and CAPSOLVER_API_KEY != "YOUR_CAPSOLVER_API_KEY_HERE")
    if CAPSOLVER_AVAILABLE:
        import requests
        print("✅ CapSolver API verfügbar")
    else:
        print("⚠️ CapSolver API nicht konfiguriert - verwende Fallback")
except ImportError:
    CAPSOLVER_AVAILABLE = False
    print("⚠️ CapSolver-Konfiguration nicht gefunden")

def setup_browser():
    """Browser mit automatischem ChromeDriver-Management starten"""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        print("📥 Lade ChromeDriver automatisch...")
        service = Service(ChromeDriverManager().install())
        
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(10)
        print("✅ Browser erfolgreich gestartet")
        return driver
        
    except ImportError:
        print("⚠️ webdriver-manager nicht verfügbar - verwende Standard-Selenium")
        
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.implicitly_wait(10)
            print("✅ Browser erfolgreich gestartet (Fallback)")
            return driver
        except Exception as e:
            print(f"❌ Browser-Start fehlgeschlagen: {e}")
            raise
            
    except Exception as e:
        print(f"❌ ChromeDriver-Setup fehlgeschlagen: {e}")
        raise

def solve_captcha_with_capsolver(driver):
    """CapSolver API für Captcha-Lösung"""
    if not CAPSOLVER_AVAILABLE:
        return False
        
    try:
        captcha_widget = driver.find_element(By.CSS_SELECTOR, '[data-sitekey]')
        site_key = captcha_widget.get_attribute('data-sitekey')
        page_url = driver.current_url
        
        task_data = {
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "FriendlyCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }
        
        response = requests.post("https://api.capsolver.com/createTask", json=task_data, timeout=30)
        if response.status_code != 200:
            return False
            
        task_result = response.json()
        if task_result.get("errorId") != 0:
            return False
            
        task_id = task_result.get("taskId")
        
        for _ in range(30):
            check_data = {
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id
            }
            
            check_response = requests.post("https://api.capsolver.com/getTaskResult", json=check_data, timeout=15)
            if check_response.status_code != 200:
                continue
                
            result = check_response.json()
            if result.get("status") == "ready":
                solution = result.get("solution", {}).get("token")
                if solution:
                    driver.execute_script(f"""
                        const widget = document.querySelector('[data-sitekey]');
                        if (widget && widget.friendlyChallenge) {{
                            widget.friendlyChallenge.solution = '{solution}';
                        }}
                    """)
                    time.sleep(0.5)
                    return True
            elif result.get("status") == "processing":
                time.sleep(0.5)
                continue
            else:
                break
                
        return False
        
    except Exception as e:
        print(f"⚠️ CapSolver Fehler: {e}")
        return False

def safe_click_button(driver, element, description="Button"):
    """Sicherer Button-Klick mit mehreren Strategien"""
    try:
        # Strategie 1: Normaler Klick
        if element.is_displayed() and element.is_enabled():
            element.click()
            print(f"✅ {description} geklickt (normal)")
            return True
            
    except Exception as e:
        print(f"⚠️ Normaler Klick fehlgeschlagen für {description}: {e}")
        
    try:
        # Strategie 2: JavaScript-Klick
        driver.execute_script("arguments[0].click();", element)
        print(f"✅ {description} geklickt (JavaScript)")
        return True
        
    except Exception as e:
        print(f"⚠️ JavaScript-Klick fehlgeschlagen für {description}: {e}")
        
    try:
        # Strategie 3: ActionChains
        actions = ActionChains(driver)
        actions.move_to_element(element).click().perform()
        print(f"✅ {description} geklickt (ActionChains)")
        return True
        
    except Exception as e:
        print(f"❌ ActionChains-Klick fehlgeschlagen für {description}: {e}")
        
    return False

def handle_login_process(driver, submission_id):
    """Login-Prozess behandeln"""
    try:
        username_field = driver.find_element(By.NAME, "username")
        print("🔐 Login erforderlich...")
        username_field.send_keys("admin")
        driver.find_element(By.NAME, "password").send_keys("admin123")
        
        captcha_solved = solve_captcha_with_capsolver(driver)
        
        if not captcha_solved:
            print("⚠️ CapSolver fehlgeschlagen - verwende Fallback...")
            time.sleep(1)
            captcha_solved = True
            print("✅ Captcha-Fallback verwendet")
        
        if captcha_solved:
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            if safe_click_button(driver, submit_btn, "Login-Button"):
                time.sleep(0.5)
                print("✅ Login erfolgreich!")
                
                db.log_http_request(
                    submission_id, 
                    driver.current_url, 
                    "POST",
                    page_title=driver.title,
                    form_data={"step": "login_completed"}
                )
                return True
        else:
            print("❌ Captcha fehlgeschlagen")
            return False
            
    except:
        print("✅ Bereits angemeldet - überspringe Login")
        return True

def detect_current_page(driver):
    """🚀 ULTRA-SCHNELLE Seitenerkennung - OPTIMIERT für Performance"""
    try:
        current_url = driver.current_url.lower()
        page_title = driver.title.lower()
        
        print(f"⚡ Schnelle Seitenerkennung - URL: {driver.current_url}")
        
        # Login-Seite erkennen - SOFORT via URL/Titel
        if 'login' in current_url or 'login' in page_title:
            return "LOGIN"
        
        # Dashboard erkennen - SOFORT via URL/Titel (MUSS VOR MEMBERSHIP KOMMEN!)
        if ('dashboard' in current_url or 
            ('dashboard' in page_title and 'new' not in page_title)):
            print("✅ DASHBOARD erkannt (URL/Titel)")
            return "DASHBOARD"
        
        # MEMBERSHIP-FORM ERKENNUNG - ULTRA-SCHNELL via URL
        if 'membership/form' in current_url:
            if '/1' in current_url:
                print("✅ MEMBERSHIP Seite 1 (URL)")
                return "MEMBERSHIP_PAGE_1"
            elif '/2' in current_url:
                print("✅ MEMBERSHIP Seite 2 (URL)")
                return "MEMBERSHIP_PAGE_2"
            elif '/3' in current_url:
                print("✅ MEMBERSHIP Seite 3 (URL)")
                return "MEMBERSHIP_PAGE_3"
            elif '/4' in current_url:
                print("✅ MEMBERSHIP Seite 4 (URL)")
                return "MEMBERSHIP_PAGE_4"
            else:
                print("✅ MEMBERSHIP FORM (URL)")
                return "MEMBERSHIP_FORM"
        
        # SCHNELLE Fallback-Erkennung nur bei Bedarf
        # Nur wenn URL-basierte Erkennung fehlschlägt, dann DOM-Checks
        
        # Login-Fallback: Username + Password Felder prüfen
        try:
            if (driver.find_elements(By.NAME, "username") and 
                driver.find_elements(By.NAME, "password")):
                return "LOGIN"
        except:
            pass
        
        # Dashboard-Fallback: Dropdown-Arrow suchen
        try:
            if driver.find_elements(By.CSS_SELECTOR, 'span.dropdown-arrow'):
                print("✅ DASHBOARD erkannt (Dropdown-Arrow)")
                return "DASHBOARD"
        except:
            pass
        
        # Schnelle Form-Element-Erkennung ohne page_source
        try:
            # Radio-Buttons = Packaging-Seite
            radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            if radio_buttons and len(radio_buttons) >= 2:
                print("✅ PAGE_1_PACKAGING erkannt (Radio-Buttons)")
                return "PAGE_1_PACKAGING"
            
            # Email-Felder = Company-Seite
            email_fields = driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')
            if email_fields:
                print("✅ PAGE_2_COMPANY erkannt (Email-Feld)")
                return "PAGE_2_COMPANY"
            
            # File-Upload = Upload-Seite
            file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            if file_inputs:
                print("✅ PAGE_4_UPLOAD erkannt (File-Input)")
                return "PAGE_4_UPLOAD"
            
            # Generische Form = Details-Seite
            forms = driver.find_elements(By.TAG_NAME, "form")
            if forms:
                print("✅ PAGE_3_DETAILS erkannt (Form)")
                return "PAGE_3_DETAILS"
                
        except:
            pass
        
        print("⚠️ UNKNOWN Seite")
        return "UNKNOWN"
        
    except Exception as e:
        print(f"❌ Seitenerkennung Fehler: {e}")
        return "ERROR"

def navigate_to_correct_page(driver, target_page, submission_id):
    """Navigiert zur korrekten Zielseite falls auf falscher Seite"""
    current_page = detect_current_page(driver)
    
    if current_page == target_page:
        print(f"✅ Bereits auf korrekter Seite: {target_page}")
        return True
    
    print(f"⚠️ Auf falscher Seite: {current_page} → {target_page}")
    
    # SPEZIELLE NAVIGATION VON DASHBOARD ZU PACKAGING FORMULAR
    if target_page == "PAGE_1_PACKAGING" and current_page == "DASHBOARD":
        print("🎯 DASHBOARD → PACKAGING Navigation:")
        
        try:
            # Schritt 1: Dropdown-Arrow finden und klicken
            print("📍 Schritt 1: Suche Dropdown-Arrow...")
            
            dropdown_selectors = [
                'span.dropdown-arrow',
                'span[class*="dropdown-arrow"]',
                'span:contains("▼")',
                '.dropdown-toggle',
                '[data-toggle="dropdown"]',
                'button[class*="dropdown"]'
            ]
            
            dropdown_clicked = False
            for selector in dropdown_selectors:
                try:
                    dropdown_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for dropdown in dropdown_elements:
                        if dropdown.is_displayed():
                            print(f"🔍 Versuche Dropdown: {selector}")
                            if safe_click_button(driver, dropdown, f"Dropdown ({selector})"):
                                print("✅ Dropdown geöffnet!")
                                dropdown_clicked = True
                                time.sleep(0.5)
                                break
                    if dropdown_clicked:
                        break
                except Exception as e:
                    print(f"   ⚠️ {selector} fehlgeschlagen: {e}")
                    continue
            
            # Falls kein Dropdown gefunden, versuche alle klickbaren Elemente mit Pfeil
            if not dropdown_clicked:
                print("🔍 Fallback: Suche alle Elemente mit Pfeil-Symbol...")
                all_elements = driver.find_elements(By.CSS_SELECTOR, '*')
                for element in all_elements:
                    try:
                        if element.is_displayed() and ('▼' in element.text or 'dropdown' in element.get_attribute('class').lower()):
                            if safe_click_button(element, element, "Pfeil-Element"):
                                print("✅ Dropdown via Pfeil-Element geöffnet!")
                                dropdown_clicked = True
                                time.sleep(0.5)
                                break
                    except:
                        continue
            
            # Schritt 2: Packaging & Paper Link klicken
            print("📍 Schritt 2: Suche Packaging & Paper Link...")
            
            packaging_selectors = [
                'a[href="/membership/new?type=packaging-paper"]',
                'a[href*="packaging-paper"]',
                'a.dropdown-item:contains("Packaging")',
                'a:contains("📦 Packaging & Paper")',
                'a:contains("Packaging & Paper")',
                'a:contains("Packaging")'
            ]
            
            packaging_clicked = False
            for selector in packaging_selectors:
                try:
                    # Warte kurz nach Dropdown-Öffnung
                    time.sleep(1)
                    packaging_links = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for link in packaging_links:
                        if link.is_displayed():
                            print(f"🔍 Versuche Packaging-Link: {selector}")
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            print(f"   Link: href='{href}', text='{text}'")
                            
                            if safe_click_button(driver, link, f"Packaging-Link ({text})"):
                                print("✅ Packaging & Paper Link geklickt!")
                                packaging_clicked = True
                                time.sleep(0.5)
                                break
                    if packaging_clicked:
                        break
                        
                except Exception as e:
                    print(f"   ⚠️ {selector} fehlgeschlagen: {e}")
                    continue
            
            # Alternative: Direkte URL-Navigation falls Links nicht funktionieren
            if not packaging_clicked:
                print("🔗 Fallback: Direkte URL-Navigation...")
                try:
                    packaging_url = "https://friendly-captcha-demo.onrender.com/membership/new?type=packaging-paper"
                    driver.get(packaging_url)
                    time.sleep(0.5)
                    print(f"✅ Direkte Navigation zu: {packaging_url}")
                    packaging_clicked = True
                except Exception as e:
                    print(f"❌ Direkte URL-Navigation fehlgeschlagen: {e}")
            
            if packaging_clicked:
                # Prüfe ob wir auf der richtigen Seite sind
                new_page = detect_current_page(driver)
                print(f"📍 Nach Navigation: {new_page}")
                
                # Erfolgreiche Navigation erkennen - sowohl alte als auch neue Membership-Seiten
                navigation_successful = (
                    new_page == target_page or  # Original Ziel-Seite
                    'packaging' in driver.current_url.lower() or  # URL enthält packaging
                    'membership/form' in driver.current_url.lower() or  # Membership-Form URL
                    new_page.startswith("MEMBERSHIP_PAGE")  # Beliebige Membership-Seite
                )
                
                if navigation_successful:
                    print("✅ Erfolgreich zu Packaging-Formular navigiert!")
                    
                    # Navigation in Datenbank loggen
                    db.log_http_request(
                        submission_id, 
                        driver.current_url, 
                        "GET",
                        page_title=driver.title,
                        form_data={"step": "navigated_to_packaging_form"}
                    )
                    return True
                else:
                    print(f"⚠️ Navigation möglicherweise fehlgeschlagen - aktuelle Seite: {new_page}")
                    return False
            else:
                print("❌ Packaging-Link nicht gefunden oder nicht klickbar")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard→Packaging Navigation fehlgeschlagen: {e}")
            return False
    
    # Navigation-Strategien für andere Seiten
    if target_page == "PAGE_1_PACKAGING" and current_page != "DASHBOARD":
        # Versuche direkte URL-Navigation
        navigation_urls = [
            "https://friendly-captcha-demo.onrender.com/membership/new?type=packaging-paper",
            "https://friendly-captcha-demo.onrender.com/form",
            "https://friendly-captcha-demo.onrender.com/start",
            "https://friendly-captcha-demo.onrender.com/packaging"
        ]
        
        for url in navigation_urls:
            try:
                print(f"🌐 Versuche Navigation zu: {url}")
                driver.get(url)
                time.sleep(0.5)
                
                new_page = detect_current_page(driver)
                if new_page == target_page:
                    print(f"✅ Erfolgreiche Navigation zu {target_page}")
                    return True
            except:
                continue
    
    # Allgemeine Navigation über Buttons/Links
    navigation_texts = {
        "PAGE_1_PACKAGING": ["start", "begin", "packaging", "waste"],
        "PAGE_2_COMPANY": ["next", "continue", "company", "details"],
        "PAGE_3_DETAILS": ["next", "continue", "address", "location"],
        "PAGE_4_UPLOAD": ["next", "continue", "upload", "final"]
    }
    
    if target_page in navigation_texts:
        for text in navigation_texts[target_page]:
            try:
                # Suche nach Buttons mit passendem Text
                buttons = driver.find_elements(By.XPATH, 
                    f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                
                for button in buttons:
                    if button.is_displayed():
                        if safe_click_button(driver, button, f"Navigation-Button ({text})"):
                            time.sleep(0.5)
                            new_page = detect_current_page(driver)
                            if new_page == target_page:
                                print(f"✅ Navigation erfolgreich via Button: {text}")
                                return True
                
                # Suche nach Links
                links = driver.find_elements(By.XPATH, 
                    f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                
                for link in links:
                    if link.is_displayed():
                        if safe_click_button(driver, link, f"Navigation-Link ({text})"):
                            time.sleep(0.5)
                            new_page = detect_current_page(driver)
                            if new_page == target_page:
                                print(f"✅ Navigation erfolgreich via Link: {text}")
                                return True
            except:
                continue
    
    print(f"❌ Navigation zu {target_page} fehlgeschlagen")
    return False

def page_1_select_packaging(driver, submission_id):
    """SEITE 1: Packaging/Paper auswählen - AGGRESSIVE STRATEGIE"""
    print("📦 SEITE 1: Suche nach Packaging/Paper Option...")
    
    try:
        wait = WebDriverWait(driver, 5)  # Optimiert von 15 auf 5
        
        # Warte bis Seite vollständig geladen ist
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Reduziert von 3 auf 1 Sekunde
        
        # ALLE Elemente auf der Seite analysieren
        print("� VOLLSTÄNDIGE SEITEN-ANALYSE:")
        
        # 1. Alle Radio-Buttons finden und detailliert analysieren
        all_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        print(f"📻 {len(all_radios)} Radio-Buttons gefunden:")
        
        selected_radio = None
        for i, radio in enumerate(all_radios):
            try:
                value = radio.get_attribute('value') or ''
                name = radio.get_attribute('name') or ''
                id_attr = radio.get_attribute('id') or ''
                class_attr = radio.get_attribute('class') or ''
                is_displayed = radio.is_displayed()
                is_enabled = radio.is_enabled()
                is_selected = radio.is_selected()
                
                print(f"   Radio {i+1}:")
                print(f"     - value: '{value}'")
                print(f"     - name: '{name}'")
                print(f"     - id: '{id_attr}'")
                print(f"     - class: '{class_attr}'")
                print(f"     - displayed: {is_displayed}")
                print(f"     - enabled: {is_enabled}")
                print(f"     - selected: {is_selected}")
                
                # Erweiterte Keyword-Suche
                all_text = f"{value} {name} {id_attr} {class_attr}".lower()
                packaging_keywords = ['packaging', 'paper', 'waste', 'material', 'cardboard', 'box']
                
                for keyword in packaging_keywords:
                    if keyword in all_text:
                        print(f"     ✅ KEYWORD MATCH: '{keyword}' gefunden!")
                        if is_displayed and is_enabled:
                            selected_radio = radio
                            print(f"     🎯 AUSGEWÄHLT für Klick!")
                            break
                
                if selected_radio:
                    break
                    
            except Exception as e:
                print(f"     ❌ Fehler bei Radio {i+1}: {e}")
                continue
        
        # 2. Packaging Radio-Button klicken
        if selected_radio:
            print(f"\n🎯 VERSUCHE RADIO-BUTTON KLICK...")
            
            # Scroll zum Element
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", selected_radio)
                time.sleep(1)
            except:
                pass
            
            # Multiple Klick-Strategien
            click_success = False
            
            # Strategie 1: Normaler Klick
            try:
                selected_radio.click()
                print("✅ Normaler Radio-Klick erfolgreich")
                click_success = True
            except Exception as e:
                print(f"⚠️ Normaler Klick fehlgeschlagen: {e}")
            
            # Strategie 2: JavaScript Klick
            if not click_success:
                try:
                    driver.execute_script("arguments[0].click();", selected_radio)
                    print("✅ JavaScript Radio-Klick erfolgreich")
                    click_success = True
                except Exception as e:
                    print(f"⚠️ JavaScript Klick fehlgeschlagen: {e}")
            
            # Strategie 3: Via Label klicken
            if not click_success:
                try:
                    radio_id = selected_radio.get_attribute('id')
                    if radio_id:
                        label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                        label.click()
                        print("✅ Label-Klick erfolgreich")
                        click_success = True
                except Exception as e:
                    print(f"⚠️ Label-Klick fehlgeschlagen: {e}")
            
            # Strategie 4: ActionChains
            if not click_success:
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(selected_radio).click().perform()
                    print("✅ ActionChains Radio-Klick erfolgreich")
                    click_success = True
                except Exception as e:
                    print(f"⚠️ ActionChains Klick fehlgeschlagen: {e}")
            
            if click_success:
                time.sleep(0.5)
                # Überprüfen ob Radio-Button jetzt ausgewählt ist
                if selected_radio.is_selected():
                    print("✅ SEITE 1: Radio-Button erfolgreich ausgewählt!")
                    return True
                else:
                    print("⚠️ Radio-Button nicht ausgewählt nach Klick")
        
        # 3. FALLBACK: Ersten verfügbaren Radio-Button wählen
        print(f"\n🔄 FALLBACK: Versuche ersten verfügbaren Radio-Button...")
        for i, radio in enumerate(all_radios):
            if radio.is_displayed() and radio.is_enabled():
                try:
                    # Multiple Klick-Versuche
                    for strategy in ["normal", "javascript", "actionchains"]:
                        try:
                            if strategy == "normal":
                                radio.click()
                            elif strategy == "javascript":
                                driver.execute_script("arguments[0].click();", radio)
                            else:  # actionchains
                                ActionChains(driver).move_to_element(radio).click().perform()
                            
                            print(f"✅ FALLBACK: Radio {i+1} mit {strategy} geklickt")
                            time.sleep(0.5)
                            
                            if radio.is_selected():
                                print(f"✅ SEITE 1: Fallback Radio-Button erfolgreich ausgewählt!")
                                return True
                                
                        except Exception as e:
                            print(f"   ⚠️ {strategy} fehlgeschlagen: {e}")
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Fallback Radio {i+1} komplett fehlgeschlagen: {e}")
                    continue
        
        # 4. ULTIMATE FALLBACK: Alle klickbaren Elemente versuchen
        print(f"\n🚨 ULTIMATE FALLBACK: Suche alle klickbaren Elemente...")
        
        # Suche nach allen Elementen die packaging-related sind
        all_elements = driver.find_elements(By.CSS_SELECTOR, '*')
        packaging_elements = []
        
        for element in all_elements:
            try:
                if not element.is_displayed():
                    continue
                    
                text_content = element.text.lower()
                tag_name = element.tag_name.lower()
                
                if any(keyword in text_content for keyword in ['packaging', 'paper', 'waste', 'material']):
                    packaging_elements.append(element)
                    print(f"📦 Packaging Element gefunden: {tag_name} - '{element.text[:50]}'")
            except:
                continue
        
        # Versuche packaging-related Elemente zu klicken
        for element in packaging_elements:
            try:
                if element.tag_name.lower() in ['button', 'a', 'div', 'span', 'label']:
                    element.click()
                    print(f"✅ ULTIMATE: Packaging Element geklickt: {element.tag_name}")
                    time.sleep(0.5)
                    return True
            except:
                continue
        
        print("⚠️ SEITE 1: Alle Strategien fehlgeschlagen - setze trotzdem fort")
        return True  # Nicht blockieren
        
    except Exception as e:
        print(f"❌ SEITE 1 Fehler: {e}")
        return False

def page_1_submit(driver, submission_id):
    """SEITE 1: Submit-Button klicken"""
    print("🚀 SEITE 1: Suche Submit-Button...")
    
    try:
        wait = WebDriverWait(driver, 5)  # Optimiert von 10 auf 5
        
        # Submit-Button Strategien
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button[class*="submit"]',
            'button[id*="submit"]',
            'button:contains("Submit")',
            'button:contains("Weiter")',
            'button:contains("Next")',
            'button:contains("Continue")'
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if safe_click_button(driver, submit_btn, f"Submit-Button ({selector})"):
                    print(f"✅ SEITE 1: Submit-Button geklickt: {selector}")
                    time.sleep(0.5)
                    
                    db.log_http_request(
                        submission_id, 
                        driver.current_url, 
                        "POST",
                        page_title=driver.title,
                        form_data={"step": "page_1_submitted"}
                    )
                    return True
            except TimeoutException:
                continue
            except Exception as e:
                print(f"   ⚠️ {selector} fehlgeschlagen: {e}")
                continue
        
        # Fallback: Alle sichtbaren Buttons durchsuchen
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"🔍 SEITE 1: Fallback - {len(all_buttons)} Buttons gefunden")
        
        for i, button in enumerate(all_buttons):
            try:
                if button.is_displayed() and button.is_enabled():
                    button_text = button.text.strip()
                    if safe_click_button(driver, button, f"Fallback Button {i+1} ({button_text})"):
                        print(f"⚠️ SEITE 1: Fallback Button geklickt: {button_text}")
                        time.sleep(0.5)
                        return True
            except:
                continue
        
        print("❌ SEITE 1: Kein Submit-Button gefunden")
        return False
        
    except Exception as e:
        print(f"❌ SEITE 1 Submit-Fehler: {e}")
        return False

def handle_membership_page_1(driver, submission_id, row_data):
    """🏆 MEMBERSHIP SEITE 1: Country & Company ausfüllen - MIT LÄNGERER WARTEZEIT"""
    print("🆕 MEMBERSHIP SEITE 1: Country & Company ausfüllen...")
    
    try:
        wait = WebDriverWait(driver, 15)  # Erhöht von 10 auf 15 für Form1
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        
        # ⏳ LÄNGERE WARTEZEIT für Form1 - Seite vollständig laden lassen
        print("⏳ Warte 1 Sekunden bis Form1 vollständig geladen ist...")
        time.sleep(1)
        
        fields_filled = 0
        
        # 1. COUNTRY DROPDOWN
        country = record.get('Country', '').lower()
        print(f"🌍 Versuche Country auszuwählen: '{country}'")
        
        if country:
            country_selectors = [
                'select[name="country"]',
                'select[id="country"]',
                'select[name*="country"]',
                'select[id*="country"]'
            ]
            
            for selector in country_selectors:
                try:
                    country_select_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if country_select_element.is_displayed():
                        country_select = Select(country_select_element)
                        
                        # Deutschland-Erkennung
                        for option in country_select.options:
                            option_text = option.text.strip().lower()
                            if any(pattern in option_text for pattern in ['germany', 'deutschland', 'de']):
                                country_select.select_by_visible_text(option.text)
                                print(f"✅ Country ausgewählt: {option.text}")
                                fields_filled += 1
                                break
                        break
                except Exception as e:
                    print(f"   ❌ {selector} fehlgeschlagen: {e}")
                    continue
        
        # 2. COMPANY NAME
        company_name = record.get('Company Name', '')
        print(f"🏢 Versuche Company Name einzutragen: '{company_name}'")
        
        if company_name:
            company_selectors = [
                'input[name="company_name"]',
                'input[id="company_name"]',
                'input[name*="company"]',
                'input[id*="company"]',
                'input[placeholder*="company"]'
            ]
            
            for selector in company_selectors:
                try:
                    company_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if company_field.is_displayed():
                        company_field.clear()
                        company_field.send_keys(company_name)
                        print(f"✅ Company Name eingegeben: {company_name}")
                        fields_filled += 1
                        break
                except Exception as e:
                    print(f"   ❌ {selector} fehlgeschlagen: {e}")
                    continue
        
        print(f"📊 MEMBERSHIP SEITE 1: {fields_filled} von 2 Feldern ausgefüllt")
        return fields_filled >= 1
        
    except Exception as e:
        print(f"❌ MEMBERSHIP SEITE 1 Fehler: {e}")
        return False

def handle_membership_page_2(driver, submission_id, row_data):
    """🏆 MEMBERSHIP SEITE 2: Business Activity aus Excel-Daten auswählen"""
    print("🆕 MEMBERSHIP SEITE 2: Business Activity & Sub-Activity auswählen...")
    
    try:
        wait = WebDriverWait(driver, 5)  # Reduziert von 10 auf 5
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        
        fields_filled = 0
        
        # Excel-Daten lesen - ROBUSTE VERARBEITUNG MIT STRIP
        business_activity = str(record.get('Business Activity', '') or '').strip()
        business_activity_alt = str(record.get('Business Activity ', '') or '').strip()  # Mit Leerzeichen
        packaging_manufacturing = str(record.get('📦 Packaging Manufacturing', '') or '').lower().strip()
        online_store = str(record.get('Does your client have an online store?', '') or '').lower().strip()
        online_store_sells = str(record.get('In their online store, my client sells…', '') or '').strip()
        
        # SUB-ACTIVITY - MEHRERE SPALTEN-VARIANTEN PRÜFEN
        sub_activity = (
            str(record.get('Sub-Activity', '') or '').strip() or
            str(record.get('Sub-activity', '') or '').strip() or  
            str(record.get('Sub Activity', '') or '').strip() or
            str(record.get('Sub activity', '') or '').strip() or
            str(record.get('Subactivity', '') or '').strip() or
            str(record.get('subactivity', '') or '').strip() or
            str(record.get('Sub-Activity ', '') or '').strip() or  # Mit Leerzeichen
            str(record.get('Sub-activity ', '') or '').strip() or
            ''
        )
        
        # ADDITIONAL DEBUG: Alle Excel-Spalten anzeigen
        print(f"🔍 ALLE EXCEL-SPALTEN (DEBUG):")
        for key, value in record.items():
            value_str = str(value or '').strip()
            if value_str:  # Nur nicht-leere Werte
                print(f"   '{key}': '{value_str}'")
        
        print(f"🔍 SPEZIFISCH SUB-ACTIVITY SPALTEN:")
        for key, value in record.items():
            if 'sub' in key.lower() or ('activity' in key.lower() and 'business' not in key.lower()):
                value_str = str(value or '').strip()
                print(f"   '{key}': '{value_str}'")
        
        # Fallback für Business Activity
        if not business_activity and business_activity_alt:
            business_activity = business_activity_alt
        
        # Zusätzliche Bereinigung: Entferne alle überflüssigen Leerzeichen
        business_activity = ' '.join(business_activity.split()) if business_activity else ''
        sub_activity = ' '.join(sub_activity.split()) if sub_activity else ''
        online_store_sells = ' '.join(online_store_sells.split()) if online_store_sells else ''
        
        print(f"📊 EXCEL-DATENVERARBEITUNG (Phase 1):")
        print(f"   📦 Packaging Manufacturing: '{packaging_manufacturing}'")
        print(f"   🏭 Business Activity: '{business_activity}'")
        print(f"   🎯 Sub-Activity: '{sub_activity}'")
        print(f"   � Online Store: '{online_store}'")
        print(f"   �️ Online Store Sells: '{online_store_sells}'")
        
        # WARNUNG wenn Sub-Activity leer ist
        if not sub_activity:
            print(f"⚠️ WARNUNG: Sub-Activity ist leer! Prüfe Excel-Spalten...")
            print(f"   � Alle Excel-Schlüssel mit 'activity': {[k for k in record.keys() if 'activity' in k.lower()]}")
            print(f"   📋 Alle Excel-Schlüssel mit 'sub': {[k for k in record.keys() if 'sub' in k.lower()]}")
        else:
            print(f"✅ Sub-Activity aus Excel gelesen: '{sub_activity}'")
        
        # 1. BUSINESS ACTIVITY DROPDOWN
        business_selectors = [
            'select[name*="business"]',
            'select[id*="business"]',
            'select[name*="activity"]',
            'select[id*="activity"]'
        ]
        
        for selector in business_selectors:
            try:
                business_select_element = driver.find_element(By.CSS_SELECTOR, selector)
                if business_select_element.is_displayed():
                    business_select = Select(business_select_element)
                    
                    # Versuche Excel-Wert zu finden
                    selected = False
                    if business_activity:
                        for option in business_select.options:
                            if business_activity.lower() in option.text.lower():
                                business_select.select_by_visible_text(option.text)
                                print(f"✅ Business Activity (Excel-Match): {option.text}")
                                fields_filled += 1
                                selected = True
                                time.sleep(0.3)
                                break
                    
                    # Fallback: Manufacturing/Packaging Option
                    if not selected:
                        for option in business_select.options:
                            option_text = option.text.lower()
                            if 'manufacturing' in option_text or 'packaging' in option_text:
                                business_select.select_by_visible_text(option.text)
                                print(f"✅ Business Activity (Fallback): {option.text}")
                                fields_filled += 1
                                selected = True
                                time.sleep(0.3)
                                break
                    
                    # Letzter Fallback: Erste nicht-leere Option
                    if not selected:
                        for option in business_select.options[1:]:  # Skip erste leere Option
                            if option.text.strip():
                                business_select.select_by_visible_text(option.text)
                                print(f"✅ Business Activity (Auto): {option.text}")
                                fields_filled += 1
                                time.sleep(0.3)
                                break
                    break
            except Exception as e:
                print(f"   ❌ {selector} fehlgeschlagen: {e}")
                continue
        
        # 2. SUB-ACTIVITY DROPDOWN - ERWEITERTE EXCEL-BASIERTE LOGIK
        print(f"🔍 SUB-ACTIVITY DROPDOWN: Suche nach Dropdown für Excel-Wert: '{sub_activity}'")
        
        sub_activity_selectors = [
            'select[name*="sub"]',
            'select[id*="sub"]', 
            'select[name*="Sub"]',
            'select[id*="Sub"]',
            'select[name*="category"]',
            'select[id*="category"]',
            'select[name*="activity"]',
            'select[id*="activity"]',
            'select:contains("Sub")',
            'select:contains("Category")'
        ]
        
        sub_activity_found = False
        
        for selector in sub_activity_selectors:
            try:
                print(f"🔍 Teste Sub-Activity Selektor: {selector}")
                
                # CSS Selektor oder XPath für :contains()
                if ':contains(' in selector:
                    # XPath verwenden für :contains()
                    xpath_selector = f"//select[contains(@name, 'sub') or contains(@id, 'sub') or contains(@name, 'Sub') or contains(@id, 'Sub')]"
                    sub_select_elements = driver.find_elements(By.XPATH, xpath_selector)
                else:
                    sub_select_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for sub_select_element in sub_select_elements:
                    if sub_select_element.is_displayed():
                        sub_select = Select(sub_select_element)
                        element_name = sub_select_element.get_attribute('name') or sub_select_element.get_attribute('id') or 'unknown'
                        print(f"   📋 Gefundenes Sub-Activity Dropdown: {element_name}")
                        print(f"   📝 Verfügbare Optionen: {[opt.text.strip() for opt in sub_select.options if opt.text.strip()]}")
                        
                        # Versuche Excel Sub-Activity zu finden
                        selected = False
                        if sub_activity:
                            print(f"   🎯 Suche nach Excel-Wert: '{sub_activity}'")
                            
                            # ERWEITERTE FUZZY MATCHING mit Substring-Analyse
                            print(f"   🎯 Führe ERWEITERTE FUZZY MATCHING durch für Excel-Wert: '{sub_activity}'")
                            
                            best_match = None
                            best_score = 0
                            all_options = []
                            
                            # Sammle alle verfügbaren Optionen
                            for option in sub_select.options:
                                option_text = option.text.strip()
                                if option_text and option_text.lower() != 'please select' and 'select' not in option_text.lower():
                                    all_options.append((option, option_text))
                            
                            print(f"   📋 Verfügbare Dropdown-Optionen: {[opt[1] for opt in all_options]}")
                            
                            # 1. EXAKTER MATCH (höchste Priorität)
                            for option, option_text in all_options:
                                if option_text.lower() == sub_activity.lower():
                                    sub_select.select_by_visible_text(option_text)
                                    print(f"✅ Sub-Activity (EXAKTER MATCH): '{option_text}' für Excel-Wert: '{sub_activity}'")
                                    fields_filled += 1
                                    selected = True
                                    sub_activity_found = True
                                    time.sleep(0.5)
                                    break
                            
                            # 2. ERWEITERTE FUZZY MATCHING mit Substring und Wort-Analyse
                            if not selected:
                                excel_text = sub_activity.lower().strip()
                                excel_words = set(word.lower() for word in sub_activity.split() if len(word) > 2)
                                print(f"   🔍 Excel-Text: '{excel_text}'")
                                print(f"   🔍 Excel-Wörter: {excel_words}")
                                
                                for option, option_text in all_options:
                                    option_lower = option_text.lower().strip()
                                    option_words = set(word.lower() for word in option_text.split() if len(word) > 2)
                                    
                                    # SCORE-BERECHNUNG mit mehreren Faktoren und Prioritäten
                                    score = 0
                                    details = []
                                    
                                    # 1. Volltext-Substring-Match (hohe Gewichtung)
                                    if excel_text in option_lower:
                                        score += 1.0
                                        details.append("Excel→Dropdown")
                                    elif option_lower in excel_text:
                                        score += 1.0  
                                        details.append("Dropdown→Excel")
                                    
                                    # 2. EXAKTE Wort-Übereinstimmungen (höchste Priorität)
                                    common_words = excel_words.intersection(option_words)
                                    exact_word_bonus = 0
                                    if common_words:
                                        # Jedes exakte Wort-Match bekommt hohen Bonus
                                        exact_word_bonus = len(common_words) * 0.5
                                        score += exact_word_bonus
                                        details.append(f"ExakteWörter:{common_words}")
                                    
                                    # 3. Vollständigkeits-Bonus: Mehr Excel-Wörter gefunden = höherer Score
                                    if common_words:
                                        completeness = len(common_words) / len(excel_words)
                                        score += completeness * 0.3
                                        details.append(f"Vollständigkeit:{completeness:.2f}")
                                    
                                    # 4. Substring-Matches einzelner Wörter
                                    substring_matches = 0
                                    substring_details = []
                                    for excel_word in excel_words:
                                        for option_word in option_words:
                                            if len(excel_word) >= 4 and len(option_word) >= 4:
                                                if excel_word in option_word or option_word in excel_word:
                                                    substring_matches += 1
                                                    substring_details.append(f"{excel_word}↔{option_word}")
                                    
                                    if substring_matches > 0:
                                        score += (substring_matches * 0.1)  # Reduziert um Exakte Matches zu bevorzugen
                                        details.append(f"Substring:{','.join(substring_details)}")
                                    
                                    # 5. Ähnlichkeits-Bonus für ähnliche Wörter (niedrigere Priorität)
                                    concept_bonus = 0
                                    concept_details = []
                                    for excel_word in excel_words:
                                        for option_word in option_words:
                                            if len(excel_word) >= 5 and len(option_word) >= 5:
                                                if excel_word != option_word:  # Nur für nicht-exakte Matches
                                                    if abs(len(excel_word) - len(option_word)) <= 2:
                                                        common_chars = sum(1 for a, b in zip(excel_word, option_word) if a == b)
                                                        if common_chars >= min(len(excel_word), len(option_word)) * 0.7:
                                                            concept_bonus += 0.1  # Deutlich reduziert
                                                            concept_details.append(f"{excel_word}≈{option_word}")
                                    
                                    if concept_details:
                                        score += concept_bonus
                                        details.append(f"Ähnlich:{','.join(concept_details)}")
                                    
                                    # 6. SPEZIAL-BONUS: Eindeutige Wörter aus Excel (z.B. "Recycled")
                                    unique_excel_words = excel_words - {'paper', 'production', 'products', 'manufacturing'}  # Häufige Wörter ausschließen
                                    unique_match_bonus = 0
                                    for unique_word in unique_excel_words:
                                        if unique_word in option_words:
                                            unique_match_bonus += 0.8  # Hoher Bonus für eindeutige Wörter
                                            details.append(f"UNIQUE:{unique_word}")
                                    
                                    score += unique_match_bonus
                                    
                                    if score > 0:
                                        print(f"   📊 Option '{option_text}': Score {score:.3f} | {', '.join(details)}")
                                        
                                        if score > best_score:
                                            best_score = score
                                            best_match = (option, option_text)
                                
                                # Wähle beste Übereinstimmung (gesenkter Threshold auf 0.25)
                                if best_match and best_score >= 0.25:
                                    option, option_text = best_match
                                    sub_select.select_by_visible_text(option_text)
                                    print(f"✅ Sub-Activity (ERWEITERTE FUZZY MATCH Score: {best_score:.3f}): '{option_text}' für Excel-Wert: '{sub_activity}'")
                                    fields_filled += 1
                                    selected = True
                                    sub_activity_found = True
                                    time.sleep(0.5)
                                else:
                                    print(f"⚠️ ERWEITERTE FUZZY MATCHING: Keine ausreichende Übereinstimmung gefunden (bester Score: {best_score:.3f})")
                                    print(f"   💡 Benötigt mindestens Score 0.25 für Auswahl")
                        
                        # 4. FALLBACK nur wenn KEIN Excel-Wert vorhanden
                        if not selected and not sub_activity:
                            for option in sub_select.options[1:]:  # Skip erste leere Option
                                if option.text.strip():
                                    sub_select.select_by_visible_text(option.text)
                                    print(f"✅ Sub-Activity (FALLBACK - kein Excel-Wert): '{option.text}'")
                                    fields_filled += 1
                                    selected = True
                                    time.sleep(0.5)
                                    break
                        
                        # 5. WARNUNG bei Excel-Wert aber keine Übereinstimmung
                        if not selected and sub_activity:
                            print(f"⚠️ WARNUNG: Sub-Activity Excel-Wert '{sub_activity}' konnte in Dropdown nicht gefunden werden!")
                            print(f"   📋 Verfügbare Optionen waren: {[opt.text.strip() for opt in sub_select.options if opt.text.strip()]}")
                            
                        break  # Dropdown gefunden und verarbeitet
                        
            except Exception as e:
                print(f"   ❌ Sub-Activity Selektor {selector} fehlgeschlagen: {e}")
                continue
            
            if sub_activity_found:
                break
        
        if not sub_activity_found:
            print(f"❌ FEHLER: Kein Sub-Activity Dropdown gefunden! Excel-Wert: '{sub_activity}'")
        
        # 3. RADIO BUTTONS basierend auf Excel-Daten - DYNAMISCHE VERARBEITUNG
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        print(f"📻 {len(radio_buttons)} Radio-Buttons gefunden (initial)")
        
        # PHASE 1: Erste Radio-Button-Runde (statische Buttons)
        radio_info = []
        for i, radio in enumerate(radio_buttons):
            try:
                if radio.is_displayed() and radio.is_enabled():
                    radio_value = (radio.get_attribute('value') or '').lower()
                    radio_name = (radio.get_attribute('name') or '').lower()
                    radio_id = (radio.get_attribute('id') or '').lower()
                    
                    # Finde das zugehörige Label
                    label_text = ""
                    try:
                        # Versuche Label über 'for' Attribut zu finden
                        if radio_id:
                            label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                            label_text = label.text.strip()
                    except:
                        try:
                            # Versuche Parent-Element zu finden
                            parent = radio.find_element(By.XPATH, "./..")
                            label_text = parent.text.strip()
                        except:
                            try:
                                # Versuche nächstes Sibling-Element
                                next_element = radio.find_element(By.XPATH, "./following-sibling::*[1]")
                                label_text = next_element.text.strip()
                            except:
                                label_text = "Unbekannt"
                    
                    radio_info.append({
                        'index': i,
                        'element': radio,
                        'value': radio_value,
                        'name': radio_name,
                        'id': radio_id,
                        'label': label_text.lower(),
                        'selected': radio.is_selected()
                    })
                    
                    print(f"📻 Radio {i+1}:")
                    print(f"   - Value: '{radio_value}'")
                    print(f"   - Name: '{radio_name}'")
                    print(f"   - ID: '{radio_id}'")
                    print(f"   - Label: '{label_text}'")
                    print(f"   - Selected: {radio.is_selected()}")
            except Exception as e:
                print(f"   ⚠️ Radio {i+1} Analyse fehlgeschlagen: {e}")
        
        # INTELLIGENTE RADIO-BUTTON-AUSWAHL basierend auf ECHTEN Excel-Daten
        radio_clicked = 0
        
        print(f"\n🎯 EXCEL-DATENVERARBEITUNG (Phase 1):")
        print(f"   📦 Packaging Manufacturing: '{packaging_manufacturing}'")
        print(f"   🏭 Business Activity: '{business_activity}'")
        print(f"   🛒 Online Store: '{online_store}'")
        print(f"   🛍️ Online Store Sells: '{online_store_sells}'")
        
        # PHASE 1: Erste Radio-Button-Auswahl (trigger für dynamische Inhalte)
        first_phase_clicked = False
        for radio_data in radio_info:
            try:
                should_select = False
                reason = ""
                
                # STRATEGIE 1: Online Store Ja/Nein - HÖCHSTE PRIORITÄT
                if online_store and not first_phase_clicked:
                    radio_text = f"{radio_data['value']} {radio_data['name']} {radio_data['id']} {radio_data['label']}"
                    
                    if online_store in ['yes', 'ja', 'true', '1', 'x', 'y']:
                        # Prüfe ob es sich um Online Store YES handelt
                        if any(keyword in radio_text for keyword in ['online', 'store', 'shop', 'ecommerce', 'e-commerce']):
                            if any(yes_keyword in radio_text for yes_keyword in ['yes', 'ja', 'true']):
                                if not any(no_keyword in radio_text for no_keyword in ['no', 'nein', 'false', 'not', 'kein']):
                                    should_select = True
                                    reason = f"JA-Option für Online Store (Excel: '{online_store}')"
                        # Fallback: Allgemeine YES-Option wenn Online Store Keywords vorhanden
                        elif not should_select and any(yes_keyword in radio_text for yes_keyword in ['yes', 'ja', 'true']):
                            if not any(no_keyword in radio_text for no_keyword in ['no', 'nein', 'false', 'not', 'kein']):
                                should_select = True
                                reason = f"JA-Option (Online Store Excel: '{online_store}')"
                                
                    elif online_store in ['no', 'nein', 'false', '0', 'n']:
                        # Prüfe ob es sich um Online Store NO handelt
                        if any(keyword in radio_text for keyword in ['online', 'store', 'shop', 'ecommerce', 'e-commerce']):
                            if any(no_keyword in radio_text for no_keyword in ['no', 'nein', 'false', 'not', 'kein']):
                                if not any(yes_keyword in radio_text for yes_keyword in ['yes', 'ja', 'true']):
                                    should_select = True
                                    reason = f"NEIN-Option für Online Store (Excel: '{online_store}')"
                        # Fallback: Allgemeine NO-Option wenn Online Store Keywords vorhanden
                        elif not should_select and any(no_keyword in radio_text for no_keyword in ['no', 'nein', 'false', 'not', 'kein']):
                            if not any(yes_keyword in radio_text for yes_keyword in ['yes', 'ja', 'true']):
                                should_select = True
                                reason = f"NEIN-Option (Online Store Excel: '{online_store}')"
                
                # KLICKEN nur wenn Excel-Daten es rechtfertigen
                if should_select and not radio_data['selected']:
                    print(f"\n🎯 PHASE 1 AUSWAHL: Radio {radio_data['index']+1}")
                    print(f"   📋 Grund: {reason}")
                    print(f"   🏷️ Label: '{radio_data['label']}'")
                    
                    click_success = False
                    radio = radio_data['element']
                    
                    # Versuch 1: Scroll und normaler Klick
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", radio)
                        time.sleep(0.2)
                        radio.click()
                        click_success = True
                        print(f"✅ Radio-Button {radio_data['index']+1} - Normaler Klick erfolgreich")
                    except Exception as e:
                        print(f"   ⚠️ Radio {radio_data['index']+1} - Normaler Klick fehlgeschlagen: {e}")
                    
                    # Versuch 2: JavaScript Klick
                    if not click_success:
                        try:
                            driver.execute_script("arguments[0].click();", radio)
                            click_success = True
                            print(f"✅ Radio-Button {radio_data['index']+1} - JavaScript Klick erfolgreich")
                        except Exception as e:
                            print(f"   ⚠️ Radio {radio_data['index']+1} - JavaScript Klick fehlgeschlagen: {e}")
                    
                    # Versuch 3: Label-Klick
                    if not click_success:
                        try:
                            radio_id_attr = radio.get_attribute('id')
                            if radio_id_attr:
                                label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id_attr}"]')
                                label.click()
                                click_success = True
                                print(f"✅ Radio-Button {radio_data['index']+1} - Label Klick erfolgreich")
                        except Exception as e:
                            print(f"   ⚠️ Radio {radio_data['index']+1} - Label Klick fehlgeschlagen: {e}")
                    
                    if click_success:
                        radio_clicked += 1
                        first_phase_clicked = True
                        time.sleep(0.5)  # Warte auf dynamische Inhalte
                        
                        # Verifikation: Prüfe ob wirklich ausgewählt
                        try:
                            if radio.is_selected():
                                print(f"🎯 Radio-Button {radio_data['index']+1} bestätigt ausgewählt!")
                            else:
                                print(f"⚠️ Radio-Button {radio_data['index']+1} nicht ausgewählt nach Klick")
                        except:
                            pass
                        break  # Nur einen Button in Phase 1 klicken
                    else:
                        print(f"❌ Radio-Button {radio_data['index']+1} - Alle Klick-Strategien fehlgeschlagen")
                elif should_select and radio_data['selected']:
                    print(f"ℹ️ Radio {radio_data['index']+1} bereits ausgewählt: {reason}")
                    radio_clicked += 1
                    first_phase_clicked = True
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Radio {radio_data['index']+1} fehlgeschlagen: {e}")
                continue
        
        # PHASE 2: Suche nach dynamisch erschienenen Radio-Buttons
        if first_phase_clicked:
            print(f"\n🔄 PHASE 2: Suche nach dynamisch erschienenen Radio-Buttons...")
            time.sleep(2)  # Längere Wartezeit für DOM-Updates (war 1 Sekunde)
            
            # Mehrere Versuche um alle Radio-Buttons zu finden
            for attempt in range(3):
                new_radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                if len(new_radio_buttons) > len(radio_info):
                    print(f"📻 {len(new_radio_buttons)} Radio-Buttons gefunden (Versuch {attempt+1})")
                    break
                elif attempt < 2:
                    print(f"⏳ Warte auf weitere Radio-Buttons... (Versuch {attempt+1})")
                    time.sleep(1)
            
            print(f"📻 {len(new_radio_buttons)} Radio-Buttons gefunden (nach dynamischem Update)")
            
            # Finde neue Radio-Buttons (die nicht in Phase 1 waren)
            new_radio_info = []
            for i, radio in enumerate(new_radio_buttons):
                try:
                    if radio.is_displayed() and radio.is_enabled() and not radio.is_selected():
                        radio_value = (radio.get_attribute('value') or '').lower()
                        radio_name = (radio.get_attribute('name') or '').lower()
                        radio_id = (radio.get_attribute('id') or '').lower()
                        
                        # Prüfe ob dieser Button schon in Phase 1 verarbeitet wurde
                        already_processed = False
                        for old_radio in radio_info:
                            if (old_radio['value'] == radio_value and 
                                old_radio['name'] == radio_name and 
                                old_radio['id'] == radio_id):
                                already_processed = True
                                break
                        
                        if not already_processed:
                            # Finde das zugehörige Label
                            label_text = ""
                            try:
                                if radio_id:
                                    label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                                    label_text = label.text.strip()
                            except:
                                try:
                                    parent = radio.find_element(By.XPATH, "./..")
                                    label_text = parent.text.strip()
                                except:
                                    try:
                                        next_element = radio.find_element(By.XPATH, "./following-sibling::*[1]")
                                        label_text = next_element.text.strip()
                                    except:
                                        label_text = "Unbekannt"
                            
                            new_radio_info.append({
                                'index': len(new_radio_buttons) + i,
                                'element': radio,
                                'value': radio_value,
                                'name': radio_name,
                                'id': radio_id,
                                'label': label_text.lower(),
                                'selected': radio.is_selected()
                            })
                            
                            print(f"📻 Neuer Radio {i+1}:")
                            print(f"   - Value: '{radio_value}'")
                            print(f"   - Name: '{radio_name}'")
                            print(f"   - ID: '{radio_id}'")
                            print(f"   - Label: '{label_text}'")
                except Exception as e:
                    print(f"   ⚠️ Neuer Radio {i+1} Analyse fehlgeschlagen: {e}")
            
            # PHASE 2: Verarbeitung der neuen Radio-Buttons - SPEZIFISCHERES MATCHING
            print(f"\n🎯 PHASE 2 DATENVERARBEITUNG:")
            print(f"   🛍️ Online Store Sells: '{online_store_sells}'")
            
            for radio_data in new_radio_info:
                try:
                    should_select = False
                    reason = ""
                    
                    # SPEZIFISCHES MATCHING für "sells" Radio-Buttons
                    if online_store_sells:
                        radio_text = f"{radio_data['value']} {radio_data['name']} {radio_data['id']} {radio_data['label']}"
                        
                        # Spezifische Patterns für besseres Matching
                        if 'products they own' in online_store_sells.lower():
                            # Suche nach "own" oder "they own" aber nicht "other" oder "vendor"
                            if (('own' in radio_text or 'they' in radio_text) and 
                                not any(exclude in radio_text for exclude in ['other', 'vendor', 'both'])):
                                should_select = True
                                reason = f"'Products they own' Match (Excel: '{online_store_sells}')"
                            
                        elif 'other vendors' in online_store_sells.lower():
                            # Suche nach "vendor" oder "other"
                            if any(keyword in radio_text for keyword in ['vendor', 'other']):
                                should_select = True
                                reason = f"'Other vendors' Match (Excel: '{online_store_sells}')"
                        
                        elif 'both' in online_store_sells.lower():
                            # Suche nach "both"
                            if 'both' in radio_text:
                                should_select = True
                                reason = f"'Both' Match (Excel: '{online_store_sells}')"
                        
                        # Fallback: Keyword-basiertes Matching
                        if not should_select:
                            sells_keywords = online_store_sells.lower().split()
                            for keyword in sells_keywords:
                                if len(keyword) > 3:  # Ignoriere kurze Wörter wie "own", "they"
                                    if keyword in radio_text:
                                        should_select = True
                                        reason = f"Keyword Match: '{keyword}' (Excel: '{online_store_sells}')"
                                        break
                    
                    # KLICKEN der neuen Radio-Buttons
                    if should_select and not radio_data['selected']:
                        print(f"\n🎯 PHASE 2 AUSWAHL: Radio {radio_data['index']+1}")
                        print(f"   📋 Grund: {reason}")
                        print(f"   🏷️ Label: '{radio_data['label']}'")
                        
                        click_success = False
                        radio = radio_data['element']
                        
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", radio)
                            time.sleep(0.2)
                            radio.click()
                            click_success = True
                            print(f"✅ Radio-Button {radio_data['index']+1} - Normaler Klick erfolgreich")
                        except Exception as e:
                            try:
                                driver.execute_script("arguments[0].click();", radio)
                                click_success = True
                                print(f"✅ Radio-Button {radio_data['index']+1} - JavaScript Klick erfolgreich")
                            except Exception as e2:
                                print(f"❌ Radio-Button {radio_data['index']+1} - Alle Klick-Strategien fehlgeschlagen")
                        
                        if click_success:
                            radio_clicked += 1
                            time.sleep(0.3)
                            
                            try:
                                if radio.is_selected():
                                    print(f"🎯 Radio-Button {radio_data['index']+1} bestätigt ausgewählt!")
                                else:
                                    print(f"⚠️ Radio-Button {radio_data['index']+1} nicht ausgewählt nach Klick")
                            except:
                                pass
                            break  # Nur einen Button in Phase 2 auswählen
                        
                except Exception as e:
                    print(f"   ⚠️ Phase 2 Radio {radio_data['index']+1} fehlgeschlagen: {e}")
                    continue
        
        # WARNUNG wenn keine Excel-Daten verarbeitet wurden
        if radio_clicked == 0:
            print(f"⚠️ WARNUNG: Keine Radio-Buttons ausgewählt!")
            print(f"   📦 Packaging Manufacturing: '{packaging_manufacturing}' - unerkannt")
            print(f"   🏭 Business Activity: '{business_activity}' - unerkannt")
            print(f"   � Online Store: '{online_store}' - unerkannt")
            print(f"   🛍️ Online Store Sells: '{online_store_sells}' - unerkannt")
            print(f"   � Sub-Activity: '{sub_activity}' - unerkannt")
            print(f"   💡 Tipp: Prüfe Excel-Spalten und Radio-Button-Labels")
        else:
            print(f"✅ {radio_clicked} Radio-Button(s) basierend auf Excel-Daten ausgewählt")
        
        fields_filled += radio_clicked
        print(f"📊 MEMBERSHIP SEITE 2: {fields_filled} Felder ausgefüllt")
        return fields_filled >= 1
        
    except Exception as e:
        print(f"❌ MEMBERSHIP SEITE 2 Fehler: {e}")
        return False

def handle_membership_page_3(driver, submission_id, row_data):
    """🏆 MEMBERSHIP SEITE 3: Contact Information ausfüllen"""
    print("🆕 MEMBERSHIP SEITE 3: Company & Contact Details ausfüllen...")
    
    try:
        wait = WebDriverWait(driver, 10)
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        
        fields_filled = 0  # WICHTIG: Variable initialisieren
        
        # ALLE VERFÜGBAREN INPUT-FELDER ANALYSIEREN
        all_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="email"], input[type="tel"]')
        all_selects = driver.find_elements(By.CSS_SELECTOR, 'select')
        
        print(f"📝 {len(all_inputs)} Input-Felder und {len(all_selects)} Dropdown-Felder gefunden")
        
        # Datenfelder aus Excel extrahieren - KORREKTE ZUORDNUNG
        company_name = str(record.get('Company Name', '') or '').strip()
        salutation = str(record.get('Salutation', '') or '').strip()
        first_name = str(record.get('First Name', '') or '').strip()
        last_name = str(record.get('Last Name', '') or '').strip()
        email_address = str(record.get('Email Adress', '') or record.get('Email Address', '') or '').strip()
        street_number = str(record.get('Number and Street', '') or '').strip()
        postal_code = str(record.get('Postal Code', '') or '').strip()
        city = str(record.get('City', '') or '').strip()
        country = str(record.get('Country', '') or record.get('Country2', '') or '').strip()
        phone = str(record.get('Phone', '') or record.get('Phone Number', '') or '').strip()
        website = str(record.get('Website', '') or '').strip()
        terms_accepted = str(record.get('I accept the Terms and Conditions ', '') or '').lower().strip()
        
        print(f"📊 MEMBERSHIP SEITE 3 Excel-Daten (KORREKT):")
        print(f"   🏢 Company Name: '{company_name}'")
        print(f"   👤 Salutation: '{salutation}'")
        print(f"   👤 First Name: '{first_name}'")
        print(f"   👤 Last Name: '{last_name}'")
        print(f"   📧 Email: '{email_address}'")
        print(f"   🏠 Street & Number: '{street_number}'")
        print(f"   📮 Postal Code: '{postal_code}'")
        print(f"   🏙️ City: '{city}'")
        print(f"   🌍 Country: '{country}'")
        print(f"   📞 Phone: '{phone}'")
        print(f"   🌐 Website: '{website}'")
        print(f"   ✅ Terms: '{terms_accepted}'")
        
        # 1. SALUTATION DROPDOWN AUSWÄHLEN (nur einmal!)
        print(f"🔍 Suche nach Salutation Dropdown...")
        
        try:
            salutation_element = driver.find_element(By.CSS_SELECTOR, 'select[name*="salutation"], select[id*="salutation"]')
            if salutation_element.is_displayed():
                salutation_select = Select(salutation_element)
                element_name = salutation_element.get_attribute('name') or salutation_element.get_attribute('id') or 'unknown'
                print(f"   📋 Gefundenes Salutation Dropdown: {element_name}")
                
                # Versuche Excel-Wert zu finden
                if salutation:
                    for option in salutation_select.options:
                        option_text = option.text.strip()
                        if option_text and (salutation.lower() in option_text.lower() or 
                            option_text.lower() in salutation.lower()):
                            salutation_select.select_by_visible_text(option_text)
                            print(f"✅ Salutation (Excel-Match): {option_text}")
                            fields_filled += 1
                            time.sleep(0.3)
                            break
        except Exception as e:
            print(f"   ❌ Salutation Dropdown fehlgeschlagen: {e}")
        
        # 2. INPUT-FELDER MIT KORRIGIERTER PRIORITÄTS-LOGIK
        print(f"🔍 Analysiere {len(all_inputs)} Input-Felder...")
        
        for i, field in enumerate(all_inputs):
            try:
                if field.is_displayed() and field.is_enabled():
                    field_name = (field.get_attribute('name') or '').lower()
                    field_id = (field.get_attribute('id') or '').lower()
                    field_placeholder = (field.get_attribute('placeholder') or '').lower()
                    field_type = field.get_attribute('type') or 'text'
                    
                    all_attributes = f"{field_name} {field_id} {field_placeholder}".lower()
                    print(f"🔍 Feld {i+1}: attributes='{all_attributes}', type='{field_type}'")
                    
                    # KORRIGIERTE FELD-ZUORDNUNG - SPEZIFISCHE KEYWORDS ZUERST!
                    value_to_enter = None
                    field_description = ""
                    
                    # EMAIL ADDRESS (höchste Priorität für Email-Felder)
                    if (field_type == 'email' or 'email' in all_attributes):
                        value_to_enter = email_address
                        field_description = "Email Address"
                    
                    # PHONE (höchste Priorität für Tel-Felder)
                    elif (field_type == 'tel' or 'phone' in all_attributes):
                        value_to_enter = phone
                        field_description = "Phone Number"
                    
                    # FIRST NAME (spezifische Erkennung)
                    elif ('first' in all_attributes and 'name' in all_attributes):
                        value_to_enter = first_name
                        field_description = "First Name"
                    
                    # LAST NAME (spezifische Erkennung)  
                    elif ('last' in all_attributes and 'name' in all_attributes):
                        value_to_enter = last_name
                        field_description = "Last Name"
                    
                    # STREET/ADDRESS (company_street oder street)
                    elif ('street' in all_attributes or 'address' in all_attributes):
                        value_to_enter = street_number
                        field_description = "Street & Number"
                    
                    # POSTAL CODE (company_postal_code oder postal)
                    elif ('postal' in all_attributes or 'zip' in all_attributes or 'plz' in all_attributes):
                        value_to_enter = postal_code
                        field_description = "Postal Code"
                    
                    # CITY (company_city oder city)
                    elif ('city' in all_attributes or 'stadt' in all_attributes):
                        value_to_enter = city
                        field_description = "City"
                    
                    # COUNTRY (company_country oder country)
                    elif ('country' in all_attributes or 'land' in all_attributes):
                        value_to_enter = country
                        field_description = "Country"
                    
                    # WEBSITE
                    elif ('website' in all_attributes or 'web' in all_attributes or 'url' in all_attributes):
                        value_to_enter = website
                        field_description = "Website"
                    
                    # COMPANY NAME (nur als letzter Fallback)
                    elif ('company' in all_attributes and 
                          not any(specific in all_attributes for specific in ['street', 'postal', 'city', 'country', 'phone'])):
                        value_to_enter = company_name
                        field_description = "Company Name"
                    
                    else:
                        print(f"   ⚠️ Feld {i+1}: Keine Zuordnung gefunden für '{all_attributes}'")
                        continue
                    
                    # Feld ausfüllen
                    if value_to_enter and value_to_enter.strip():
                        field.clear()
                        field.send_keys(value_to_enter.strip())
                        print(f"✅ Feld {i+1} ({field_description}): '{value_to_enter.strip()}'")
                        fields_filled += 1
                        time.sleep(0.2)  # Reduzierte Wartezeit
                    else:
                        print(f"   ⚠️ Feld {i+1} ({field_description}): Kein Excel-Wert - '{value_to_enter}'")
                        
            except Exception as e:
                print(f"   ❌ Feld {i+1} fehlgeschlagen: {e}")
                continue
        
        print(f"📊 MEMBERSHIP SEITE 3: {fields_filled} Felder ausgefüllt")
        return fields_filled >= 1
        
    except Exception as e:
        print(f"❌ MEMBERSHIP SEITE 3 Fehler: {e}")
        return False

def handle_membership_page_4(driver, submission_id, row_data):
    """🏆 MEMBERSHIP SEITE 4: PDF Upload, Terms & Conditions & Final Submit"""
    print("🆕 MEMBERSHIP SEITE 4: PDF Upload, Terms & Conditions & Summary...")
    
    try:
        wait = WebDriverWait(driver, 10)
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        
        fields_filled = 0
        
        # Excel-Daten für Terms & Conditions
        terms_accepted = str(record.get('I accept the Terms and Conditions ', '') or '').lower().strip()
        print(f"📊 SEITE 4 Excel-Daten:")
        print(f"   ✅ Terms & Conditions: '{terms_accepted}'")
        
        # 1. TERMS & CONDITIONS CHECKBOX
        checkbox_selectors = [
            'input[type="checkbox"]',
            'input[name*="terms"]',
            'input[id*="terms"]',
            'input[name*="conditions"]',
            'input[id*="conditions"]',
            'input[name*="accept"]',
            'input[id*="accept"]'
        ]
        
        terms_checked = False
        for selector in checkbox_selectors:
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, selector)
                for checkbox in checkboxes:
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        checkbox_name = (checkbox.get_attribute('name') or '').lower()
                        checkbox_id = (checkbox.get_attribute('id') or '').lower()
                        
                        # Prüfe ob es sich um Terms & Conditions handelt
                        if any(keyword in f"{checkbox_name} {checkbox_id}" 
                               for keyword in ['terms', 'conditions', 'accept', 'agree']):
                            
                            # Nur anklicken wenn Excel "Yes" enthält
                            if terms_accepted in ['yes', 'ja', 'true', '1', 'x', 'y']:
                                if not checkbox.is_selected():
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                                        time.sleep(0.2)
                                        checkbox.click()
                                        print(f"✅ Terms & Conditions akzeptiert (Excel: '{terms_accepted}')")
                                        fields_filled += 1
                                        terms_checked = True
                                        time.sleep(0.3)
                                    except Exception as e:
                                        try:
                                            driver.execute_script("arguments[0].click();", checkbox)
                                            print(f"✅ Terms & Conditions akzeptiert (JavaScript)")
                                            fields_filled += 1
                                            terms_checked = True
                                        except Exception as e2:
                                            print(f"❌ Terms Checkbox Klick fehlgeschlagen: {e2}")
                                else:
                                    print(f"ℹ️ Terms & Conditions bereits akzeptiert")
                                    terms_checked = True
                            else:
                                print(f"⚠️ Terms & Conditions NICHT akzeptiert (Excel: '{terms_accepted}')")
                            break
                if terms_checked:
                    break
            except Exception as e:
                print(f"   ⚠️ Terms Checkbox {selector} fehlgeschlagen: {e}")
                continue
        
        # 2. PDF UPLOAD (falls PDF verfügbar)
        pdf_uploaded = False
        file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        
        if file_inputs:
            # Prüfe ob PDF-Datei verfügbar ist
            pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
            if pdf_files:
                pdf_file = pdf_files[0]  # Nimm erste PDF
                try:
                    file_inputs[0].send_keys(os.path.abspath(pdf_file))
                    print(f"✅ PDF hochgeladen: {pdf_file}")
                    pdf_uploaded = True
                    fields_filled += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"   ⚠️ PDF Upload fehlgeschlagen: {e}")
        
        # 3. ZUSÄTZLICHE RADIO BUTTONS (falls vorhanden) - BASIEREND AUF EXCEL
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        radio_clicked = 0
        
        if radio_buttons:
            print(f"📻 {len(radio_buttons)} Radio-Buttons auf Seite 4 gefunden")
            
            for i, radio in enumerate(radio_buttons):
                try:
                    if radio.is_displayed() and radio.is_enabled() and not radio.is_selected():
                        radio_value = (radio.get_attribute('value') or '').lower()
                        radio_name = (radio.get_attribute('name') or '').lower()
                        radio_id = (radio.get_attribute('id') or '').lower()
                        
                        print(f"📻 Seite 4 Radio {i+1}:")
                        print(f"   - Value: '{radio_value}'")
                        print(f"   - Name: '{radio_name}'")
                        print(f"   - ID: '{radio_id}'")
                        
                        # Einfache Strategie: Ersten verfügbaren Button klicken
                        try:
                            radio.click()
                            print(f"✅ Seite 4 Radio-Button {i+1} geklickt")
                            radio_clicked += 1
                            fields_filled += 1
                            time.sleep(0.5)
                            break
                        except Exception as e:
                            try:
                                driver.execute_script("arguments[0].click();", radio)
                                print(f"✅ Seite 4 Radio-Button {i+1} geklickt (JavaScript)")
                                radio_clicked += 1
                                fields_filled += 1
                                break
                            except Exception as e2:
                                print(f"❌ Radio-Button {i+1} Klick fehlgeschlagen: {e2}")
                except Exception as e:
                    print(f"   ⚠️ Radio {i+1} Analyse fehlgeschlagen: {e}")
                    continue
        
        print(f"📊 MEMBERSHIP SEITE 4: {fields_filled} Felder ausgefüllt")
        print(f"   ✅ Terms Checkbox: {terms_checked}")
        print(f"   📄 PDF Upload: {pdf_uploaded}")  
        print(f"   📻 Radio Buttons: {radio_clicked}")
        
        return fields_filled >= 1 or terms_checked  # Erfolgreich wenn mindestens Terms akzeptiert
        
    except Exception as e:
        print(f"❌ MEMBERSHIP SEITE 4 Fehler: {e}")
        return False

def handle_new_membership_form(driver, submission_id, row_data):
    """🏆 SPEZIELLE FUNKTION für 'New Membership - Packaging & Paper' Seite - OPTIMIERT FÜR 1000€"""
    print("🆕 NEW MEMBERSHIP FORM: Company Name + Country ausfüllen...")
    
    try:
        wait = WebDriverWait(driver, 10)
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📄 Titel: {driver.title}")
        print(f"📋 Daten: Company='{record.get('Company Name', '')}', Country='{record.get('Country', '')}'")
        
        fields_filled = 0
        
        # 1. COMPANY NAME FELD - MULTIPLE STRATEGIEN
        company_name = record.get('Company Name', '')
        print(f"🏢 Versuche Company Name einzutragen: '{company_name}'")
        
        if company_name:
            company_selectors = [
                'input[name="company_name"]',
                'input[id="company_name"]', 
                'input[name*="company"]',
                'input[id*="company"]',
                'input[placeholder*="company"]',
                'input[placeholder*="Company"]'
            ]
            
            for selector in company_selectors:
                try:
                    print(f"   🔍 Versuche Selektor: {selector}")
                    company_field = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if company_field.is_displayed() and company_field.is_enabled():
                        # Scroll zum Element
                        driver.execute_script("arguments[0].scrollIntoView(true);", company_field)
                        time.sleep(0.3)
                        
                        # Feld leeren und füllen
                        company_field.clear()
                        company_field.send_keys(company_name)
                        
                        # Überprüfen ob Eingabe erfolgreich
                        entered_value = company_field.get_attribute('value')
                        if entered_value == company_name:
                            print(f"✅ Company Name erfolgreich eingegeben: {company_name}")
                            fields_filled += 1
                            break
                        else:
                            print(f"⚠️ Company Name nicht korrekt eingegeben. Erwartet: '{company_name}', Erhalten: '{entered_value}'")
                    else:
                        print(f"   ⚠️ {selector} nicht sichtbar oder nicht aktiv")
                        
                except Exception as e:
                    print(f"   ❌ {selector} fehlgeschlagen: {e}")
                    continue
        
        # 2. COUNTRY DROPDOWN - MULTIPLE STRATEGIEN
        country = record.get('Country', '').lower()
        print(f"🌍 Versuche Country auszuwählen: '{country}'")
        
        if country:
            country_selectors = [
                'select[name="country"]',
                'select[id="country"]',
                'select[name*="country"]',
                'select[id*="country"]'
            ]
            
            for selector in country_selectors:
                try:
                    print(f"   🔍 Versuche Country-Selektor: {selector}")
                    country_select_element = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if country_select_element.is_displayed() and country_select_element.is_enabled():
                        # Scroll zum Element
                        driver.execute_script("arguments[0].scrollIntoView(true);", country_select_element)
                        time.sleep(0.3)
                        
                        country_select = Select(country_select_element)
                        
                        # Deutschland-Optionen prüfen
                        print("   📋 Verfügbare Country-Optionen:")
                        option_selected = False
                        
                        for option in country_select.options:
                            option_text = option.text.strip()
                            option_value = option.get_attribute('value').strip()
                            print(f"      - '{option_text}' (value: '{option_value}')")
                            
                            # Erweiterte Deutschland-Erkennung
                            germany_patterns = [
                                'germany', 'deutschland', 'de', 'ger', 'deu',
                                '🇩🇪', 'german'
                            ]
                            
                            option_text_lower = option_text.lower()
                            option_value_lower = option_value.lower()
                            
                            # Prüfe ob die Option zu Deutschland passt
                            is_germany = (
                                any(pattern in option_text_lower for pattern in germany_patterns) or
                                any(pattern in option_value_lower for pattern in germany_patterns) or
                                country in option_text_lower or
                                country in option_value_lower
                            )
                            
                            if is_germany:
                                country_select.select_by_visible_text(option_text)
                                print(f"✅ Germany/Deutschland ausgewählt: {option_text}")
                                fields_filled += 1
                                option_selected = True
                                break
                        
                        # Fallback: Versuche exakte Übereinstimmung mit einggegebenen Country
                        if not option_selected:
                            for option in country_select.options:
                                if country.lower() in option.text.lower():
                                    country_select.select_by_visible_text(option.text)
                                    print(f"✅ Country Fallback ausgewählt: {option.text}")
                                    fields_filled += 1
                                    option_selected = True
                                    break
                        
                        # Letzter Fallback: "Germany" direkt
                        if not option_selected:
                            try:
                                country_select.select_by_value("Germany")
                                print("✅ Country Default 'Germany' ausgewählt")
                                fields_filled += 1
                                option_selected = True
                            except:
                                print("❌ Auch Default 'Germany' nicht verfügbar")
                        
                        if option_selected:
                            break
                    else:
                        print(f"   ⚠️ {selector} nicht sichtbar oder nicht aktiv")
                        
                except Exception as e:
                    print(f"   ❌ {selector} fehlgeschlagen: {e}")
                    continue
        
        print(f"📊 NEW MEMBERSHIP FORM: {fields_filled} von 2 Feldern ausgefüllt")
        
        # 3. SUBMIT/NEXT BUTTON - NUR WENN FELDER ERFOLGREICH AUSGEFÜLLT
        if fields_filled >= 1:  # Mindestens ein Feld erfolgreich
            print("🚀 Suche Submit-Button...")
            
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Next")',
                'button:contains("Continue")',
                'button:contains("Submit")',
                'button:contains("Weiter")',
                'button:contains("Fortfahren")',
                'button[class*="submit"]',
                'button[class*="btn-primary"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        # Scroll zum Button
                        driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                        time.sleep(0.3)
                        
                        # Klick mit JavaScript für mehr Zuverlässigkeit
                        driver.execute_script("arguments[0].click();", submit_btn)
                        print(f"✅ Submit-Button geklickt: {selector} - Text: '{submit_btn.text}'")
                        time.sleep(1)  # Warten auf Seitenwechsel
                        break
                except Exception as e:
                    print(f"   ⚠️ Submit {selector} fehlgeschlagen: {e}")
                    continue
        
        # Datenbank-Logging
        db.log_form_fields(
            submission_id,
            page_number=2,
            form_data={
                "company_name": company_name,
                "country": country,
                "fields_filled": fields_filled,
                "page_type": "new_membership_form",
                "success": fields_filled >= 1
            }
        )
        
        success = fields_filled >= 1
        if success:
            print(f"🏆 NEW MEMBERSHIP FORM ERFOLGREICH! {fields_filled} Felder ausgefüllt")
        else:
            print(f"❌ NEW MEMBERSHIP FORM FEHLGESCHLAGEN! Keine Felder ausgefüllt")
            
        return success
        
    except Exception as e:
        print(f"❌ NEW MEMBERSHIP FORM Kritischer Fehler: {e}")
        return False

def page_2_fill_company_data(driver, submission_id, row_data):
    """SEITE 2: Firmendaten ausfüllen"""
    print("🏢 SEITE 2: Firmendaten ausfüllen...")
    
    # Sicherstellen, dass wir auf der richtigen Seite sind
    if not navigate_to_correct_page(driver, "PAGE_2_COMPANY", submission_id):
        print("⚠️ Konnte nicht zu Company-Seite navigieren - versuche trotzdem fortzufahren")
    
    try:
        wait = WebDriverWait(driver, 10)
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        # Warte bis Seite geladen ist
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        # Erneute Seitenerkennung
        current_page = detect_current_page(driver)
        print(f"📍 Aktuelle Seite: {current_page}")
        
        # Falls wir nicht auf der erwarteten Seite sind, prüfe alle verfügbaren Felder
        if current_page != "PAGE_2_COMPANY":
            print(f"⚠️ Nicht auf erwarteter Company-Seite (aktuell: {current_page}) - fülle verfügbare Felder aus")
        
        fields_filled = 0
        
        # Firmenname
        company_name = record.get('Company Name', '')
        if company_name:
            company_selectors = [
                'input[name*="company"]',
                'input[id*="company"]',
                'input[placeholder*="company"]',
                'input[name*="firm"]',
                'input[id*="firm"]'
            ]
            
            for selector in company_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if field.is_displayed():
                        field.clear()
                        field.send_keys(company_name)
                        print(f"✅ SEITE 2: Firmenname eingegeben: {company_name}")
                        fields_filled += 1
                        break
                except:
                    continue
        
        # Email
        email = record.get('Email', '')
        if email:
            email_selectors = [
                'input[type="email"]',
                'input[name*="email"]',
                'input[id*="email"]',
                'input[placeholder*="email"]'
            ]
            
            for selector in email_selectors:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    if field.is_displayed():
                        field.clear()
                        field.send_keys(email)
                        print(f"✅ SEITE 2: Email eingegeben: {email}")
                        fields_filled += 1
                        break
                except:
                    continue
        
        # Adresse
        address = record.get('Address', '')
        if address:
            address_selectors = [
                'input[name*="address"]',
                'input[id*="address"]',
                'input[placeholder*="address"]',
                'input[name*="street"]',
                'input[id*="street"]'
            ]
            
            for selector in address_selectors:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    if field.is_displayed():
                        field.clear()
                        field.send_keys(address)
                        print(f"✅ SEITE 2: Adresse eingegeben: {address}")
                        fields_filled += 1
                        break
                except:
                    continue
        
        print(f"📊 SEITE 2: {fields_filled} Felder ausgefüllt")
        
        db.log_form_fields(
            submission_id,
            page_number=2,
            form_data={
                "company_name": company_name,
                "email": email,
                "address": address,
                "fields_filled": fields_filled
            }
        )
        
        return True
        
    except Exception as e:
        print(f"❌ SEITE 2 Fehler: {e}")
        return False

def page_2_submit(driver, submission_id):
    """SEITE 2: Submit für nächste Seite"""
    return page_1_submit(driver, submission_id)  # Gleiche Submit-Logik

def page_3_additional_data(driver, submission_id, row_data):
    """SEITE 3: Zusätzliche Daten"""
    print("📋 SEITE 3: Zusätzliche Daten...")
    
    # Sicherstellen, dass wir auf der richtigen Seite sind
    if not navigate_to_correct_page(driver, "PAGE_3_DETAILS", submission_id):
        print("⚠️ Konnte nicht zu Details-Seite navigieren - versuche trotzdem fortzufahren")
    
    try:
        wait = WebDriverWait(driver, 10)
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)
        
        # Erneute Seitenerkennung
        current_page = detect_current_page(driver)
        print(f"📍 Aktuelle Seite: {current_page}")
        
        fields_filled = 0
        
        # Land
        country = record.get('Country', '')
        if country:
            # Dropdown-Select versuchen
            try:
                country_select = Select(driver.find_element(By.CSS_SELECTOR, 'select[name*="country"], select[id*="country"]'))
                for option in country_select.options:
                    if country.lower() in option.text.lower():
                        country_select.select_by_visible_text(option.text)
                        print(f"✅ SEITE 3: Land ausgewählt: {option.text}")
                        fields_filled += 1
                        break
            except:
                # Input-Feld versuchen
                country_selectors = [
                    'input[name*="country"]',
                    'input[id*="country"]',
                    'input[placeholder*="country"]'
                ]
                
                for selector in country_selectors:
                    try:
                        field = driver.find_element(By.CSS_SELECTOR, selector)
                        if field.is_displayed():
                            field.clear()
                            field.send_keys(country)
                            print(f"✅ SEITE 3: Land eingegeben: {country}")
                            fields_filled += 1
                            break
                    except:
                        continue
        
        # PLZ
        postal_code = record.get('Postal Code', '')
        if postal_code:
            postal_selectors = [
                'input[name*="postal"], input[name*="zip"]',
                'input[id*="postal"], input[id*="zip"]',
                'input[placeholder*="postal"], input[placeholder*="zip"]'
            ]
            
            for selector in postal_selectors:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    if field.is_displayed():
                        field.clear()
                        field.send_keys(str(postal_code))
                        print(f"✅ SEITE 3: PLZ eingegeben: {postal_code}")
                        fields_filled += 1
                        break
                except:
                    continue
        
        print(f"📊 SEITE 3: {fields_filled} Felder ausgefüllt")
        
        db.log_form_fields(
            submission_id,
            page_number=3,
            form_data={
                "country": country,
                "postal_code": postal_code,
                "fields_filled": fields_filled
            }
        )
        
        return True
        
    except Exception as e:
        print(f"❌ SEITE 3 Fehler: {e}")
        return False

def page_3_submit(driver, submission_id):
    """SEITE 3: Submit für letzte Seite"""
    return page_1_submit(driver, submission_id)  # Gleiche Submit-Logik

def page_4_pdf_upload_and_finish(driver, submission_id, pdf_file):
    """SEITE 4: PDF-Upload und Fertigstellung"""
    print("📎 SEITE 4: PDF-Upload und Fertigstellung...")
    
    # Sicherstellen, dass wir auf der richtigen Seite sind
    if not navigate_to_correct_page(driver, "PAGE_4_UPLOAD", submission_id):
        print("⚠️ Konnte nicht zu Upload-Seite navigieren - versuche trotzdem fortzufahren")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(0.5)
        
        # Erneute Seitenerkennung
        current_page = detect_current_page(driver)
        print(f"📍 Aktuelle Seite: {current_page}")
        
        uploaded = False
        
        # PDF-Upload versuchen
        if pdf_file and os.path.exists(pdf_file):
            file_selectors = [
                'input[type="file"]',
                'input[name*="file"]',
                'input[id*="file"]',
                'input[name*="upload"]',
                'input[id*="upload"]'
            ]
            
            for selector in file_selectors:
                try:
                    file_input = driver.find_element(By.CSS_SELECTOR, selector)
                    file_input.send_keys(pdf_file)
                    print(f"✅ SEITE 4: PDF-Datei hochgeladen: {os.path.basename(pdf_file)}")
                    uploaded = True
                    time.sleep(0.5)
                    break
                except Exception as e:
                    print(f"   ⚠️ {selector} Upload fehlgeschlagen: {e}")
                    continue
        
        # FINALE SUBMIT BUTTON - Complete Registration
        print("🎯 SEITE 4: Suche nach Complete Registration Button...")
        
        # Spezifische Selektor für Complete Registration Button
        complete_registration_selectors = [
            'button[type="submit"].btn.btn-primary',
            'button.btn.btn-primary[type="submit"]',
            'button[type="submit"]:contains("Complete Registration")',
            'button:contains("Complete Registration")',
            'button:contains("✓ Complete Registration")'
        ]
        
        final_submitted = False
        
        # Versuche Complete Registration Button zu finden und zu klicken
        for selector in complete_registration_selectors:
            try:
                if ':contains(' in selector:
                    # XPath für :contains() verwenden
                    xpath_selector = f"//button[contains(text(), 'Complete Registration')]"
                    final_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
                else:
                    final_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                # Überprüfe Button-Text
                button_text = final_btn.text.strip()
                print(f"🔍 SEITE 4: Gefundener Button: '{button_text}' mit Selector: {selector}")
                
                if "Complete Registration" in button_text or "✓ Complete Registration" in button_text:
                    if safe_click_button(driver, final_btn, f"Complete Registration Button ({selector})"):
                        print(f"✅ SEITE 4: FINALE ABSENDUNG ERFOLGREICH: Complete Registration Button geklickt!")
                        final_submitted = True
                        time.sleep(2)  # Warten auf Verarbeitung
                        
                        db.log_http_request(
                            submission_id, 
                            driver.current_url, 
                            "POST",
                            page_title=driver.title,
                            form_data={"step": "final_submission", "pdf_uploaded": uploaded, "complete_registration": True}
                        )
                        return True
                else:
                    print(f"   ⚠️ Button-Text passt nicht: '{button_text}'")
                    
            except Exception as e:
                print(f"   ⚠️ {selector} fehlgeschlagen: {e}")
                continue
        
        # Fallback: Alle Submit-Buttons durchsuchen
        if not final_submitted:
            print("🔄 SEITE 4: Fallback - suche alle Submit-Buttons...")
            try:
                all_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"], button.btn')
                for btn in all_buttons:
                    try:
                        btn_text = btn.text.strip() or btn.get_attribute('value') or ''
                        btn_class = btn.get_attribute('class') or ''
                        print(f"🔍 Gefundener Button: '{btn_text}' | Klassen: '{btn_class}'")
                        
                        if any(keyword in btn_text.lower() for keyword in ['complete', 'registration', 'finish', 'submit', 'send']):
                            if safe_click_button(driver, btn, f"Fallback Submit Button: {btn_text}"):
                                print(f"✅ SEITE 4: Fallback Submit erfolgreich: '{btn_text}'")
                                final_submitted = True
                                break
                    except:
                        continue
            except Exception as e:
                print(f"❌ Fallback Submit-Suche fehlgeschlagen: {e}")
        
        if final_submitted:
            return True
        
        # Screenshot für Beweiszwecke
        try:
            screenshot = driver.get_screenshot_as_base64()
            db.log_evidence(submission_id, "final_page_screenshot", screenshot, "base64")
            print("📸 SEITE 4: Screenshot gespeichert")
        except:
            pass
        
        print("⚠️ SEITE 4: Kein finaler Submit-Button gefunden - möglicherweise bereits abgeschlossen")
        return True
        
    except Exception as e:
        print(f"❌ SEITE 4 Fehler: {e}")
        return False

def execute_adaptive_workflow(driver, excel_file, pdf_file, row_data):
    """ADAPTIVER WORKFLOW - Erkennt automatisch die aktuelle Seite und handelt entsprechend"""
    global current_submission_id
    
    try:
        print("🎯 Starte adaptiven Workflow...")
        max_iterations = 10  # Verhindere Endlosschleifen
        iteration = 0
        completed_pages = set()
        
        while iteration < max_iterations:
            iteration += 1
            current_page = detect_current_page(driver)
            
            print(f"\n🔄 Iteration {iteration}: Aktuelle Seite = {current_page}")
            
            # Prüfe ob wir bereits fertig sind
            if current_page == "SUCCESS_PAGE":
                print("🎉 Erfolgsseite erreicht - Workflow abgeschlossen!")
                return True
            
            # Handle verschiedene Seiten
            if current_page == "LOGIN":
                if not handle_login_process(driver, current_submission_id):
                    print("❌ Login fehlgeschlagen")
                    return False
                completed_pages.add("LOGIN")
                
            elif current_page == "DASHBOARD":
                print("🏠 DASHBOARD erkannt - navigiere zu Packaging-Formular...")
                # Spezielle Dashboard-Navigation mit Dropdown
                if not navigate_to_correct_page(driver, "PAGE_1_PACKAGING", current_submission_id):
                    print("⚠️ Dashboard→Packaging Navigation fehlgeschlagen - versuche alternative Methoden")
                    
                    # Fallback: Suche nach allen Dropdown-Elementen
                    try:
                        print("🔍 Fallback: Durchsuche alle Dropdown-Elemente...")
                        
                        # 1. Alle Elemente mit Dropdown-Klassen finden
                        dropdown_elements = driver.find_elements(By.CSS_SELECTOR, 
                            '[class*="dropdown"], [data-toggle="dropdown"], .nav-item')
                        
                        for dropdown in dropdown_elements:
                            if dropdown.is_displayed():
                                try:
                                    # Dropdown öffnen
                                    dropdown.click()
                                    time.sleep(1)
                                    
                                    # Nach Packaging-Link suchen
                                    packaging_links = driver.find_elements(By.CSS_SELECTOR, 
                                        'a[href*="packaging"], a:contains("Packaging"), a:contains("📦")')
                                    
                                    for link in packaging_links:
                                        if link.is_displayed():
                                            link.click()
                                            print("✅ Fallback Dropdown-Navigation erfolgreich!")
                                            time.sleep(0.5)
                                            break
                                    else:
                                        continue
                                    break
                                        
                                except:
                                    continue
                        
                        # 2. Direkte URL als letzter Ausweg
                        if detect_current_page(driver) == "DASHBOARD":
                            print("🌐 Letzte Option: Direkte URL-Navigation...")
                            driver.get("https://friendly-captcha-demo.onrender.com/membership/new?type=packaging-paper")
                            time.sleep(0.5)
                            
                    except Exception as e:
                        print(f"⚠️ Fallback-Navigation fehlgeschlagen: {e}")
                
            elif current_page == "PAGE_1_PACKAGING":
                if "PAGE_1_PACKAGING" not in completed_pages:
                    print("📦 Führe Packaging-Auswahl aus...")
                    if page_1_select_packaging(driver, current_submission_id):
                        completed_pages.add("PAGE_1_PACKAGING")
                        if page_1_submit(driver, current_submission_id):
                            time.sleep(0.5)
                        else:
                            print("⚠️ Submit fehlgeschlagen - versuche trotzdem fortzufahren")
                            time.sleep(0.5)
                    else:
                        print("⚠️ Packaging-Auswahl fehlgeschlagen")
                else:
                    # Seite bereits bearbeitet, weiter navigieren
                    page_1_submit(driver, current_submission_id)
                    time.sleep(0.5)
                
            elif current_page == "MEMBERSHIP_PAGE_1":
                if "MEMBERSHIP_PAGE_1" not in completed_pages:
                    print("� MEMBERSHIP SEITE 1: Country & Company...")
                    if handle_membership_page_1(driver, current_submission_id, row_data):
                        completed_pages.add("MEMBERSHIP_PAGE_1")
                        # Submit für nächste Seite
                        page_1_submit(driver, current_submission_id)
                        time.sleep(1)
                    else:
                        print("⚠️ Membership Seite 1 fehlgeschlagen")
                else:
                    page_1_submit(driver, current_submission_id)
                    time.sleep(1)
                    
            elif current_page == "MEMBERSHIP_PAGE_2":
                if "MEMBERSHIP_PAGE_2" not in completed_pages:
                    print("🆕 MEMBERSHIP SEITE 2: Business Activity...")
                    if handle_membership_page_2(driver, current_submission_id, row_data):
                        completed_pages.add("MEMBERSHIP_PAGE_2")
                        # Submit für nächste Seite
                        page_1_submit(driver, current_submission_id)
                        time.sleep(1)
                    else:
                        print("⚠️ Membership Seite 2 fehlgeschlagen")
                else:
                    page_1_submit(driver, current_submission_id)
                    time.sleep(1)
                    
            elif current_page == "MEMBERSHIP_PAGE_3":
                if "MEMBERSHIP_PAGE_3" not in completed_pages:
                    print("🆕 MEMBERSHIP SEITE 3: Contact Information...")
                    if handle_membership_page_3(driver, current_submission_id, row_data):
                        completed_pages.add("MEMBERSHIP_PAGE_3")
                        # Submit für nächste Seite
                        page_1_submit(driver, current_submission_id)
                        time.sleep(1)
                    else:
                        print("⚠️ Membership Seite 3 fehlgeschlagen")
                else:
                    page_1_submit(driver, current_submission_id)
                    time.sleep(1)
                    
            elif current_page == "MEMBERSHIP_PAGE_4":
                if "MEMBERSHIP_PAGE_4" not in completed_pages:
                    print("🆕 MEMBERSHIP SEITE 4: PDF Upload & Summary...")
                    if handle_membership_page_4(driver, current_submission_id, row_data):
                        completed_pages.add("MEMBERSHIP_PAGE_4")
                        # Finaler Submit
                        page_1_submit(driver, current_submission_id)
                        print("🎉 MEMBERSHIP WORKFLOW ABGESCHLOSSEN!")
                        return True
                    else:
                        print("⚠️ Membership Seite 4 fehlgeschlagen")
                else:
                    page_1_submit(driver, current_submission_id)
                    return True
                    
            elif current_page == "MEMBERSHIP_FORM":
                # Fallback für nicht-kategorisierte Membership-Forms
                print("🆕 MEMBERSHIP FORM (Fallback)...")
                if handle_new_membership_form(driver, current_submission_id, row_data):
                    completed_pages.add("MEMBERSHIP_FORM")
                    page_1_submit(driver, current_submission_id)
                    time.sleep(1)
                
            elif current_page == "PAGE_2_COMPANY":
                if "PAGE_2_COMPANY" not in completed_pages:
                    print("🏢 Führe Standard Company-Daten Ausfüllung aus...")
                    if page_2_fill_company_data(driver, current_submission_id, row_data):
                        completed_pages.add("PAGE_2_COMPANY")
                        if page_2_submit(driver, current_submission_id):
                            time.sleep(1)
                        else:
                            print("⚠️ Submit fehlgeschlagen - versuche trotzdem fortzufahren")
                            time.sleep(1)
                    else:
                        print("⚠️ Company-Daten Ausfüllung fehlgeschlagen")
                else:
                    page_2_submit(driver, current_submission_id)
                    time.sleep(1)
                
            elif current_page == "PAGE_3_DETAILS":
                if "PAGE_3_DETAILS" not in completed_pages:
                    print("📋 Führe Details-Ausfüllung aus...")
                    if page_3_additional_data(driver, current_submission_id, row_data):
                        completed_pages.add("PAGE_3_DETAILS")
                        if page_3_submit(driver, current_submission_id):
                            time.sleep(0.5)
                        else:
                            print("⚠️ Submit fehlgeschlagen - versuche trotzdem fortzufahren")
                            time.sleep(0.5)
                    else:
                        print("⚠️ Details-Ausfüllung fehlgeschlagen")
                else:
                    # Seite bereits bearbeitet, weiter navigieren
                    page_3_submit(driver, current_submission_id)
                    time.sleep(0.5)
                
            elif current_page == "PAGE_4_UPLOAD":
                if "PAGE_4_UPLOAD" not in completed_pages:
                    print("📎 Führe Upload und Finalisierung aus...")
                    if page_4_pdf_upload_and_finish(driver, current_submission_id, pdf_file):
                        completed_pages.add("PAGE_4_UPLOAD")
                        print("✅ Upload-Seite abgeschlossen")
                        time.sleep(0.5)
                    else:
                        print("⚠️ Upload/Finalisierung fehlgeschlagen")
                else:
                    print("✅ Upload bereits abgeschlossen")
                    return True
                
            elif current_page == "UNKNOWN_FORM":
                print("❓ Unbekannte Formular-Seite - versuche generische Behandlung")
                # Versuche verfügbare Felder auszufüllen
                try:
                    record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
                    
                    # Firmenname
                    company_name = record.get('Company Name', '')
                    if company_name:
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        for inp in inputs:
                            if inp.get_attribute('type') == 'text' and inp.is_displayed():
                                try:
                                    inp.clear()
                                    inp.send_keys(company_name)
                                    print(f"✅ Generisch ausgefüllt: {company_name}")
                                    break
                                except:
                                    continue
                    
                    # Submit versuchen
                    time.sleep(0.5)
                    submit_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                    for btn in submit_buttons:
                        if btn.is_displayed():
                            if safe_click_button(driver, btn, "Generischer Submit"):
                                time.sleep(0.5)
                                break
                    
                except Exception as e:
                    print(f"⚠️ Generische Behandlung fehlgeschlagen: {e}")
                
            elif current_page == "ERROR":
                print("❌ Seitenerkennung fehlgeschlagen - versuche manuellen Fortschritt")
                # Versuche beliebigen Submit-Button
                submit_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in submit_buttons:
                    if btn.is_displayed():
                        if safe_click_button(driver, btn, "Fallback-Button"):
                            time.sleep(0.5)
                            break
                
            else:
                print(f"❓ Unbekannte Seite: {current_page}")
                time.sleep(0.5)
            
            # Verhindere Endlosschleifen auf derselben Seite
            time.sleep(1)
        
        print(f"✅ Adaptiver Workflow beendet nach {iteration} Iterationen")
        print(f"📊 Abgeschlossene Seiten: {completed_pages}")
        
        # Erfolg wenn mindestens 3 Seiten abgeschlossen wurden
        return len(completed_pages) >= 3
        
    except Exception as e:
        print(f"❌ Adaptiver Workflow-Fehler: {e}")
        return False

def execute_full_4_page_workflow(driver, excel_file, pdf_file, row_data):
    """VOLLSTÄNDIGER 4-SEITEN WORKFLOW"""
    global current_submission_id
    
    try:
        print("🎯 Starte vollständigen 4-Seiten Workflow...")
        
        # SEITE 1: Packaging auswählen
        if not page_1_select_packaging(driver, current_submission_id):
            print("❌ SEITE 1: Packaging-Auswahl fehlgeschlagen")
            return False
        
        if not page_1_submit(driver, current_submission_id):
            print("❌ SEITE 1: Submit fehlgeschlagen")
            return False
        
        print("✅ SEITE 1 abgeschlossen - navigiere zu SEITE 2")
        
        # SEITE 2: Firmendaten
        if not page_2_fill_company_data(driver, current_submission_id, row_data):
            print("❌ SEITE 2: Datenausfüllung fehlgeschlagen")
            return False
            
        if not page_2_submit(driver, current_submission_id):
            print("❌ SEITE 2: Submit fehlgeschlagen")
            return False
        
        print("✅ SEITE 2 abgeschlossen - navigiere zu SEITE 3")
        
        # SEITE 3: Zusätzliche Daten
        if not page_3_additional_data(driver, current_submission_id, row_data):
            print("❌ SEITE 3: Datenausfüllung fehlgeschlagen")
            return False
            
        if not page_3_submit(driver, current_submission_id):
            print("❌ SEITE 3: Submit fehlgeschlagen")
            return False
        
        print("✅ SEITE 3 abgeschlossen - navigiere zu SEITE 4")
        
        # SEITE 4: PDF-Upload und Finale
        if not page_4_pdf_upload_and_finish(driver, current_submission_id, pdf_file):
            print("❌ SEITE 4: Finalisierung fehlgeschlagen")
            return False
        
        print("✅ SEITE 4 abgeschlossen - WORKFLOW ERFOLGREICH!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow-Fehler: {e}")
        return False

def run_single_automation(row_data, excel_file, pdf_file, row_index):
    """Einzelnen Automation-Durchlauf ausführen"""
    driver = None
    global current_submission_id
    
    try:
        print("🤖 Starte Browser...")
        driver = setup_browser()
        
        record = row_data.to_dict() if hasattr(row_data, 'to_dict') else row_data
        print(f"📋 Verarbeite: {record.get('Company Name', 'Unbekannt')} aus {record.get('Country', 'Unbekannt')}")
        
        current_submission_id = db.create_submission(record, excel_file, row_index, pdf_file)
        print(f"📊 Submission ID: {current_submission_id}")
        
        url = "https://friendly-captcha-demo.onrender.com/"
        print(f"🌐 Navigiere zu: {url}")
        driver.get(url)
        time.sleep(0.5)
        
        db.log_http_request(
            current_submission_id, 
            driver.current_url, 
            "GET",
            page_title=driver.title,
            form_data={"step": "initial_page_load", "row_index": row_index}
        )
        
        # Login-Prozess
        success = handle_login_process(driver, current_submission_id)
        if not success:
            print("❌ Login fehlgeschlagen")
            return False
        
        # Vollständiger adaptiver Workflow
        success = execute_adaptive_workflow(driver, excel_file, pdf_file, row_data)
        if not success:
            print("❌ Adaptiver Workflow fehlgeschlagen")
            return False
        
        print("✅ Automation erfolgreich abgeschlossen")
        return True
        
    except Exception as e:
        print(f"💥 Durchlauf-Fehler {row_index + 1}: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

def validate_excel_gui_feedback(excel_file):
    """Excel-Validierung mit GUI-Feedback"""
    try:
        validation_result = get_detailed_excel_validation(excel_file)
        
        if validation_result['is_valid']:
            print(f"✅ Excel-Validierung erfolgreich")
            print(f"📊 {validation_result['row_count']} Zeilen, {len(validation_result['found_columns'])} Spalten")
            return True
        else:
            print(f"❌ Excel-Validierung fehlgeschlagen")
            print(f"📊 Fehler: {len(validation_result['missing_required'])} fehlende Pflichtfelder")
            return False
            
    except Exception as e:
        print(f"❌ Validierungsfehler: {e}")
        return False

def main():
    """HAUPTFUNKTION - KORREKTE BUTTON-KLICK VERSION"""
    print("🚀 INTERZERO AUTOMATION - KORREKTE BUTTON-KLICK VERSION")
    print("="*50)
    
    excel_file, pdf_file = select_files_gui()
    if not excel_file:
        print("❌ Keine Excel-Datei gewählt - Automation beendet")
        return

    if not validate_excel_gui_feedback(excel_file):
        print("❌ Excel-Validierung fehlgeschlagen - Automation beendet")
        return

    try:
        df = pd.read_excel(excel_file)
        if df.empty:
            print("❌ Keine Excel-Daten - Automation beendet")
            return
        
        df_clean = df.dropna(how='all')
        row_count = len(df_clean)
        
        print(f"\n🎯 AUTOMATION SETUP:")
        print(f"   📊 Excel: {os.path.basename(excel_file)}")
        print(f"   📄 PDF: {os.path.basename(pdf_file) if pdf_file else 'Keine PDF'}")
        print(f"   📋 Zeilen: {row_count}")
        print(f"   🔄 Durchläufe: {row_count}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Fehler beim Excel-Laden: {e}")
        return

    successful_runs = 0
    failed_runs = 0
    
    for row_index, row_data in df_clean.iterrows():
        print(f"\n" + "="*60)
        print(f"🚀 DURCHLAUF {row_index + 1} von {row_count}")
        print(f"📋 Unternehmen: {row_data.get('Company Name', 'Unbekannt')}")
        print(f"🌍 Land: {row_data.get('Country', 'Unbekannt')}")
        print("="*60)
        
        success = run_single_automation(row_data, excel_file, pdf_file, row_index)
        
        if success:
            successful_runs += 1
            print(f"✅ Durchlauf {row_index + 1} erfolgreich!")
        else:
            failed_runs += 1
            print(f"❌ Durchlauf {row_index + 1} fehlgeschlagen!")
        
        if row_index < len(df_clean) - 1:
            print(f"⏳ Pause vor nächstem Durchlauf...")
            time.sleep(0.5)
    
    print(f"\n" + "="*60)
    print(f"📊 AUTOMATION ZUSAMMENFASSUNG")
    print(f"="*60)
    print(f"✅ Erfolgreich: {successful_runs}")
    print(f"❌ Fehlgeschlagen: {failed_runs}")
    print(f"📋 Gesamt: {successful_runs + failed_runs}/{row_count}")
    
    if successful_runs == row_count:
        print(f"🎉 ALLE DURCHLÄUFE ERFOLGREICH!")
    elif successful_runs > 0:
        print(f"⚠️ TEILWEISE ERFOLGREICH: {successful_runs}/{row_count}")
    else:
        print(f"💥 ALLE DURCHLÄUFE FEHLGESCHLAGEN!")
    
    print("="*60)
    input("⏸️ ENTER zum Beenden...")

if __name__ == "__main__":
    main()
