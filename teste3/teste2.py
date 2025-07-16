import whisper
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import tempfile
import time
import keyboard
import unicodedata
import string
import pandas as pd


'''
import os 


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "resultado.csv")
 
dados = pd.read_csv(
    csv_path,
    sep=';',        
    encoding='latin-1'
)


'''



# Carrega a planilha de produtos
dados = pd.read_csv(
    'resultado.csv',
    sep=';',        
    encoding='latin-1'
)

# Função para limpar e normalizar textos
def limpar_texto(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = text.replace(" ", "")
    text = text.replace("\n", "")
    return text

# Medir o tempo de carregamento do modelo
print("Carregando modelo Whisper 'large'...")
start_model_time = time.time()
model = whisper.load_model("large")
end_model_time = time.time()
load_duration = end_model_time - start_model_time
print(f"Modelo carregado em {load_duration:.2f} segundos.\n")

# Configuração da gravação
sample_rate = 16000

print("Mantenha a tecla ESPAÇO pressionada para gravar. Quando soltar, o áudio será transcrito.\n(Ctrl+C para sair)\n")

try:
    while True:
        print("Aguardando pressionar a tecla espaço...")

        # Espera o pressionamento da tecla
        keyboard.wait("space")
        print("Gravando... (mantenha pressionado)")

        frames = []

        # Enquanto a tecla espaço estiver pressionada, capture áudio
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
            while keyboard.is_pressed("space"):
                data, _ = stream.read(1024)
                frames.append(data)

        print("Tecla solta! Parando gravação e transcrevendo...")

        # Concatena todos os frames em um array numpy
        audio_data = np.concatenate(frames, axis=0)

        # Salva o áudio temporariamente
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wav.write(temp_audio.name, sample_rate, audio_data)
            audio_path = temp_audio.name

        # Transcreve com Whisper
        start_time = time.time()
        result = model.transcribe(audio_path, language='pt')
        duration_proc = time.time() - start_time

        texto = result["text"]

        print("\nTRANSCRIÇÃO:")
        print(texto)
        print(f"Tempo de processamento: {duration_proc:.2f} segundos\n")

        # PROCESSAMENTO DO TEXTO TRANSCRITO
        print("Um registro foi encontrado desse produto? ")

        processado = limpar_texto(texto)
        produto_encontrado = []
        setor_encontrado = []
        fila_encontrado = []
        produto_match = []

        for _, linha in dados.iterrows():
            # produto_falado pode ter vários produtos separados por vírgula
            produtos_falados = str(linha['produto_falado']).split(',')
            produtos_falados = [limpar_texto(p) for p in produtos_falados]

            for produto_limpo in produtos_falados:
                if produto_limpo and produto_limpo in processado:
                    produto_encontrado.append(linha['Produto'])
                    produto_match.append(produto_limpo)
                    setor_encontrado.append(linha['Setor'])
                    fila_encontrado.append(linha['filas'])
                    break  # encontrou um produto válido dessa linha, pode ir pra próxima linha

        if not produto_encontrado:
            print('NÃO\n\n')
        else:
            print('SIM\n\n')
            for produto, produto_falado, setor, fila in zip(produto_encontrado, produto_match, setor_encontrado, fila_encontrado):
                print(f"FALA DO CLIENTE = {produto_falado}\n")
                print(f"PRODUTO = {produto}\n")
                print(f"SETOR = {setor}\n")
                print(f"FILA = {fila}\n")
                print("- -"*5 + "\n")


except KeyboardInterrupt:
    print("\nEncerrado pelo usuário.")
except Exception as e:
    print(f"Erro: {e}")
