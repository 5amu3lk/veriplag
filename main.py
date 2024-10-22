from flask import Flask, render_template, request, redirect
import nltk
from spellchecker import SpellChecker  # Importar pyspellchecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import docx
import matplotlib.pyplot as plt
import io
import base64

# Descargar recursos necesarios de NLTK
nltk.download('punkt')

app = Flask(__name__)

# Inicializar el corrector ortográfico
spell = SpellChecker(language='es')  # Usar el diccionario en español

# Función para limpiar el texto
def limpiar_texto(texto):
    tokens = nltk.word_tokenize(texto.lower())
    tokens = [token for token in tokens if token.isalpha()]
    return " ".join(tokens)

# Función para corregir ortografía usando pyspellchecker
from nltk.tokenize import sent_tokenize

def corregir_ortografia_parrafo(texto):
    # Tokenizar el texto
    palabras = nltk.word_tokenize(texto.lower())
    
    # Corregir palabras mal escritas
    palabras_corregidas = []
    for palabra in palabras:
        # Verificar si la palabra está en el diccionario y si no, corregirla
        if palabra not in spell:
            correccion = spell.correction(palabra)
            if correccion:  # Si encuentra una corrección
                palabras_corregidas.append(correccion)
            else:
                palabras_corregidas.append(palabra)  # Si no hay corrección, dejar la palabra como está
        else:
            palabras_corregidas.append(palabra)  # Si la palabra es correcta, mantenerla

    # Unir las palabras corregidas de nuevo en un texto
    texto_corregido = " ".join(palabras_corregidas)
    return texto_corregido


# Función para vectorizar textos
def vectorizar_textos(textos):
    vectorizador = TfidfVectorizer()
    return vectorizador.fit_transform(textos)

# Función para calcular similitud
def calcular_similitud(vector1, vector2):  
    return cosine_similarity(vector1, vector2)[0][0]

# Función para detectar plagio
def detectar_plagio(texto1, texto2):
    textos = [limpiar_texto(texto1), limpiar_texto(texto2)]
    vectores = vectorizar_textos(textos)
    similitud = calcular_similitud(vectores[0], vectores[1])
    return similitud

# Función para extraer texto de URLs
def buscar_urls(texto, api_key, cx, num_results=10):
    texto_codificado = requests.utils.quote(texto)
    url = f"https://www.googleapis.com/customsearch/v1?q={texto_codificado}&key={api_key}&cx={cx}&num={num_results}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        results = response_json.get('items', [])
        return [result['link'] for result in results]
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la búsqueda: {e}")
        return []

# Función para extraer texto de una URL
def extraer_texto_de_url(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        return page_text
    except Exception as e:
        print(f"Error al acceder a la URL {url}: {e}")
    return ""

# Función para extraer texto de archivos subidos (PDF o DOCX)
def extraer_texto_archivo(archivo):
    extension = os.path.splitext(archivo.filename)[1].lower()
    texto_extraido = ""

    if extension == '.pdf':
        lector_pdf = PyPDF2.PdfReader(archivo)
        for pagina in range(len(lector_pdf.pages)):
            texto_extraido += lector_pdf.pages[pagina].extract_text()
    elif extension == '.docx':
        documento = docx.Document(archivo)
        for parrafo in documento.paragraphs:
            texto_extraido += parrafo.text
    else:
        raise ValueError("Formato de archivo no soportado")

    return texto_extraido

# Función para crear la gráfica
def crear_grafica(resultados, porcentaje_total):
    urls = [resultado['url'] for resultado in resultados]
    similitudes = [resultado['similitud'] for resultado in resultados]

    plt.figure(figsize=(10, 5))
    plt.barh(urls, similitudes, color='skyblue')
    plt.axvline(x=porcentaje_total, color='red', label=f'Promedio: {porcentaje_total:.2f}%')
    plt.title('Resultados de Plagio')
    plt.xlabel('Porcentaje de Similitud')
    plt.ylabel('URLs')
    plt.legend()
    plt.tight_layout()

    # Guardar la gráfica en un objeto BytesIO y codificar en base64
    imagen = io.BytesIO()
    plt.savefig(imagen, format='png')
    imagen.seek(0)
    grafic_base64 = base64.b64encode(imagen.getvalue()).decode('utf8')
    plt.close()  # Cerrar la figura para liberar memoria
    return grafic_base64

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para corrección ortográfica
@app.route('/correcion', methods=['GET', 'POST'])
def correccion_ortografica():
    if request.method == 'POST':
        texto = request.form['textoIA']
        if not texto:
            return redirect('/correcion')

        texto_correcto = corregir_ortografia_parrafo(texto)  
        return render_template('correcion.html', texto_original=texto, texto_correcto=texto_correcto)
    
    return render_template('correcion.html')

# Ruta para buscar plagio
@app.route('/buscar', methods=['POST'])
def buscar():
    texto1 = request.form['texto1']

    # Configura tu API Key y el ID del motor de búsqueda
    api_key = 'AIzaSyC9taR34o8H4ufg9gDD8faPdN1OKhEs1HA'  # Reemplaza por tu API Key
    cx = '848334ce8c0c74f06'  # Reemplaza por el ID de tu motor de búsqueda

    urls = buscar_urls(texto1, api_key, cx)
    resultados = []
    total_similitud = 0  
    cantidad_resultados = len(urls)  

    for url in urls:
        texto_url = extraer_texto_de_url(url)
        similitud = detectar_plagio(texto1, texto_url)
        if similitud > 0:  
            resultados.append({'url': url, 'similitud': round(similitud * 100, 2)})  
            total_similitud += similitud * 100  

    # Calcular el porcentaje general de plagio
    if cantidad_resultados > 0:
        porcentaje_total = total_similitud / cantidad_resultados
    else:
        porcentaje_total = 0

    # Crear la gráfica
    grafic_base64 = crear_grafica(resultados, porcentaje_total)

    return render_template('resultados.html', resultados=resultados, porcentaje_total=round(porcentaje_total, 2), grafic_base64=grafic_base64)

# Ruta para subir un archivo y detectar plagio
@app.route('/subir_archivo', methods=['POST'])
def subir_archivo():
    if 'archivo' not in request.files:
        return redirect('/')

    archivo = request.files['archivo']
    if archivo.filename == '':
        return redirect('/')

    texto_documento = extraer_texto_archivo(archivo)

    # Texto de referencia para comparación
    texto_referencia = "Texto de referencia para comparación."

    # Calcular similitud de plagio
    similitud = detectar_plagio(texto_documento, texto_referencia)
    similitud_porcentaje = round(similitud * 100, 2)

    # Mostrar los resultados
    return render_template('resultadodos.html', 
                           resultados=[{'url': 'Documento subido', 'similitud': similitud_porcentaje}])

if __name__ == '__main__':
    app.run(debug=True) 