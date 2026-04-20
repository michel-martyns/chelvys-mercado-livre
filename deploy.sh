#!/bin/bash
# Script de deploy do OAuth Callback no Cloud Run
# Uso: ./deploy.sh

set -e

# Configurações
PROJECT_ID="chelvys"
REGION="southamerica-east1"
REPO_NAME="chelvys-docker"
IMAGE_NAME="ml-oauth-callback"
SERVICE_NAME="ml-oauth-callback"

echo "==================================="
echo "Deploy - ML OAuth Callback"
echo "==================================="

# 1. Habilitar APIs
echo "[1/6] Habilitando APIs..."
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project $PROJECT_ID

# 2. Criar Artifact Registry (se não existir)
echo "[2/6] Verificando Artifact Registry..."
gcloud artifacts repositories describe $REPO_NAME \
  --location=$REGION \
  --project=$PROJECT_ID \
  || gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker registry para aplicações Chelvys" \
    --project=$PROJECT_ID

# 3. Build da imagem
echo "[3/6] Build da imagem Docker..."
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  --project=$PROJECT_ID

# 4. Deploy no Cloud Run
echo "[4/6] Deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 300 \
  --set-env-vars="MERCADOLIVRE_APP_ID=2968420069553527,MERCADOLIVRE_SECRET_KEY=lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS" \
  --project=$PROJECT_ID

# 5. Obter URL
echo "[5/6] Obtendo URL do serviço..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format="value(status.url)" \
  --project=$PROJECT_ID)

echo ""
echo "==================================="
echo "✅ Deploy completo!"
echo "==================================="
echo ""
echo "URL do serviço: $SERVICE_URL"
echo "URL de callback: $SERVICE_URL/callback"
echo ""
echo "Próximos passos:"
echo "1. Adicione '$SERVICE_URL/callback' no Redirect URIs do Mercado Livre"
echo "2. Acesse $SERVICE_URL para iniciar o OAuth"
echo ""
echo "Comandos úteis:"
echo "  Ver logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo "  Ver status: gcloud run services describe $SERVICE_NAME --region $REGION"
echo ""
