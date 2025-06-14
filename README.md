# Automação de opções da URA

- Objetivo: Diminuir o tempo de atendimento de ligações realizadas para o setor de suporte através de uma automação envolvendo inteligência artificial

### [Artefato 1](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/artefato1)

![image](https://github.com/user-attachments/assets/c7a9202b-0c10-462f-b44e-15421bc9ad87)

- Primeiro teste para abordar o problema, teve relativo sucesso, porém com algumas considearções a serem feitas;
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
