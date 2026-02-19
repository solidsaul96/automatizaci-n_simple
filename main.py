import sys
import os
import logging
import re
import io

os.environ['CHROME_LOG_FILE'] = os.devnull
os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

class SilentError(io.StringIO):
    def write(self, x):
        pass
    def flush(self):
        pass

_old_stderr = sys.stderr
sys.stderr = SilentError()

logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('webdriver_manager').setLevel(logging.CRITICAL)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from funciones_agentes.obtener_clima import obtener_clima
from funciones_agentes.obtener_precio_accion import obtener_precio_accion
from utils.sanitizar import sanitizar

PALABRAS_SALIR = ['salir', 'exit', 'quit', 'bye', 'adiós', 'adios', 'chao', 'hasta luego', 'hasta']

PALABRAS_IGNORAR = ['dame', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'me', 'mira', 'dime', 'cuál', 'cual', 'cómo', 'como', 'en', 'a', 'por', 'para', 'del', 'de', 'es', 'está']

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--log-level=3")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins")
options.add_argument("--disable-sync")
options.add_argument("--disable-notifications")
options.add_argument("--disable-default-apps")
options.add_argument("--mute-audio")
options.add_argument("--disable-logging")
options.add_argument("--no-default-browser-check")
options.add_argument("--no-first-run")
options.add_argument("--disable-component-extensions-with-background-pages")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-breakpad")
options.add_argument("--disable-client-side-phishing-detection")
options.add_argument("--disable-hang-monitor")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-prompt-on-repost")
options.add_argument("--disable-preconnect")
options.add_argument("--disable-features=TranslateUI")
options.add_argument("--disable-features=Translate")
options.add_argument("--disable-features=IsolateOrigins")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-suggestions-ui")
options.add_argument("--disable-bookmark-ui")
options.add_argument("--disable-gcm-channel-status-api")
options.add_argument("--disable-site-isolation-trials")
options.add_argument("--metrics-recording-only")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

try:
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
except Exception as e:
    sys.stderr = _old_stderr
    print(f"Error al inicializar Chrome: {e}")
    sys.exit(1)

sys.stderr = _old_stderr

def extraer_ubicacion(user_input):
    texto = user_input.lower()
    palabras_clima = ['clima', 'temperatura', 'weather', 'lluvia', 'nieve', 'viento', 'nublado', 'soleado']
    for palabra in palabras_clima:
        texto = texto.replace(palabra, '')
    for palabra in PALABRAS_IGNORAR:
        texto = re.sub(r'\b' + palabra + r'\b', '', texto)
    texto = ' '.join(texto.split())
    return texto.strip() if texto.strip() else user_input

def debe_salir(user_input):
    texto_limpio = user_input.lower().strip()
    for palabra in PALABRAS_SALIR:
        if palabra in texto_limpio:
            return True
    return False

def procesar_input(user_input):
    if "clima" in user_input or "temperatura" in user_input:
        return obtener_clima
    elif "precio" in user_input or "accion" in user_input or "valor" in user_input:
        return obtener_precio_accion
    return None

print("Hola, soy tu asistente virtual. ¿En qué puedo ayudarte hoy?")
print("(Escribe 'salir', 'exit' o 'quit' para terminar)\n")

try:
    while True:
        user_input = sanitizar(input("---> "))
        if debe_salir(user_input):
            print("¡Hasta luego! Gracias por usar el asistente virtual.")
            break
        funcion_agente = procesar_input(user_input)
        if funcion_agente is None:
            print("No entendí tu solicitud. Intenta nuevamente.")
        else:
            consulta = extraer_ubicacion(user_input)
            respuesta = funcion_agente(driver, consulta)
            print(f">>> {respuesta}")

except KeyboardInterrupt:
    print("\n\n¡Programa interrumpido por el usuario!")
    
finally:
    if driver is not None:
        try:
            driver.quit()
            print("✓ Navegador cerrado correctamente.")
        except Exception as e:
            try:
                driver.close()
                print("✓ Navegador cerrado (modo alternativo).")
            except:
                print("✗ Error al cerrar el navegador (Se cerrará automáticamente).")