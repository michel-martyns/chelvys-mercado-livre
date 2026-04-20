# Deploy - Cloud Run OAuth Callback

## Visão Geral

Este documento descreve como fazer deploy da aplicação de OAuth callback no Google Cloud Run.

## Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Mercado Livre  │────▶│  Cloud Run       │────▶│  Secret Manager │
│  OAuth Server   │     │  (Callback)      │     │  (Tokens)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                         ┌──────────────────┐
                         │  Cloud Build     │
                         │  (Build Image)   │
                         └──────────────────┘
```

## Custo Estimado

| Serviço | Custo Mensal |
|---------|--------------|
| Cloud Run (2 req/dia) | ~$0 (free tier) |
| Artifact Registry | ~$0 (5GB free) |
| **Total** | **~$0/mês** |

---

## Passo 1: Habilitar APIs Necessárias

```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

---

## Passo 2: Criar Artifact Registry

```bash
gcloud artifacts repositories create chelvys-docker \
  --repository-format=docker \
  --location=southamerica-east1 \
  --description="Docker registry para aplicações Chelvys"
```

---

## Passo 3: Build e Push da Imagem

```bash
# Navegar até o diretório do projeto
cd chelvys-mercado-livre

# Build da imagem
gcloud builds submit --tag southamerica-east1-docker.pkg.dev/chelvys/chelvys-docker/ml-oauth-callback:latest

# O build usa o Dockerfile automaticamente
```

---

## Passo 4: Deploy no Cloud Run

```bash
gcloud run deploy ml-oauth-callback \
  --image southamerica-east1-docker.pkg.dev/chelvys/chelvys-docker/ml-oauth-callback:latest \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 300 \
  --set-env-vars="MERCADOLIVRE_APP_ID=2968420069553527,MERCADOLIVRE_SECRET_KEY=lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS"
```

### Parâmetros Explicados

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `--allow-unauthenticated` | Sim | OAuth precisa ser acessível publicamente |
| `--min-instances 0` | 0 | Não cobrar quando ocioso |
| `--max-instances 1` | 1 | Limitar custos |
| `--memory 256Mi` | 256MB | Suficiente para app simples |
| `--cpu 1` | 1 vCPU | Padrão mínimo |

---

## Passo 5: Obter URL do Serviço

```bash
gcloud run services describe ml-oauth-callback \
  --platform managed \
  --region southamerica-east1 \
  --format="value(status.url)"
```

Exemplo de URL: `https://ml-oauth-callback-*.a.run.app`

---

## Passo 6: Configurar no Mercado Livre

1. Acesse https://applications.mercadolivre.com.br/
2. Selecione sua aplicação "Auto Publicador WeDrop"
3. Em "Redirect URIs", adicione a URL do Cloud Run + `/callback`:
   ```
   https://ml-oauth-callback-*.a.run.app/callback
   ```
4. Salve

---

## Passo 7: Testar o Fluxo

### Acessar URL de Autorização

```bash
# Substitua pela sua URL do Cloud Run
AUTH_URL="https://ml-oauth-callback-*.a.run.app/callback"
curl "$AUTH_URL"
```

Ou abra no navegador:
```
https://ml-oauth-callback-*.a.run.app/
```

### Clicar em "Autorizar Aplicação"

1. Será redirecionado para o Mercado Livre
2. Faça login e autorize
3. Voltará para o Cloud Run com o código
4. A aplicação troca o código pelo token
5. Tokens salvos em `.env_tokens`

---

## Passo 8: Recuperar Tokens

### Opção A: Via Logs do Cloud Run

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ml-oauth-callback" \
  --limit=10 \
  --format="table(textPayload)"
```

### Opção B: Via Secret Manager (Recomendado)

```bash
# Criar secret
gcloud secrets create ml-access-token --replication-policy="automatic"
gcloud secrets create ml-refresh-token --replication-policy="automatic"

# Adicionar versões (após obter tokens)
echo -n "SEU_ACCESS_TOKEN" | gcloud secrets versions add ml-access-token --data-file=-
echo -n "SEU_REFRESH_TOKEN" | gcloud secrets versions add ml-refresh-token --data-file=-

# Acessar tokens
gcloud secrets versions access latest --secret=ml-access-token
gcloud secrets versions access latest --secret=ml-refresh-token
```

---

## Passo 9: Atualizar .env Local

Copie os tokens obtidos para o `.env` local:

```env
MERCADOLIVRE_ACCESS_TOKEN=APP_USR-...
MERCADOLIVRE_REFRESH_TOKEN=TGRT-...
```

---

## Teste Final

```bash
# Testar API do ML
ACCESS_TOKEN="seu_token_aqui"

curl -X GET "https://api.mercadolivre.com/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Resposta esperada:
```json
{
  "id": 123456789,
  "nickname": "seu_nick",
  "email": "seu@email.com"
}
```

---

## Comandos Úteis

### Ver status do serviço
```bash
gcloud run services describe ml-oauth-callback --region southamerica-east1
```

### Ver logs em tempo real
```bash
gcloud app logs tail -s ml-oauth-callback
```

### Deletar serviço
```bash
gcloud run services delete ml-oauth-callback --region southamerica-east1
```

### Listar todas as revisões
```bash
gcloud run revisions list --service ml-oauth-callback --region southamerica-east1
```

---

## Troubleshooting

### Erro: "Permission denied"
```bash
# Verificar permissões da service account
gcloud projects add-iam-policy-binding chelvys \
  --member="serviceAccount:112928287261109296808-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### Erro: "Invalid redirect_uri"
- Verifique se o URI no Cloud Run **exatamente igual** ao cadastrado no ML
- Inclua `/callback` no final

### Erro: "Code expired"
- O código expira em minutos
- Execute o fluxo novamente

### Cloud Run muito lento (cold start)
- Normal com `--min-instances 0`
- Primeiro request demora ~2-5 segundos
- Requests subsequentes são rápidos
