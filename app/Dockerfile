FROM python:3.10-slim

WORKDIR /usr/src/app

# Copia o requirements subindo um nível
COPY requirements.txt ./ 

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# COPIA CORRETA: Copia tudo o que está na pasta do Dockerfile (que é a própria pasta app)
COPY app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
