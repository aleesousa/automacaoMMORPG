# Bot-ED-JUGG

Automacao experimental para partidas Juggernaut no jogo Epic Duel.

## Recursos

- interface com estado da execucao e contador de partidas;
- somente um processo do bot por vez;
- parada segura pelo botao ou pela tecla F10 (com a janela em foco);
- PyAutoGUI Fail-Safe ativo: mova o mouse rapidamente para o canto superior esquerdo;
- busca de imagens com timeout, sem clicar quando a imagem nao for encontrada;
- log de execucao salvo em `bot.log`;
- interrupcao automatica depois de cinco erros consecutivos.

## Requisitos

- Python 3.9 ou superior;
- imagens de referencia dentro da pasta `skils/`;
- resolucao e escala de tela compativeis com as imagens capturadas.

Instale as dependencias dentro da pasta do projeto:

```bash
python3 -m pip install -r requirements.txt
```

## Estrutura esperada

```text
automacaoMMORPG/
├── app.py
├── requirements.txt
└── skils/
    ├── jugg.png
    ├── skil1.png ... skil7.png
    ├── continuar.png ... continuar3.png
    └── x3.png ... x21.png e x23.png
```

O programa valida esses arquivos antes de iniciar e mostra quais estao ausentes.

## Executar

No Windows (PowerShell), prepare o ambiente na primeira vez:

```powershell
cd C:\Estudos\automacaoMMORPG
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para abrir o programa, use o Python do ambiente virtual (nao precisa ativa-lo):

```powershell
cd C:\Estudos\automacaoMMORPG
.\.venv\Scripts\python.exe app.py
```

Em outros sistemas:

```bash
python3 app.py
```

1. Deixe o jogo visivel e sem outras janelas sobre ele.
2. Clique em **Start Bot**.
3. Use **Stop Bot** ou F10 para interromper.
4. Em uma emergencia, use o Fail-Safe levando o mouse ao canto superior esquerdo.

[Video de demonstracao](https://drive.google.com/file/d/1aqwQMQZmeMtbGB2NV3OQU2RgHl3zSS6q/view?usp=sharing)

## Ajustes

Os valores `CONFIDENCE`, `INTERVALO_BUSCA` e `INTERVALO_ENTRE_CICLOS`, no inicio de
`app.py`, controlam a tolerancia visual e a velocidade. Reduzir demais os intervalos
pode aumentar falsos cliques e consumo de CPU.

Automacoes podem contrariar os termos do jogo e causar penalidades na conta. Use
somente onde isso for permitido e nao tente contornar mecanismos anti-cheat.
