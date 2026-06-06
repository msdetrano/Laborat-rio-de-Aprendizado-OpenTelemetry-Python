import random
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import StatusCode

# ==========================================
# 1. CONFIGURAÇÃO DO LOGGER COM CORRELAÇÃO DE TRACE
# ==========================================
# Filtro para injetar o Trace ID e Span ID atuais nos logs do Python.
class OTelLoggingFilter(logging.Filter):
    def filter(self, record):
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            context = current_span.get_span_context()
            # Formata os IDs como strings hexadecimais padrão
            record.trace_id = format(context.trace_id, "032x")
            record.span_id = format(context.span_id, "016x")
        else:
            record.trace_id = "00000000000000000000000000000000"
            record.span_id = "0000000000000000"
        return True

# Configurando o logger principal da aplicação
logger = logging.getLogger("otlp-app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.addFilter(OTelLoggingFilter())
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s] [TraceID: %(trace_id)s SpanID: %(span_id)s] - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ==========================================
# 2. INICIALIZAÇÃO DO OPENTELEMETRY (SDKs)
# ==========================================
# Definimos um Recurso (Resource) que descreve o nosso serviço.
resource = Resource.create(attributes={
    "service.name": "learn-otlp-python",
    "service.version": "1.0.0",
    "environment": "development"
})

# --- TRACING SETUP ---
# Provedor de Tracing que orquestra a geração de spans
tracer_provider = TracerProvider(resource=resource)
# Configura o exportador OTLP via gRPC enviando para o coletor (localhost:4317)
otlp_span_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
# Adiciona o processador de spans em lote (BatchSpanProcessor) ao provedor
span_processor = BatchSpanProcessor(otlp_span_exporter)
tracer_provider.add_span_processor(span_processor)
# Define o tracer global
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("learn-otlp-python-tracer")

# --- METRICS SETUP ---
# Configura o exportador OTLP de métricas via gRPC enviando para o coletor
otlp_metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
# Configura o leitor que puxa as métricas de tempos em tempos (a cada 5s para fins de teste)
metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)
# Provedor de Métricas
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
# Define o meter global
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("learn-otlp-python-meter")

# ==========================================
# 3. CRIAÇÃO DE MÉTRICAS CUSTOMIZADAS (INSTRUMENTOS)
# ==========================================
# Um Counter serve para contar ocorrências (ex: requisições, erros, cliques)
dice_roll_counter = meter.create_counter(
    name="dice_rolls_total",
    description="Contagem total de lançamentos de dado",
    unit="1"
)

# Um Histogram serve para analisar distribuição de valores (ex: latência, tamanho de arquivos)
dice_roll_histogram = meter.create_histogram(
    name="dice_roll_value_distribution",
    description="Distribuição dos valores resultantes dos dados",
    unit="1"
)

# ==========================================
# 4. CRIAÇÃO DA APLICAÇÃO FASTAPI
# ==========================================
app = FastAPI(
    title="OpenTelemetry Learning App",
    description="API experimental para aprender conceitos práticos de observabilidade."
)

# Rota principal
@app.get("/")
def read_root():
    logger.info("Rota principal / acessada.")
    return {"message": "Bem-vindo ao laboratório de OpenTelemetry! Acesse /docs para ver os endpoints."}

# Rota /rolldice demonstrando Traces Manuais, Atributos, Eventos e Métricas
@app.get("/rolldice")
def roll_dice(player: Optional[str] = "Anonimo"):
    logger.info(f"O jogador {player} iniciou uma jogada de dados.")
    
    # Criamos um Span manual para monitorar esta operação específica
    with tracer.start_as_current_span("roll_dice_operation") as span:
        # Adiciona um Evento (um log estruturado com carimbo de data/hora anexado a este Span)
        span.add_event("Preparando para rolar o dado")
        
        # Simula o lançamento do dado
        time.sleep(random.uniform(0.1, 0.3))  # Simula latência de processamento
        roll_value = random.randint(1, 6)
        
        # Adicionando atributos ricos ao Span (metadados importantes para filtros e buscas)
        span.set_attribute("roll.value", roll_value)
        span.set_attribute("roll.player", player)
        
        is_lucky = roll_value >= 5
        span.set_attribute("roll.is_lucky", is_lucky)
        
        # Incrementa nossa métrica Counter
        # Opcionalmente passamos atributos para categorizar e segmentar a contagem
        dice_roll_counter.add(1, {"player": player, "lucky": str(is_lucky)})
        
        # Registra o valor no Histogram
        dice_roll_histogram.record(roll_value, {"player": player})
        
        span.add_event("Dado rolado com sucesso")
        
        logger.info(f"Dado rolado. Resultado: {roll_value} (Sorte: {is_lucky})")
        
        return {
            "player": player,
            "roll": roll_value,
            "lucky": is_lucky
        }

# Rota /sim-workflow demonstrando traces hierárquicos (parent-child spans) e tratamento de erros
@app.get("/sim-workflow")
def simulate_workflow():
    logger.info("Iniciando fluxo de trabalho complexo simulado...")
    
    with tracer.start_as_current_span("complex_workflow_root") as root_span:
        
        # --- ETAPA 1: Consulta no banco de dados (Span Filho 1) ---
        with tracer.start_as_current_span("db_query_step") as db_span:
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.statement", "SELECT * FROM users WHERE active = true;")
            
            logger.info("Simulando query no banco de dados...")
            time.sleep(0.15)  # Simulação
            db_span.add_event("Banco respondeu com 42 usuários")
            
        # --- ETAPA 2: Integração de API externa com possibilidade de erro (Span Filho 2) ---
        with tracer.start_as_current_span("external_api_call") as api_span:
            api_span.set_attribute("http.url", "https://api.parceiro.com/v1/data")
            api_span.set_attribute("http.method", "GET")
            
            logger.info("Simulando requisição para API de parceiro...")
            time.sleep(0.1)
            
            # Simula uma chance de falha (30%)
            should_fail = random.random() < 0.3
            if should_fail:
                error_msg = "Conexão com a API do parceiro expirou (Timeout de 5000ms)"
                logger.error(error_msg)
                
                # Registra a exceção no Span para aparecer de forma destacada no Jaeger
                api_span.record_exception(ValueError(error_msg))
                # Marca o status do Span como ERROR
                api_span.set_status(StatusCode.ERROR, error_msg)
                
                raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível")
            
            api_span.set_status(StatusCode.OK)
            api_span.add_event("API externa respondeu 200 OK")
            logger.info("Fluxo completado com sucesso!")
            
        return {"status": "sucesso", "mensagem": "Fluxo finalizado corretamente"}

# ==========================================
# 5. INSTRUMENTAÇÃO AUTOMÁTICA DO FASTAPI
# ==========================================
# O FastAPIInstrumentor vai interceptar automaticamente todas as requisições HTTP recebidas,
# criando spans pais automáticos para cada requisição HTTP recebida pela API.
FastAPIInstrumentor.instrument_app(app)
