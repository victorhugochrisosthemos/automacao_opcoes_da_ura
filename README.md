# Automação de opções da URA

- Objetivo: Diminuir o tempo de atendimento de ligações realizadas para o setor de suporte através de uma automação envolvendo inteligência artificial
- O funcionamento inicial dos protótipos seguem a seguinte lógica:
  1. pega-se um áudio .mp3
  2. usa o modelo whisper para transcrever de áudio para texto
  3. nesse texto é verificado se há algum produto Intelbras
  4. se houver então indicamos qual é a fila de suporte correta para direcionar o cliente
- Foi criado um [relatório](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/blob/main/Viabilidade_de_Integrao_entre_Talkdesk_e_o_Projeto_IA_na_URA.pdf) sobre viabilidade de integração com a Talkdesk

# Fase 2

- Realização de um sistema que integre o algoritmo gerado da fase 1 com a seleção de opções da URA de um servidor SIP
- Exemplo: quando o cliente ligar, o algoritmo identifica qual é a fila do suporte, e esse sistema da fase 2 precisa navegar em opções da URA, se for uma DISA multinível, o sistema deve enviar innformações para o servidor para chegar até seu destino através das opções

## [Protótipo 1](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/teste_vitor_servidor_sip)

<img width="784" height="522" alt="image" src="https://github.com/user-attachments/assets/a6d68f72-f99e-4db3-9866-788d9b2b9f14" />

- Informações SIP estão sendo duplicadas, ainda estamos vendo como debugar isso
- Não está funcional
- O ideial é o servidor SIP apontado pelo código seja uma UnniTI 2k ou um IAD 100 para testes
- Como rodar o código?
1. Rode o código em um virtual environment, não é obrigatório, mas ajuda se precisar rodar versões diferentes de python, por exemplo. Tem um arquivo chamado anotações.txt no diretório desse protótipo
2. Instale o Python 3.8+ e verifique com `python --version`.
3. Altere a linha `server = SIPURAServer(...)` com o IP local da máquina (`host`), IP e porta da sua PBX (`pbx_ip`, `pbx_port`) e porta RTP desejada (`rtp_port`).
4. Certifique-se de que as portas `5091` (SIP) e `13010` (RTP) estão liberadas no firewall e roteador.
5. Execute o servidor com `python sip_ura_server.py` no terminal.
6. Configure seu softphone (Ex: Linphone ou Zoiper) para registrar no IP/porta configurados no servidor.
7. Faça uma chamada para o URA usando o softphone e siga as instruções no terminal para navegar pelos menus.



# Fase 1

- Desenvolvimento de conexão do  modelo Whisper Large com dados sobre produtos Intelbras e suas filas correspondentes de suporte técnico
 
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
- Diponível no [Hugging Face](https://huggingface.co/)
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
