from vosk import Model, KaldiRecognizer
import wave
import json

# Caminho do modelo (ajuste se estiver diferente)
model_path = "C:/Users/Victor/Desktop/Intelbras/projeto_IA_na_URA/teste2/vosk-model-small-pt-0.3"
audio_path = "audio.wav"  # troque pelo nome do seu arquivo convertido

# Carrega modelo
model = Model(model_path)

# Abre o áudio .wav
wf = wave.open(audio_path, "rb")
rec = KaldiRecognizer(model, wf.getframerate())

transcricao = ""

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        texto = json.loads(rec.Result())['text']
        transcricao += texto + " "

# Exibe resultado
print("TRANSCRIÇÃO COMPLETA:\n")
print(transcricao)
