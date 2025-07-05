from transformers import pipeline
import sounddevice as sd
import numpy as np
import time
import keyboard
import torch
import unicodedata
import string
import pandas as pd

# Configurações
MODEL_TTS = "facebook/mms-tts-por"
MODEL_STT = "facebook/wav2vec2-large-xlsr-53-portuguese"
SAMPLE_RATE = 16000
CHANNELS = 1  # Garantir áudio mono
DURATION = 5  # Duração máxima da gravação

# Carrega a planilha de produtos
dados = pd.read_csv(
    'resultado.csv',
    sep=';',        
    encoding='latin-1'
)

              

# Inicialização dos modelos
tts = pipeline("text-to-speech", model=MODEL_TTS)
stt = pipeline("automatic-speech-recognition", model=MODEL_STT)

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

def record_audio():
    """Grava áudio quando o usuário pressionar Espaço"""
    print("\nPressione ESPAÇO para gravar (solte para parar)...")
    keyboard.wait('space')
    print("Gravando...", end='', flush=True)
    
    audio = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32') as stream:
        start_time = time.time()
        while keyboard.is_pressed('space') and (time.time() - start_time) < DURATION:
            data, _ = stream.read(int(SAMPLE_RATE * 0.1))
            audio.append(data)
    
    print(" Concluído!")
    return np.concatenate(audio) if audio else np.array([])

def prepare_audio(audio):
    """Prepara o áudio para o modelo STT"""
    if len(audio) == 0:
        return None
    # Converte para mono se necessário e garante o formato correto
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return {"array": audio, "sampling_rate": SAMPLE_RATE}

def play_audio(audio, sr=SAMPLE_RATE):
    """Reproduz áudio com tratamento de erro"""
    try:
        sd.play(audio, sr)
        sd.wait()
    except Exception as e:
        print(f"Erro ao reproduzir: {e}")

def assistente():
    print("=== Assistente por Voz ===")
    print("Comandos válidos: 'olá', 'horas', 'sair'")
    
    while True:
        try:
            audio = record_audio()
            audio_input = prepare_audio(audio)
            
            if audio_input is not None:
                texto = stt(audio_input)["text"].lower()
                print(f"Você disse: {texto}")

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


                
                if any(x in texto for x in ["olá", "ola", "oi"]):
                    resposta = "Olá! Como posso ajudar?"
                elif any(x in texto for x in ["horas", "hora", "horário"]):
                    resposta = f"São {time.strftime('%H:%M')}"
                elif "sair" in texto:
                    resposta = "Até logo! Encerrando..."
                    play_audio(tts(resposta)["audio"])
                    break
                else:
                    resposta = "Desculpe, não entendi. Diga 'horas' ou 'olá'."
                
                print(f"TRANSCRIÇÃO: {resposta}")
                play_audio(tts(resposta)["audio"])
            else:
                print("Nenhum áudio detectado. Tente novamente.")
                
        except Exception as e:
            print(f"Erro: {str(e)}")
            print("Tentando novamente...")

if __name__ == "__main__":
    try:
        import keyboard
    except ImportError:
        print("Instale o módulo 'keyboard': pip install keyboard")
        exit()
    
    try:
        assistente()
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário")