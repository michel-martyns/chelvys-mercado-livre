# Pipeline Completo: WeDrop -> Mercado Livre

**Projeto:** chelvys-mercado-livre  
**Data:** 2026-04-19  
**Status:** Implementação parcial - API ML em descoberta

## Visão Geral

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   WeDrop    │ -> │  Processador │ -> │  GCS/URLs   │ -> │  Mercado     │
│  (extrair)  │    │   (imagens)  │    │  (hospedar) │    │   Livre      │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## 1. Extração WeDrop

**Fonte:** https://dash.wedrop.com.br/catalog/{ID}  
**Credenciais:**
- Email: michelmartins70150@gmail.com
- Senha: Xuxu1808*

**Arquivo:** `src/wedrop/extractor.py`

```python
class WeDropExtractor:
    async def login(self) -> bool:
        # POST /login com email/senha
        
    async def extrair_produto(self, catalog_id: str) -> Produto:
        # GET /catalog/{id}
        # Parse HTML com BeautifulSoup
        # Retorna: id, nome, preco, imagens[], descricao, sku, etc.
```

**Dados extraídos:**
- ID do produto (ex: 32425)
- Nome completo
- Preço de custo
- Lista de URLs de imagens
- Descrição
- SKU
- Categoria
- Estoque disponível

**Status:** ⚠️ Login não persiste - requer investigação do fluxo real

---

## 2. Processamento de Imagens

**Arquivo:** `src/images/processor.py`

### Padrões Mercado Livre 2026

| Requisito | Valor |
|-----------|-------|
| Tamanho | 1200x1200px (ideal zoom) |
| Formato | JPG/PNG |
| Modo | RGB |
| Fundo | Branco/neutro |
| Peso | < 2MB (ideal 500KB) |
| Quantidade | Até 10 imagens |

### Processamento

```python
class ImageProcessor:
    TARGET_SIZE = 1200
    MIN_SIZE = 500
    MAX_SIZE = 1920
    QUALITY = 85
    
    async def processar_url(self, url: str):
        # 1. Download da imagem
        # 2. Converter para RGB
        # 3. Remover fundo (se transparente)
        # 4. Redimensionar (Lanczos)
        # 5. AI Enhance:
        #    - Unsharp Mask (nitidez)
        #    - Contraste +15%
        #    - Saturação +10%
        #    - Brilho +5%
        # 6. Otimizar peso (< 2MB)
        # 7. Retornar bytes processados
```

### AI Enhance Details

```python
def _ai_enhance(self, img: Image.Image):
    # Nitidez
    img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # Contraste
    ImageEnhance.Contrast(img).enhance(1.15)
    
    # Saturação
    ImageEnhance.Color(img).enhance(1.1)
    
    # Brilho
    ImageEnhance.Brightness(img).enhance(1.05)
```

**Opcional - ESRGAN Real:**
```bash
pip install realesrgan-opencv
```

---

## 3. Upload para Google Cloud Storage

**Arquivo:** `src/images/uploader.py`

### Estrutura no GCS

```
gs://chelvys-ml-images/mercado-livre/{nome-normalizado}/imagem1.jpg
gs://chelvys-ml-images/mercado-livre/{nome-normalizado}/imagem2.jpg
...
```

### Normalização de Nome

```python
def _normalizar_nome(self, nome: str) -> str:
    # "Fone de Ouvido Bluetooth TWS" 
    # -> "fone-de-ouvido-bluetooth-tws"
    nome = nome.lower()
    nome = re.sub(r'[^\w\s-]', '', nome)  # Remove especiais
    nome = re.sub(r'[-\s]+', '-', nome)   # Hifens múltiplos -> único
    return nome
```

### Credenciais GCP

**Service Account:** `c:\Users\miche\OneDrive\Documentos\GitHub\.service-account\chelvys-3969c91a2439.json`

**Configuração Local:**
```bash
set GOOGLE_APPLICATION_CREDENTIALS=c:\Users\miche\OneDrive\Documentos\GitHub\.service-account\chelvys-3969c91a2439.json
```

**Cloud Run:**
- Deploy com service account attach
- URL: `https://ml-oauth-callback-783579532864.southamerica-east1.run.app`

**Status:** ⚠️ ADC não configurado localmente - fallback para URLs originais

---

## 4. Enriquecimento de Dados

### Título Otimizado

```python
titulo = f"{produto.nome} - Original com Garantia"
```

### Descrição Enriquecida

```markdown
## {produto.nome}

### Características:
- Produto original e de qualidade
- Pronto para uso imediato
- Garantia do fornecedor

### Especificações:
- SKU: {produto.sku}
- Categoria: {produto.categoria}
- Peso: {produto.peso}
- Dimensões: {produto.dimensoes}

### Conteúdo da Embalagem:
- 1x {produto.nome}
- Manual de instruções
- Caixa original

---

**Envio imediato para todo o Brasil!**
```

### Cálculo de Preço

```python
MARKUP = 1.3  # 30% margem
ML_FEE = 0.15 # 15% taxa Mercado Livre

def calcular_preco_venda(custo):
    # preco_venda = custo * markup / (1 - taxa_ml)
    return round((custo * MARKUP) / (1 - ML_FEE), 2)

# Exemplo: custo R$45,00
# venda = 45 * 1.3 / 0.85 = R$68,82
# lucro = 68,82 - 45,00 = R$23,82
```

---

## 5. Publicação Mercado Livre

### Autenticação OAuth 2.0

**App ID:** 2968420069553527  
**Secret:** lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS

**Fluxo:**
1. Redirect para:
   ```
   https://auth.mercadolivre.com.br/authorization?
             client_id=2968420069553527&
             response_type=code&
             redirect_uri=https://ml-oauth-callback-783579532864.southamerica-east1.run.app/callback
   ```
2. Usuário autoriza
3. Callback recebe `code`
4. Exchange code por token:
   ```python
   POST https://api.mercadolibre.com/oauth/token
   {
     "client_id": APP_ID,
     "client_secret": SECRET_KEY,
     "grant_type": "authorization_code",
     "redirect_uri": REDIRECT_URI,
     "code": code
   }
   ```
5. Salvar `access_token` e `refresh_token`

**Arquivo OAuth:** `src/oauth_callback/main.py`

---

### User Products API (2026 Model)

**Vendedor:** CHELVYS (384397682)  
**Tag:** `user_product_seller` - exige modelo User Products

#### Payload User Products

```python
payload = {
    "category_id": "MLBXXXXX",  # Leaf category
    "family_name": "Nome da Família",  # Catálogo ML
    "price": 68.82,
    "currency_id": "BRL",
    "available_quantity": 50,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_special",
    "pictures": [{"source": url}],
    "attributes": [
        {"id": "BRAND", "value_name": "Generic"},
        {"id": "SELLER_PACKAGE_HEIGHT", "value_name": "5 cm"},
        {"id": "SELLER_PACKAGE_WIDTH", "value_name": "10 cm"},
        {"id": "SELLER_PACKAGE_LENGTH", "value_name": "12 cm"},
        {"id": "SELLER_PACKAGE_WEIGHT", "value_name": "150 g"}
    ]
}
```

#### Endpoint

```python
POST https://api.mercadolibre.com/items
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json
```

#### Resposta de Sucesso

```json
{
  "id": "MLB1234567890",
  "permalink": "https://produto.mercadolivre.com.br/MLB-1234567890",
  "status": "active"
}
```

#### Descrição do Item

```python
POST https://api.mercadolibre.com/items/{item_id}/description
{
  "plain_text": "## Descrição completa...\n\n..."
}
```

---

## 6. Estrutura de Dados Salva

**Local:** `data/processed/{item_id}.json`

```json
{
  "wedrop_id": "32425",
  "ml_item_id": "MLB1234567890",
  "ml_permalink": "https://...",
  "ml_status": "active",
  "tipo": "user_product",
  "family_name": "Fone TWS Wireless",
  "preco_custo": 45.00,
  "preco_venda": 68.82,
  "estoque": 50,
  "data_publicacao": "2026-04-19T10:30:00"
}
```

---

## Arquivos do Projeto

```
chelvys-mercado-livre/
├── src/
│   ├── main.py                 # Pipeline principal
│   ├── test_pipeline.py        # Teste com mock
│   ├── test_user_products.py   # Teste User Products API
│   ├── oauth_callback/
│   │   └── main.py            # FastAPI OAuth callback
│   ├── wedrop/
│   │   └── extractor.py       # Scraper WeDrop
│   ├── images/
│   │   ├── processor.py       # Processamento imagens
│   │   └── uploader.py        # Upload GCS
│   └── utils/
│       └── llm_category.py    # (Futuro) LLM para categorias
├── data/
│   └── processed/             # JSONs salvos
├── docs/
│   ├── API_PUBLICACAO.md      # Docs API ML
│   ├── FLUXO_PROCESSAMENTO.md # Fluxo imagens
│   ├── DEPLOY_CLOUD_RUN.md    # Deploy OAuth
│   ├── IMPLEMENTACAO_USER_PRODUCTS.md  # Esta docs
│   └── PIPELINE_COMPLETO.md   # Este arquivo
├── requirements.txt
├── .env                        # Variáveis de ambiente
└── README.md
```

---

## Variáveis de Ambiente (.env)

```bash
# WeDrop
WEDROP_EMAIL=michelmartins70150@gmail.com
WEDROP_PASSWORD=Xuxu1808*

# Mercado Livre
MERCADOLIVRE_APP_ID=2968420069553527
MERCADOLIVRE_SECRET_KEY=lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS
MERCADOLIVRE_ACCESS_TOKEN=...
MERCADOLIVRE_REFRESH_TOKEN=...

# Google Cloud
GCP_PROJECT_ID=chelvys
GCS_BUCKET_NAME=chelvys-ml-images
GOOGLE_APPLICATION_CREDENTIALS=...

# Configurações
DEFAULT_MARKUP=1.3
ML_FEE_RATE=0.15
```

---

## Status Atual por Componente

| Componente | Status | Observações |
|------------|--------|-------------|
| OAuth ML | ✅ Funcional | Cloud Run deployado |
| WeDrop Extractor | ⚠️ Parcial | Login não persiste |
| Image Processor | ✅ Funcional | PIL + enhance |
| GCS Uploader | ⚠️ Parcial | ADC local faltando |
| ML User Products API | 🔍 Descoberta | Endpoints 404, requer investigação |
| LLM Categoria | 📋 Pendente | A implementar |

---

## Próximos Passos

1. **Investigar User Products API**
   - Encontrar leaf category válida
   - Identificar atributos obrigatórios
   - Vincular family_name ao catálogo existente

2. **Configurar ADC Local**
   - `gcloud auth application-default login`
   - Ou usar service account JSON diretamente

3. **Corrigir WeDrop Extractor**
   - Investigar fluxo de login real
   - Possível necessidade de Selenium

4. **Implementar LLM para Categorias**
   - Ler nome do produto WeDrop
   - Interpretar e mapear para categoria MLB

5. **Test End-to-End**
   - Produto 32425 completo
   - Validação de preço e publicação

---

## Lições Aprendidas

1. **User Products é obrigatório para este seller**
   - Tag `user_product_seller` impede items tradicionais
   - Requer vínculo com catálogo ML

2. **API ML tem limitações**
   - Muitos endpoints documentados retornam 404
   - Domínio correto: `api.mercadolibre.com` (não .com.br)

3. **Imagens são críticas**
   - 1200x1200 ideal para zoom
   - Peso < 2MB evita rejeição

4. **OAuth requer redirect URI válido**
   - localhost não funciona
   - Cloud Run resolveu o problema
