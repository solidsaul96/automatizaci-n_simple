from selenium.webdriver.common.by import By
import time
import re
import requests

def obtener_clima(driver, consulta):
    clima_api = obtener_clima_por_api(consulta)
    if clima_api:
        return clima_api
    return obtener_clima_por_scraping(driver, consulta)

def obtener_clima_por_api(consulta):
    try:
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            'name': consulta,
            'count': 1,
            'language': 'es',
            'format': 'json'
        }
        
        response = requests.get(geocoding_url, params=params, timeout=5)
        if response.status_code != 200 or not response.json().get('results'):
            return None
        
        localidad = response.json()['results'][0]
        latitude = localidad['latitude']
        longitude = localidad['longitude']
        ciudad = localidad.get('name', consulta)
        pais = localidad.get('country', '')
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
            'temperature_unit': 'celsius',
            'language': 'es'
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=5)
        if weather_response.status_code != 200:
            return None
        
        datos = weather_response.json()['current']
        temperatura = int(datos['temperature_2m'])
        humedad = datos['relative_humidity_2m']
        viento = datos['wind_speed_10m']
        codigo_clima = datos['weather_code']
        condicion = interpretar_codigo_wmo(codigo_clima)
        
        return f"Clima en {ciudad}: {temperatura}°C, {condicion}. Humedad: {humedad}%, Viento: {viento} km/h"
        
    except Exception as e:
        return None


def interpretar_codigo_wmo(code):
    codigos = {
        0: 'Despejado',
        1: 'Principalmente despejado',
        2: 'Parcialmente nublado',
        3: 'Nublado',
        45: 'Niebla',
        48: 'Niebla con escarcha',
        51: 'Llovizna ligera',
        53: 'Llovizna moderada',
        55: 'Llovizna densa',
        61: 'Lluvia débil',
        63: 'Lluvia moderada',
        65: 'Lluvia fuerte',
        71: 'Nieve débil',
        73: 'Nieve moderada',
        75: 'Nieve fuerte',
        80: 'Aguaceros débiles',
        81: 'Aguaceros moderados',
        82: 'Aguaceros fuertes',
        95: 'Tormenta',
        96: 'Tormenta con granizo',
        99: 'Tormenta con granizo fuerte',
    }
    return codigos.get(code, 'Condición desconocida')

def obtener_clima_por_scraping(driver, consulta):
    try:
        driver.get(f"https://www.google.com/search?q=clima+{consulta}")
        time.sleep(2)
        ciudad = extraer_ciudad(driver, consulta)
        temperatura = extraer_temperatura(driver)
        condicion = extraer_condicion_clima(driver)
        resultado = f"Clima en {ciudad}: {temperatura}°C, {condicion}."
        return resultado
        
    except Exception as e:
        return f"No se pudo obtener el clima para {consulta} en este momento."


def extraer_ciudad(driver, consulta):
    selectores_ciudad = [
        "div.BNeawe.tAd8D",
        "div.BNeawe.s3v9rd.AP7Wnd",
        "h2.BNeawe.tAd8D",
        "span.VfPpkd-xl07Ob-XxIAqe-OWXEXe-AHe6Kc-Y7dXd",
        "div.Z0LcW",
    ]
    
    for selector in selectores_ciudad:
        try:
            elemento = driver.find_element(By.CSS_SELECTOR, selector)
            texto = elemento.text.strip()
            if texto and any(char.isalpha() for char in texto):
                return texto.split('\n')[0]
        except:
            continue
    
    return consulta.capitalize()


def extraer_temperatura(driver):
    selectores_temperatura = [
        "span.BNeawe.tAd8D.AP7Wnd",
        "span.BNeawe.iBp5qf.AP7Wnd",
        "div.BNeawe.iBp5qf.AP7Wnd",
        "span.wtsrZe",
        "div.EZt08",
    ]
    
    for selector in selectores_temperatura:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for elemento in elementos:
                texto = elemento.text.strip()
                if re.search(r'-?\d+\s*°[CF]', texto):
                    Match = re.search(r'(-?\d+)', texto)
                    if Match:
                        return Match.group(1)
        except:
            continue
    
    return "N/A"


def extraer_condicion_clima(driver):
    selectores_condicion = [
        "span.BNeawe.tAd8D.AP7Wnd",
        "div.BNeawe.iBp5qf",
        "div.BNeawe.s3v9rd",
    ]
    
    palabras_clima = [
        'soleado', 'nublado', 'parcialmente nublado', 'lluvia', 'llovizna',
        'tormenta', 'nieve', 'niebla', 'granizo', 'viento',
        'sunny', 'cloudy', 'rainy', 'clear', 'partly', 'storm',
        'snow', 'fog', 'hail', 'windy'
    ]
    
    for selector in selectores_condicion:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for elemento in elementos:
                texto = elemento.text.lower().strip()
                for palabra in palabras_clima:
                    if palabra in texto:
                        return texto.split('\n')[0]
        except:
            continue
    
    return "Condición desconocida"


def extraer_detalles_clima(driver):
    try:
        selectores_detalles = [
            "div.BNeawe.deIvCb.AP7Wnd",
            "span.BNeawe.deIvCb.AP7Wnd",
            "div.BNeawe.s3v9rd.AP7Wnd",
        ]
        
        detalles_encontrados = []
        
        for selector in selectores_detalles:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    texto = elemento.text.strip()
                    if texto and any(keyword in texto.lower() for keyword in 
                                    ['sensación', 'humedad', 'viento', 'wind', 'humidity', 'feels']):
                        detalles_encontrados.append(texto)
            except:
                continue
        
        return ' '.join(detalles_encontrados[:2]) if detalles_encontrados else ""
        
    except:
        return ""