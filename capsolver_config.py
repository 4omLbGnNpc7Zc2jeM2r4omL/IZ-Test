# CapSolver Konfiguration
# Tragen Sie hier Ihren CapSolver API-Key ein

# 🔑 CapSolver API Konfiguration
# 
# WICHTIG: Tragen Sie hier Ihren eigenen CapSolver API-Key ein!
# Sie erhalten diesen von: https://capsolver.com
#
# Beispiel: CAPSOLVER_API_KEY = "CAP-1234567890ABCDEF..."

CAPSOLVER_API_KEY = "CAP-0878A06C912DE97F20A9BA634C97D434"

# Anweisungen:
# 1. Registrieren Sie sich bei CapSolver.com
# 2. Erstellen Sie einen API-Key in Ihrem Dashboard
# 3. Ersetzen Sie "YOUR_CAPSOLVER_API_KEY_HERE" mit Ihrem echten Key
# 4. Speichern Sie diese Datei

if CAPSOLVER_API_KEY == "YOUR_CAPSOLVER_API_KEY_HERE":
    print("⚠️  WARNUNG: Bitte konfigurieren Sie Ihren CapSolver API-Key in capsolver_config.py")
    print("📝 Anleitung: https://capsolver.com → Dashboard → API Key erstellen")

# Alternative: Setzen Sie den API-Key als Umgebungsvariable
# export CAPSOLVER_API_KEY="ihr_api_key"
# oder in Windows:
# set CAPSOLVER_API_KEY=ihr_api_key
