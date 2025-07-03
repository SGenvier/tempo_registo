import subprocess
import webbrowser
import time
import os
import sys

# Caminho para o ficheiro principal Streamlit
main_script = os.path.join(os.path.dirname(__file__), "main.py")

# Arranca o Streamlit em background
proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", main_script])

# Espera o servidor arrancar
time.sleep(2)
webbrowser.open("http://localhost:8501")

# Mantém o script aberto enquanto o Streamlit corre
proc.wait()