import sounddevice as sd
import queue
import sys
import json
import time
from vosk import Model, KaldiRecognizer
import unicodedata
import string
import pandas as pd

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

# ⏳ Medição do tempo de carregamento do modelo Vosk
print("Carregando modelo Vosk...")
inicio_modelo = time.time()
model_path = "C:/Users/Victor/Desktop/Intelbras/projeto_IA_na_URA/teste2/vosk-model-small-pt-0.3"
model = Model(model_path)
fim_modelo = time.time()
print(f"Modelo carregado em {fim_modelo - inicio_modelo:.2f} segundos.\n")

# Configurações de áudio
sample_rate = 16000
block_size = 4000
q = queue.Queue()

# Callback de captura de áudio
def callback(indata, frames, time_data, status):
    if status:
        print(f"Erro de status: {status}", file=sys.stderr)
    q.put(indata.tobytes())

# Inicializa o reconhecedor
rec = KaldiRecognizer(model, sample_rate)

print("Pressione SPACE e fale algo, ao soltar a tecla irá mostrar a transcrição (Ctrl+C para sair)\n")

try:
    with sd.InputStream(samplerate=sample_rate, blocksize=block_size,
                        dtype='int16', channels=1, callback=callback):
        while True:
            
            data = q.get()

            # Início da medição do tempo
            inicio = time.time()

            if rec.AcceptWaveform(data):
                resultado = json.loads(rec.Result())
                texto = resultado.get("text", "").strip()

                fim = time.time()
                duracao = fim - inicio  # tempo em segundos

                if texto:
                    print(f"\nTEXTO RECONHECIDO: {texto}")
                    print(f"Tempo de processamento: {duracao:.3f} segundos\n")
                    print("Pressione SPACE e fale algo, ao soltar a tecla irá mostrar a transcrição (Ctrl+C para sair)\n")

                    # PROCESSAMENTO DO TEXTO TRANSCRITO
                    print("Um registro foi encontrado desse produto? ")

                    processado = limpar_texto(texto)
                    produto_encontrado = []
                    setor_encontrado = []
                    fila_encontrado = []
                    produto_match = []

                    for _, linha in dados.iterrows():
                        produtos_falados = str(linha['produto_falado']).split(',')
                        produtos_falados = [limpar_texto(p) for p in produtos_falados]

                        for produto_limpo in produtos_falados:
                            if produto_limpo and produto_limpo in processado:
                                produto_encontrado.append(linha['Produto'])
                                produto_match.append(produto_limpo)
                                setor_encontrado.append(linha['Setor'])
                                fila_encontrado.append(linha['filas'])
                                break

                    if not produto_encontrado:
                        print('NÃO\n')
                    else:
                        print('SIM\n')
                        for produto, produto_falado, setor, fila in zip(produto_encontrado, produto_match, setor_encontrado, fila_encontrado):
                            print(f"FALA DO CLIENTE = {produto_falado}\n")
                            print(f"PRODUTO = {produto}\n")
                            print(f"SETOR = {setor}\n")
                            print(f"FILA = {fila}\n")
                            print("- -" * 5 + "\n")
                    print("Pressione SPACE e fale algo, ao soltar a tecla irá mostrar a transcrição (Ctrl+C para sair)\n")

                

except KeyboardInterrupt:
    print("\nEncerrado pelo usuário")
except Exception as e:
    print(f"Erro: {str(e)}")
