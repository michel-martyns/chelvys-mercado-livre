# Status do Projeto - Chelvys Mercado Livre

**Data:** 2026-04-19

---

## Resumo Executivo

Sistema de automação para publicação de produtos WeDrop no Mercado Livre está em fase de **configuração inicial**.

---

## Concluído ✅

### 1. Estrutura do Projeto
- [x] Repositório GitHub criado: https://github.com/michel-martyns/chelvys-mercado-livre
- [x] Primeiro commit realizado (sem credenciais)
- [x] Service Account salva localmente (não commitada)

### 2. Documentação
- [x] API_PUBLICACAO.md - Documentação completa da API ML
- [x] FLUXO_PROCESSAMENTO.md - Fluxo WeDrop → ML
- [x] SETUP_MERCADO_LIVRE.md - Setup de credenciais
- [x] DEPLOY_CLOUD_RUN.md - Deploy no GCP
- [x] STATUS_ATUAL.md - Este arquivo

### 3. Código
- [x] OAuth Callback (FastAPI) para Cloud Run
- [x] Dockerfile configurado
- [x] Script deploy.sh automatizado

### 4. Credenciais Salvas
- [x] WeDrop: `michelmartins70150@gmail.com` / `Xuxu1808*`
- [x] Mercado Livre App ID: `2968420069553527`
- [x] Mercado Livre Secret Key: `lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS`
- [x] GCP Service Account: `michel@chelvys.iam.gserviceaccount.com`

### 5. GCP Configurado
- [x] Projeto `chelvys` ativo
- [x] Cloud Resource Manager API habilitada
- [x] Artifact Registry criado: `chelvys-docker` (southamerica-east1)

---

## Pendente ⏳

### 1. Deploy Cloud Run (Concluído ✅)
- [x] Build da imagem Docker
- [x] Deploy do serviço `ml-oauth-callback`
- [x] URL: https://ml-oauth-callback-783579532864.southamerica-east1.run.app
- [ ] Configurar URL no Mercado Livre (Redirect URI)
- [ ] Obter Access Token

### 2. Implementação WeDrop
- [ ] Criar extractor (scraping)
- [ ] Modelos de dados
- [ ] Salvar dados brutos

### 3. Implementação Mercado Livre
- [ ] Cliente API
- [ ] Publicação de produtos
- [ ] Validação de dados

### 4. Pipeline Completo
- [ ] Orquestração
- [ ] Logs e monitoramento
- [ ] Tratamento de erros

---

## Próximos Passos Imediatos

1. **Build Docker** - Corrigir Dockerfile e buildar imagem
2. **Deploy Cloud Run** - Subir serviço de OAuth callback
3. **Configurar ML** - Adicionar redirect URI no Mercado Livre
4. **Obter Token** - Completar fluxo OAuth

---

## Comandos para Continuar

```bash
# Navegar para diretório do oauth
cd chelvys-mercado-livre/src/oauth_callback

# Build da imagem
gcloud builds submit --tag southamerica-east1-docker.pkg.dev/chelvys/chelvys-docker/ml-oauth-callback:latest --project=chelvys

# Deploy no Cloud Run
gcloud run deploy ml-oauth-callback \
  --image southamerica-east1-docker.pkg.dev/chelvys/chelvys-docker/ml-oauth-callback:latest \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --memory 256Mi \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars="MERCADOLIVRE_APP_ID=2968420069553527,MERCADOLIVRE_SECRET_KEY=lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS" \
  --project=chelvys
```

---

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   WeDrop    │────▶│  Extractor   │────▶│ Enriqueci-  │
│  Catálogo   │     │  (Scraping)  │     │   mento     │
└─────────────┘     └──────────────┘     └─────────────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Mercado    │◀────│   Publicador │◀────│  Imagens    │
│   Livre     │     │    (API)     │     │  (GCS/CDN)  │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## Custos Estimados (GCP)

| Serviço | Uso | Custo Mensal |
|---------|-----|--------------|
| Cloud Run | 2-10 req/dia | ~$0 (free tier) |
| Artifact Registry | 1 imagem | ~$0 (5GB free) |
| Cloud Storage | Imagens produtos | ~$0-5 (depende do volume) |
| **Total** | | **~$0-5/mês** |
