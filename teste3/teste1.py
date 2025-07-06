import whisper

# Carrega o modelo 'large' (será baixado na primeira vez e salvo no cache local)
print("Carregando modelo Whisper 'large'...")
model = whisper.load_model("large")

# Caminho do seu áudio (pode ser .wav, .mp3, etc.)
audio_path = "audio1.mp3"  # <- troque se necessário

# Transcreve o áudio
print("Transcrevendo...")
result = model.transcribe(audio_path, language='pt')

# Exibe o resultado
print("\nTRANSCRIÇÃO COMPLETA:\n")
print(result["text"])


# C:/Users/Victor/Desktop/Intelbras/projeto_IA_na_URA/teste3/ffmpeg-2025-07-01-git-11d1b71c31-essentials_build/bin