# Automação de opções da URA

- Objetivo: Diminuir o tempo de atendimento de ligações realizadas para o setor de suporte através de uma automação envolvendo inteligência artificial
- O funcionamento inicial dos protótipos seguem a seguinte lógica:
  1. pega-se um áudio .mp3
  2. usa o modelo whisper para transcrever de áudio para texto
  3. nesse texto é verificado se há algum produto Intelbras
  4. se houver então indicamos qual é a fila de suporte correta para direcionar o cliente
- Foi criado um [relatório](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/blob/main/Viabilidade_de_Integrao_entre_Talkdesk_e_o_Projeto_IA_na_URA.pdf) sobre viabilidade de integração com a Talkdesk
 
## [Protótipo 4](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/teste3)

![image](https://github.com/user-attachments/assets/1370bd35-7747-4b94-aab9-df01bdb2209f)


- Utilização do modelo [Whisper Large](https://github.com/ggml-org/whisper.cpp) rodando offline
- Modelo pesado
- Exige uma boa capacidade de processamento
- Demora para carregar o modelo, mas até o momento é o que gera as melhores transcrições
- A demora pode ser resolvida usando um hardware mais potente
- Tive que baixar e instalar o [FFMPEG](https://www.gyan.dev/ffmpeg/builds/), usei a versão [Essentials](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z)
- Pode perceber que a transcrição não está correta, mas no arquivo .csv foi colocado possíveis transcrições já testadas que o modelo interpreta, com isso mesmo a transcrição sendo errada podemos identificar qual produto se refere


## [Protótipo 3](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/teste2)

![image](https://github.com/user-attachments/assets/33a95526-4e44-4daf-a410-0cadfcfecf18)

- Utilizado o modelo [VOSK](https://alphacephei.com/vosk/models), rodando offline
- Esse é um modelo leve, mas não tão preciso
- Pode perceber que a transcrição não está correta, mas no arquivo .csv foi colocado possíveis transcrições já testadas que o modelo interpreta, com isso mesmo a transcrição sendo errada podemos identificar qual produto se refere

## [Protótipo 2](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/teste1)

![image](https://github.com/user-attachments/assets/3ec0b49a-e536-4f44-876a-f890e2148a4b)

- Modelo de IA disponilizado pelo Facebook/Meta
- Diponível no Hugging Face
- Precisa de acesso à internet
- Pode perceber que a transcrição não está correta, mas no arquivo .csv foi colocado possíveis transcrições já testadas que o modelo interpreta, com isso mesmo a transcrição sendo errada podemos identificar qual produto se refere

## [Protótipo 1]()

### Teste 1

![image](https://github.com/user-attachments/assets/c7a9202b-0c10-462f-b44e-15421bc9ad87)


### Teste 2

![image](https://github.com/user-attachments/assets/4fcc4d35-5bd8-456e-b4c1-441d579467ef)


- Primeiro teste para abordar o problema, teve relativo sucesso, porém com algumas considerações a serem feitas;
- Está demorando para carregar o modelo e para transcrever;
- Foi utilizado recursos do site Hugging Face para encontrar um modelo de IA;
- O modelo usado é o whisper-large-v3
- Esse modelo está no conjunto dos melhores pelo que eu li, o porém está relacionado ao tempo de processamento;
- Precisamos diminuir o tempo de execução, opções:
  - Testar um hardware com GPU potente;
  - Testar outros modelos do Hugging Face;
- Fiz poucos testes, mas é possível verificar que alguns produtos não foram reconhecidos pelo modelo, o TIP 1001 D por exemplo foi transcrito como Chip 1001D, o que consequentemente faz com que ele não seja encontrado na base de registros do .CSV de teste
- Não fiz um executável
- Precisa utiilizar um ambiente virtual para rodar (venv)
- Tem um artigo da [Medium](https://medium.com/axinc-ai/whisper-large-v3-turbo-high-accuracy-and-fast-speech-recognition-model-be2f6af77bdc) falando sobre o modelo
- Precisa de acesso à rede para carregar o modelo
- Seria mais interessante usar o modelo offline
- Não precisa de chave para usar o modelo, pelo pouco que li dá para baixar sim, mas vou deixar para o próximo artefato


### Desenvolvedores

- Vitor dos Santos
- Victor Chrisosthemos
