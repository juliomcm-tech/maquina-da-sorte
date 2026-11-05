# Máquina da Sorte · versão autónoma

App de EuroMilhões e EuroDreams que é tua e funciona sem o Claude: chave inteligente, teste semana a semana, resultados, registo e conferência de chaves.

## O que está nesta pasta

| Ficheiro | Para quê |
|---|---|
| `index.html` | A app inteira (histórico desde 2004 já lá dentro). |
| `manifest.webmanifest`, `sw.js`, `icon-*.png` | Permitem instalar no telemóvel como app e abri-la sem rede. |
| `dados/resultados.json` | Resultados recentes com prémios e vencedores. É o robô que o mantém. |
| `scripts/atualizar.py` | O robô: lê os arquivos abertos e a página oficial dos Jogos Santa Casa. |
| `.github/workflows/atualizar.yml` | Diz ao GitHub quando correr o robô (noites de sorteio e manhã seguinte). |

## Pôr online (10 minutos, grátis)

1. No GitHub, cria um repositório novo, por exemplo `maquina-da-sorte` (como fizeste com o Mister Zé).
2. Carrega **todos** os ficheiros desta pasta, mantendo as pastas `dados`, `scripts` e `.github`.
   A pasta `.github` começa por ponto e pode estar escondida no computador. Se o upload pelo browser a saltar, cria o ficheiro à mão no GitHub com o nome `.github/workflows/atualizar.yml` e cola o conteúdo.
3. **Settings → Pages → Deploy from a branch → main → / (root) → Save.**
4. **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
5. **Actions → Atualizar resultados → Run workflow**, para o primeiro teste. Deve acabar a verde.
6. Abre `https://O-TEU-UTILIZADOR.github.io/maquina-da-sorte/` no telemóvel.
   No Chrome: menu ⋮ → **Adicionar ao ecrã principal**. Fica com ícone, como uma app.

## Como se atualiza

- O botão **Atualizar** (e a abertura da app) vai buscar:
  - `dados/resultados.json` do teu repositório, com prémios oficiais, vencedores na Europa e em Portugal;
  - os números diretamente aos arquivos abertos LottoData (MIT, fonte win2day.at) e Lottochaos (CC BY 4.0).
- O robô corre sozinho nas noites de sorteio. Não precisas de fazer nada.
- O EuroDreams pode demorar alguns dias a aparecer nos arquivos abertos. Se tiveres pressa, usa **Resultado à mão** na secção Resultados. Quando a fonte oficial chegar, corrige-o sozinha.

## As tuas chaves

- Ficam guardadas no próprio telemóvel. Cada pessoa (tu, a tua esposa) tem as suas.
- Em **Conferir chaves → Guardar cópia** fazes uma cópia de segurança (ficheiro `.json`). **Repor cópia** recupera-as noutro telemóvel ou depois de limpar o browser.

## Se o robô deixar de funcionar

Se os Jogos Santa Casa mudarem a página, o robô escreve um aviso nos registos do GitHub Actions e continua a usar os arquivos abertos. Os números continuam a chegar, só faltam os prémios em euros. A página oficial pode ser aberta em https://www.jogossantacasa.pt.

## Novidades

- **Tema Midnight**: o visual inspirado na app de música, com moldura, vidro lilás e carrossel em perspetiva.
- **Modelo Einstein** e **Laboratório**: os testes, o duelo com o modelo anterior e o "Vale a pena jogar hoje?".
- **Cartão da chave**: imagem para partilhar (WhatsApp, Instagram…) antes e depois do sorteio.
- **Ler o talão com a câmara**: em Conferir chaves. Lê as chaves e o código M1lhão; confirmas antes de registar.
- **M1lhão**: guarda o código do talão; o robô traz o código sorteado e a app confere.
- **Chaves de sempre**: ícone de repetir numa chave registada, e ela fica registada em todos os sorteios.
- **Carteira**: gasto e ganho por mês, limite mensal com aviso, e **sociedade** (ícone das duas pessoas) com a parte de cada um.
- **Avisos**: notificação no telemóvel quando há prémio (com a app aberta) e, com a app **ntfy**, aviso do resultado mesmo com a app fechada.
- **PIN**: bloqueia a app neste telemóvel (Carteira → Bloqueio com PIN).

## Só para ti

- As chaves, a carteira e o PIN ficam **só no teu telemóvel**. Quem abrir o mesmo link vê a app vazia, sem nada teu.
- A página tem `noindex` e `robots.txt`, para não aparecer no Google.
- Um site do GitHub Pages é sempre público para quem tiver o link. Não partilhes o endereço se não quiseres, e usa o PIN.

## Avisos com a app fechada (opcional)

1. Instala a app **ntfy** (Play Store, grátis).
2. Na Máquina da Sorte, em **Carteira → Avisos de resultado**, copia o teu tópico (`maquina-…`).
3. Na app ntfy, toca em **+** e subscreve esse tópico.
4. No GitHub: **Settings → Secrets and variables → Actions → New repository secret**, nome `NTFY_TOPIC` e, como valor, o tópico.

Joga com moderação: nenhuma estratégia muda a probabilidade de ganhar.

© 2026 Júlio Melo
