FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/oauth_callback/ ./

# Expor porta
ENV PORT=8080
EXPOSE 8080

# Rodar aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
