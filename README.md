# Automação de opções da URA

- Objetivo: Diminuir o tempo de atendimento de ligações realizadas para o setor de suporte através de uma automação envolvendo inteligência artificial

### [Artefato 1](https://github.com/victorhugochrisosthemos/automacao_opcoes_da_ura/tree/main/artefato1)

![image](https://github.com/user-attachments/assets/2d2d8af4-f1b7-408b-968d-96cb1291e42a)

- Primeiro teste para abordar o problema, teve relativo sucesso, porém com algumas considearções a serem feitas;
- Está demorando para carregar o modelo e para transcrever;
- Foi utilizado recursos do site Hugging Face para encontrar um modelo de IA;
- O modelo usado é o whisper-large-v3
- Esse modelo está no conjunto dos melhores pelo que eu li, o porém está relacionado ao tempo de processamento;
- Precisamos diminuir o tempo de execução, opções:
  - Testar um hardware com GPU potente;
  - Testar outros modelos do Hugging Face;
- Fiz poucos testes, mas é possível verificar que alguns produtos não foram reconhecidos pelo modelo, o TIP 1001 D por exemplo foi transcrito como Chip 1001D, o que consequentemente faz com que ele não seja encontrado na base de registros do .CSV de teste
