# 🚀 Laboratório de Aprendizado OpenTelemetry + Python

Bem-vindo ao seu ambiente de testes de observabilidade! Este projeto foi projetado para ensinar a você, de forma prática e interativa, o funcionamento do **OpenTelemetry (OTel)**, integrando rastreamento (Traces), métricas (Metrics) e registros (Logs).

---

## 🧭 O que estamos rodando?

Nossa infraestrutura local é composta por:

1. **Sua Aplicação FastAPI**: Roda localmente na sua máquina (porta `8000`). Ela envia dados de observabilidade usando o padrão OTel.
2. **OpenTelemetry Collector**: Atua como um receptor central (recebe os dados da sua aplicação via OTLP na porta `4317` e distribui para os locais certos).
3. **Jaeger**: Backend de visualização de traces distribuídos (porta `16686`).
4. **Prometheus**: Banco de dados temporal para guardar e consultar métricas (porta `9090`).

```
                    ┌──────────────────────────┐
                    │  App Python (FastAPI)    │
                    │  Port 8000               │
                    └────────────┬─────────────┘
                                 │ (OTLP / gRPC)
                                 ▼
                    ┌──────────────────────────┐
                    │  OTel Collector          │
                    │  Ports 4317 / 4318       │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ (Traces)                      │ (Metrics)
                 ▼                               ▼
      ┌─────────────────────┐         ┌─────────────────────┐
      │ Jaeger UI           │         │ Prometheus UI       │
      │ Port 16686          │         │ Port 9090           │
      └─────────────────────┘         └─────────────────────┘
```

---

## 🛠️ Como Iniciar o Ambiente

Siga as instruções passo a passo no terminal:

### Passo 1: Subir os serviços de infraestrutura (Docker Compose)
Abra seu terminal na pasta deste projeto (`opentelemetry-learning`) e digite:
```bash
docker compose up -d
```
*Isso vai baixar e inicializar o Jaeger, Prometheus e o OTel Collector em segundo plano.*

### Passo 2: Criar e ativar o ambiente virtual Python
No mesmo diretório, execute:

**No macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar as dependências
Com o ambiente virtual ativo, instale os pacotes:
```bash
pip install -r requirements.txt
```

### Passo 4: Rodar o aplicativo FastAPI
Execute o servidor de desenvolvimento:
```bash
uvicorn app.main:app --reload
```
*O servidor estará acessível em: `http://localhost:8000`*

---

## 🎯 Exercícios Práticos: Aprendendo na Prática

Com tudo rodando, vamos fazer 5 atividades para entender a observabilidade em profundidade.

---

### 🟢 Exercício 1: Gerando Telemetria e Verificando Conectividade

Abra o navegador ou use o `curl` no terminal para gerar acessos no app:

1. Acesse a rota raiz algumas vezes:
   ```bash
   curl http://localhost:8000/
   ```
2. Acesse a rota de jogar dados algumas vezes, alterando os parâmetros:
   ```bash
   curl "http://localhost:8000/rolldice?player=Maria"
   curl "http://localhost:8000/rolldice?player=Joao"
   curl "http://localhost:8000/rolldice"
   ```

---

### 🟢 Exercício 2: Caçando Traces no Jaeger

Os **Traces** ajudam a visualizar o caminho completo que uma requisição percorre e quanto tempo ela demora em cada etapa.

1. Abra o painel do Jaeger no seu navegador: **[http://localhost:16686](http://localhost:16686)**
2. No menu à esquerda, em **Service**, selecione `learn-otlp-python`.
3. Clique em **Find Traces**.
4. Selecione uma das requisições para `/rolldice`.
5. **Observe:**
   * O Span pai (`GET /rolldice`) foi criado automaticamente pela auto-instrumentação do FastAPI.
   * O Span filho (`roll_dice_operation`) foi criado manualmente por nós no código.
   * Clique em `roll_dice_operation`. Na aba **Tags**, veja os atributos customizados que injetamos: `roll.value`, `roll.player`, `roll.is_lucky`.
   * Veja os **Logs** (Events) associados ao Span, marcando exatamente o segundo em que a rolagem começou e terminou.

---

### 🟢 Exercício 3: Explorando Métricas no Prometheus

**Métricas** são dados agregados numéricos ótimos para monitorar a saúde global e a volumetria do sistema em tempo real.

1. Acesse o painel do Prometheus: **[http://localhost:9090](http://localhost:9090)**
2. Na barra de pesquisa de consultas, digite a métrica:
   ```promql
   otel_dice_rolls_total
   ```
3. Clique em **Execute** e mude para a aba **Graph**.
   * Você verá o total de jogadas registradas.
   * Note as *labels* (tags de métricas): você consegue ver quantas vezes `Maria` jogou versus `Joao`, ou quantos resultados foram de "sorte" (`lucky="True"`).
4. Agora digite:
   ```promql
   otel_dice_roll_value_distribution_bucket
   ```
   * Isso exibe os baldes (buckets) de distribuição do histograma, revelando como os valores rolados estão distribuídos de 1 a 6.

---

### 🟢 Exercício 4: Investigando Erros no Jaeger

Uma das maiores utilidades dos traces é debugar incidentes rapidamente.

1. Chame a rota de simulação de workflow várias vezes no terminal até ela dar erro:
   ```bash
   curl http://localhost:8000/sim-workflow
   ```
   *Esta rota tem 30% de chance de falhar simulando uma chamada de API externa expirada.*
2. Quando receber a resposta de erro `503 Service Unavailable`, volte ao Jaeger (**[http://localhost:16686](http://localhost:16686)**).
3. Busque por traces da operação `/sim-workflow`.
4. Procure o trace que está marcado com um ícone de **erro vermelho**.
5. Abra esse trace e expanda o Span `external_api_call`:
   * Veja o status do span alterado para `Error`.
   * Sob os eventos, você verá a stack trace do erro python (`ValueError`), revelando a linha exata onde ocorreu a falha!

---

### 🟢 Exercício 5: Correlação de Logs com Traces

Uma das práticas mais eficientes em observabilidade é poder ler um log do console e achar o trace correspondente instantaneamente.

1. Olhe para a janela do terminal onde o `uvicorn` está rodando.
2. Note o formato das mensagens de log impressas:
   ```text
   [2026-06-06 18:42:00,123] INFO [otlp-app] [TraceID: 3a9254... SpanID: 4d28e...] - Dado rolado. Resultado: 5 (Sorte: True)
   ```
3. Copie o `TraceID` gerado na linha do log.
4. Vá para o Jaeger, cole esse ID no campo de busca localizado no canto superior direito e aperte Enter.
5. O Jaeger trará **exatamente** o trace que gerou aquela linha de log. Isso poupa horas de depuração em produção!

---

## 💡 Exercício Extra (Para criar suas próprias coisas!)
Abra o arquivo [app/main.py](file:///Users/mdetrano/Downloads/opentelemetry-learning/app/main.py). 
Tente:
1. Criar uma nova rota (`/minha-rota`).
2. Criar uma métrica do tipo Counter para contar acessos a essa nova rota.
3. Adicionar um Span manual com um atributo customizado.
4. Chamar a rota e conferir os novos resultados no Jaeger e Prometheus!
