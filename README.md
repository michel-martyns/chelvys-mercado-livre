# Chelvys - Mercado Livre Automação

Sistema de automação para publicação de produtos WeDrop no Mercado Livre com processamento de imagens via IA.

## Visão Geral

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   WeDrop    │ -> │  Processador │ -> │  GCS/URLs   │ -> │  Mercado     │
│  (extrair)  │    │   (imagens)  │    │  (hospedar) │    │   Livre      │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## Funcionalidades

- **Extração WeDrop**: Scraping de produtos do catálogo (ID, nome, preço, imagens, descrição)
- **Classificação LLM**: Uso de IA para mapear produto → categoria MLB correta
- **Processamento de Imagens**:
  - Redimensionamento para 1200x1200px (padrão ML 2026)
  - AI Enhance (nitidez, contraste, saturação, brilho)
  - Remoção de fundo
  - Otimização de peso (< 2MB)
- **Upload GCS**: Hospedagem em `gs://chelvys-ml-images/mercado-livre/{nome-normalizado}/`
- **Publicação ML**: API User Products (vendedor com tag `user_product_seller`)

## Estrutura do Projeto

```
chelvys-mercado-livre/
├── docs/
│   ├── API_PUBLICACAO.md         # API Mercado Livre
│   ├── FLUXO_PROCESSAMENTO.md    # Fluxo imagens
│   ├── DEPLOY_CLOUD_RUN.md       # OAuth callback
│   ├── IMPLEMENTACAO_USER_PRODUCTS.md  # User Products API
│   └── PIPELINE_COMPLETO.md      # Documentação completa
├── src/
│   ├── main.py                   # Pipeline principal
│   ├── test_pipeline.py          # Teste com mock
│   ├── test_user_products.py     # Teste User Products
│   ├── oauth_callback/
│   │   └── main.py              # FastAPI OAuth
│   ├── wedrop/
│   │   └── extractor.py         # Scraper WeDrop
│   ├── images/
│   │   ├── processor.py         # Processamento imagens
│   │   └── uploader.py          # Upload GCS
│   └── utils/
│       └── llm_category.py      # Classificador LLM
├── data/processed/               # JSONs salvos
├── requirements.txt
├── .env                          # Credenciais
└── README.md
```

## Credenciais Configuradas

| Serviço | Status | Detalhes |
|---------|--------|----------|
| WeDrop | ✅ | michelmartins70150@gmail.com |
| Mercado Livre | ✅ | App: 2968420069553527 |
| Google Cloud | ✅ | chelvys-3969c91a2439 |
| OAuth Callback | ✅ | Cloud Run deployado |

## Links Úteis

- [WeDrop Dashboard](https://dash.wedrop.com.br/)
- [Produto Teste 32425](https://dash.wedrop.com.br/catalog/32425)
- [Mercado Livre Developers](https://developers.mercadolibre.com/)
- [Google Cloud Console](https://console.cloud.google.com/)

## Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
# Editar .env com credenciais

# Configurar GCP ADC (local)
export GOOGLE_APPLICATION_CREDENTIALS="c:\Users\miche\OneDrive\Documentos\GitHub\.service-account\chelvys-3969c91a2439.json"
```

## Uso

```bash
# Pipeline completo
python src/main.py

# Teste com mock
python src/test_pipeline.py

# Teste User Products API
python src/test_user_products.py
```

## Status Atual

| Componente | Status |
|------------|--------|
| OAuth ML | ✅ Funcional |
| WeDrop Extractor | ⚠️ Parcial |
| Image Processor | ✅ Funcional |
| GCS Uploader | ⚠️ ADC local |
| ML User Products API | 🔍 Descoberta |
| LLM Categoria | ✅ Implementado |

## Documentação Completa

Ver [docs/PIPELINE_COMPLETO.md](docs/PIPELINE_COMPLETO.md) para detalhes técnicos.
