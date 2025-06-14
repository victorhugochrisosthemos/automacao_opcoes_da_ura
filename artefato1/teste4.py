import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from datasets import Audio
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from threading import Thread
import unicodedata
import string
import pandas as pd
import sys
import io

# Configura o stdout para UTF-8 (para log interno, não afeta UI do app)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# Variável global para armazenar tempo de carregamento do modelo
tempo_carregamento_modelo = 0

# Carrega o modelo Whisper uma vez
def load_model():
    global pipe, tempo_carregamento_modelo
    start_model = time.time()

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    end_model = time.time()
    tempo_carregamento_modelo = end_model - start_model

# Transcreve áudio em thread separada
def transcrever_audio():
    filepath = entry_path.get()
    if not filepath:
        messagebox.showerror("Erro", "Selecione um arquivo de áudio primeiro!")
        return

    btn_transcrever.config(state=tk.DISABLED, text="Transcrevendo...")
    text_output.delete('1.0', tk.END)
    text_output.insert(tk.END, "Processando... Por favor aguarde.\n")
    root.update()

    try:
        start_total = time.time()

        audio_data = Audio().decode_example(Audio().encode_example(filepath))

        start_transcricao = time.time()
        result = pipe(audio_data, generate_kwargs={"language": "pt"})
        end_transcricao = time.time()

        transcribed_text = result["text"]
        tempo_transcricao = end_transcricao - start_transcricao
        tempo_total = time.time() - start_total + tempo_carregamento_modelo

        text_output.delete('1.0', tk.END)
        text_output.insert(tk.END, "-"*30 + "\n")
        text_output.insert(tk.END, f"TEXTO TRANSCRITO:\n{transcribed_text}\n")
        text_output.insert(tk.END, f"Tempo de carregamento do modelo: {tempo_carregamento_modelo:.2f} segundos\n")
        text_output.insert(tk.END, "-"*30 + "\n")

        # MOSTRA A RESPOSTA NA INTERFACE
        text_output.insert(tk.END, f"Tempo de transcrição: {tempo_transcricao:.2f} segundos\n")
        text_output.insert(tk.END, f"Tempo total (carregamento + transcrição): {tempo_total:.2f} segundos\n")
        
        text_output.insert(tk.END, "* *"*5 + "\n")

        text_output.insert(tk.END, f"\nModelo utilizado: openai/whisper-large-v3\n")

        text_output.insert(tk.END, "* *"*5 + "\n")


        # PROCESSAMENTO DO TEXTO TRANSCRITO
        text_output.insert(tk.END, "Um registro foi encontrado desse produto? ")

        processado = limpar_texto(transcribed_text)
        produto_encontrado = []
        setor_encontrado = []
        fila_encontrado = []

        for _, linha in dados.iterrows():
            produto = str(linha['Produto'])
            produto_limpo = limpar_texto(produto)

            if produto_limpo and produto_limpo in processado:
                produto_encontrado.append(linha['Produto'])
                setor_encontrado.append(linha['Setor'])
                fila_encontrado.append(linha['filas'])

        if not produto_encontrado:
            text_output.insert(tk.END, 'NÃO\n\n')
           
        else:
            text_output.insert(tk.END, 'SIM\n\n')
            for produto, setor, fila in zip(produto_encontrado, setor_encontrado, fila_encontrado):
                text_output.insert(tk.END, f"PRODUTO = {produto}\n")
                text_output.insert(tk.END, f"SETOR = {setor}\n")
                text_output.insert(tk.END, f"FILA = {fila}\n")
                text_output.insert(tk.END, "- -"*5 + "\n")  
        
        text_output.insert(tk.END, "OBS: O áudio precisa ser em formato .mp3")


    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}")
    finally:
        btn_transcrever.config(state=tk.NORMAL, text="Transcrever Áudio")

# Seleciona arquivo
def selecionar_arquivo():
    filetypes = (("Arquivos de áudio", "*.mp3 *.wav *.ogg"), ("Todos os arquivos", "*.*"))
    filename = filedialog.askopenfilename(title="Selecione um arquivo de áudio", filetypes=filetypes)
    if filename:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, filename)

# Interface
root = tk.Tk()
root.title("Transcrição de Áudio com Whisper")
root.geometry("800x600")
root.configure(bg='black')

frame = tk.Frame(root, padx=10, pady=10, bg='black')
frame.pack(fill=tk.BOTH, expand=True)

# Label
tk.Label(frame, text="Arquivo de Áudio:", fg="#00FF00", bg='black', font=("Courier", 10, "bold")).grid(row=0, column=0, sticky='w')

# Entry
entry_path = tk.Entry(frame, width=50, bg='black', fg='#00FF00', insertbackground='#00FF00', font=("Courier", 10))
entry_path.grid(row=0, column=1, padx=5, sticky='ew')

# Botões
btn_selecionar = tk.Button(frame, text="Selecionar", command=selecionar_arquivo,
                           bg='black', fg='#00FF00', activebackground='green', font=("Courier", 10))
btn_selecionar.grid(row=0, column=2, padx=5)

btn_transcrever = tk.Button(frame, text="Transcrever Áudio",
                            command=lambda: Thread(target=transcrever_audio).start(),
                            bg='black', fg='#00FF00', activebackground='green', font=("Courier", 10))
btn_transcrever.grid(row=1, column=0, columnspan=3, pady=10)

# ScrolledText
text_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=25,
                                        bg='black', fg='#00FF00', insertbackground='#00FF00', font=("Courier", 10))
text_output.grid(row=2, column=0, columnspan=3, sticky='nsew')

frame.columnconfigure(1, weight=1)
frame.rowconfigure(2, weight=1)

# Inicia o modelo assim que a interface abrir
load_model()

root.mainloop()