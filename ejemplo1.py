import sys
import nltk
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox)
from PyQt5.QtGui import QPalette, QColor, QFont
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup

# Descargar recursos necesarios de NLTK
nltk.download('punkt')

def limpiar_texto(texto):
    tokens = nltk.word_tokenize(texto.lower())
    tokens = [token for token in tokens if token.isalpha()]
    return " ".join(tokens)

def vectorizar_textos(textos):
    vectorizador = TfidfVectorizer()
    return vectorizador.fit_transform(textos) 

def calcular_similitud(vector1, vector2):  

    return cosine_similarity(vector1, vector2)[0][0]

def detectar_plagio(texto1, texto2):
    textos = [limpiar_texto(texto1), limpiar_texto(texto2)]
    vectores = vectorizar_textos(textos)
    similitud = calcular_similitud(vectores[0], vectores[1])
    return similitud
  
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

def extraer_texto_de_url(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        return page_text
    except requests.exceptions.Timeout:
        print(f"Tiempo de espera excedido para la URL {url}")
    except Exception as e:
        print(f"Error al acceder a la URL {url}: {e}")
    return ""

class DetectorPlagioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Detector de Plagio")
        self.setGeometry(100, 100, 800, 600)

        # Widget central
        widget = QWidget(self)
        self.setCentralWidget(widget)

        # Layout principal
        layout = QVBoxLayout()

        # Estilos
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Arial;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QLabel {
                font-size: 18px;
                color: #333333;
            }
        """)

        # Etiqueta y área de texto para ingresar el texto
        label = QLabel("Ingresa el texto a verificar:")
        layout.addWidget(label)
        
        self.texto_input = QTextEdit()
        layout.addWidget(self.texto_input)

        # Botón para iniciar la búsqueda de similitud
        boton_buscar = QPushButton("Buscar Similitud")
        boton_buscar.clicked.connect(self.buscar_y_comparar)
        layout.addWidget(boton_buscar)
 
        # Área de texto para mostrar los resultados
        resultados_label = QLabel("Resultados:")
        layout.addWidget(resultados_label)
        
        self.resultados_texto = QTextEdit()
        self.resultados_texto.setReadOnly(True)
        layout.addWidget(self.resultados_texto)

        widget.setLayout(layout)

    def buscar_y_comparar(self):
        texto1 = self.texto_input.toPlainText().strip()
        if not texto1:
            QMessageBox.warning(self, "Advertencia", "Por favor, ingresa un texto para comparar.")
            return

        # Configura tu API Key y el ID del motor de búsqueda
        api_key = 'AIzaSyC9taR34o8H4ufg9gDD8faPdN1OKhEs1HA'  # Reemplaza por tu API Key
        cx = '848334ce8c0c74f06'            # Reemplaza por el ID de tu motor de búsqueda

        self.resultados_texto.clear()  # Limpiar el área de resultados
        urls = buscar_urls(texto1, api_key, cx)
        
        if urls:
            coincidencias = False
            for url in urls:
                page_text = extraer_texto_de_url(url)
                if page_text:
                    similitud = detectar_plagio(texto1, page_text)
                    if similitud > 0.5:  # Solo mostrar similitudes significativas
                        self.resultados_texto.append(f"URL: {url}\nSimilitud: {similitud * 100:.2f}%\n")
                        coincidencias = True
            if not coincidencias:
                self.resultados_texto.append("No se encontraron coincidencias significativas.\n")
        else:
            self.resultados_texto.append("No se encontraron coincidencias significativas.\n")
  
def main():
    app = QApplication(sys.argv)
    ex = DetectorPlagioApp()
    ex.show()      
    sys.exit(app.exec_())
  
if __name__ == '__main__':
    main()







