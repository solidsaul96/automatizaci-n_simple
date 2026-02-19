import unicodedata


def sanitizar(text):
    text = text.lower()
    text = text.replace('ñ', 'n')
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([car for car in text if not unicodedata.combining(car)])
    
    return text