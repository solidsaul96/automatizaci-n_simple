from selenium.webdriver.common.by import By
import time
import re
import requests

TICKERS_CONOCIDOS = {
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
    'amazon': 'AMZN',
    'tesla': 'TSLA',
    'facebook': 'META',
    'meta': 'META',
    'nvidia': 'NVDA',
    'amd': 'AMD',
    'intel': 'INTC',
    'cisco': 'CSCO',
    'ibm': 'IBM',
    'netflix': 'NFLX',
    'disney': 'DIS',
    'coca cola': 'KO',
    'pepsi': 'PEP',
    'mcdonalds': 'MCD',
    'banorte': 'GBNORTE.MX',
    'femsa': 'FEMSA.MX',
}

def obtener_precio_accion(driver, consulta):
    ticker = obtener_ticker(consulta)
    
    if not ticker:
        return f"No se pudo identificar el ticker para '{consulta}'."
    precio_info = obtener_precio_por_api(ticker)
    if precio_info:
        return precio_info
    return obtener_precio_por_scraping(driver, ticker, consulta)

def obtener_ticker(consulta):
    consulta_lower = consulta.lower().strip()
    for empresa, ticker in TICKERS_CONOCIDOS.items():
        if empresa in consulta_lower:
            return ticker
    if len(consulta_lower) <= 5 and consulta_lower.isalpha():
        return consulta_lower.upper()
    return None

def obtener_precio_por_api(ticker):
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': 'demo'
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return None
        
        datos = response.json()
        if 'Global Quote' not in datos or not datos['Global Quote'].get('05. price'):
            return None
        
        quote = datos['Global Quote']
        precio = float(quote['05. price'])
        cambio = float(quote.get('09. change', 0))
        
        if precio <= 0:
            return None
        
        empresa = quote.get('01. symbol', ticker)
        cambio_pct = f"({cambio:+.2f})" if cambio != 0 else ""
        
        return f"{empresa} [{ticker}] ${precio:.2f} USD. {cambio_pct}"
        
    except Exception as e:
        return None


def obtener_precio_por_scraping(driver, ticker, empresa):
    try:
        driver.get(f"https://www.google.com/search?q={ticker}+stock+price")
        time.sleep(2)
        selectores_precio = [
            "span[jsname='vWLAgc']",
            "span.fl",
            "div.BNeawe.iBp5qf.AP7Wnd",
            "span.Trsw0d",
            "div.RivaKc",
        ]
        precio_encontrado = None
        for selector in selectores_precio:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text.strip()
                if texto and any(char.isdigit() for char in texto):
                    numeros = re.findall(r'[\d.]+', texto)
                    if numeros:
                        precio_encontrado = numeros[0]
                        break
            except:
                continue
        
        if precio_encontrado:
            return f"{empresa} [{ticker}] ${precio_encontrado} USD."
        else:
            return f"{empresa} [{ticker}]: Precio no disponible en este momento."
        
    except Exception as e:
        return f"{empresa} [{ticker}]: No se pudo obtener el precio."
