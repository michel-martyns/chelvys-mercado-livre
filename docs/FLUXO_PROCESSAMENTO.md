# Fluxo de Processamento - WeDrop para Mercado Livre

## Visão Geral do Projeto

Sistema de automação para:
1. Extrair produtos do catálogo WeDrop
2. Enriquecer e tratar informações
3. Melhorar qualidade das imagens
4. Publicar automaticamente no Mercado Livre

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FLUXO COMPLETO                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐ │
│  │   WeDrop    │───▶│  Extração   │───▶│ Enriqueci-  │───▶│   Tratamento│ │
│  │  Catálogo   │    │   Dados     │    │   mento     │    │   Imagens   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └────────────┘ │
│                                                                   │       │
│                                                                   ▼       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │       │
│  │   Mercado   │◀───│ Publicação  │◀───│  Validação  │◀──────────┘       │
│  │   Livre     │    │   API       │    │   Dados     │                   │
│  └─────────────┘    └─────────────┘    └─────────────┘                   │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Extração de Dados (WeDrop)

### URL Base do Catálogo
```
https://dash.wedrop.com.br/catalog/{ID_CATALOGO}
```

### Catálogo Exemplo
```
https://dash.wedrop.com.br/catalog/32425
```

### Dados a Extrair de Cada Produto

| Campo | Descrição | Origem |
|-------|-----------|--------|
| `nome` | Nome/título do produto | Título principal |
| `preço` | Preço de custo | Valor exibido |
| `imagens` | URLs das fotos | Galeria de imagens |
| `descricao` | Descrição detalhada | Texto descritivo |
| `sku` | Código SKU | Identificador único |
| `categoria` | Categoria do produto | Classificação WeDrop |
| `estoque` | Quantidade disponível | Status de estoque |
| `variações` | Cores, tamanhos | Seletor de variações |
| `peso` | Peso do produto | Ficha técnica |
| `dimensões` | Tamanho da embalagem | Ficha técnica |

### Método de Extração

Como não há API pública, a extração será feita via:

**Opção A: Web Scraping (Recomendado inicialmente)**
```python
# Fluxo sugerido
1. Login automático na WeDrop (requests + BeautifulSoup ou Selenium)
2. Navegar até o catálogo
3. Extrair HTML e parsear dados
4. Salvar em formato estruturado (JSON)
```

**Opção B: Exportação Manual**
```
1. Acessar dashboard manualmente
2. Exportar CSV/XML (se disponível)
3. Processar arquivo localmente
```

---

## 2. Enriquecimento de Dados

### O que Enriquecer

| Dado Original | Ação | Resultado |
|---------------|------|-----------|
| Título básico | Adicionar palavras-chave | Título otimizado para SEO |
| Descrição curta | Expandir com benefícios | Descrição completa e persuasiva |
| Categoria WeDrop | Mapear para categoria ML | Category ID do Mercado Livre |
| Atributos genéricos | Adicionar atributos específicos | Marca, modelo, material, etc. |

### Exemplo de Transformação

**Original (WeDrop):**
```json
{
  "nome": "Fone Bluetooth TWS",
  "descricao": "Fone sem fio com case",
  "categoria": "Eletrônicos"
}
```

**Enriquecido:**
```json
{
  "title": "Fone Bluetooth TWS Wireless Estéreo Hi-Fi Com Case Carregador",
  "description": "## Descrição do Produto\n\nExperimente a liberdade do som sem fios com o Fone Bluetooth TWS...\n\n### Características:\n- Tecnologia Bluetooth 5.0\n- Autonomia de 24 horas com case\n- Cancelamento de ruído passivo\n- Design ergonômico e confortável...",
  "category_id": "MLB147982",
  "attributes": [
    {"id": "BRAND", "value_name": "Genérico"},
    {"id": "CONNECTIVITY", "value_name": "Bluetooth"},
    {"id": "MODEL", "value_name": "TWS"}
  ]
}
```

### Mapeamento de Categorias

| Categoria WeDrop | Categoria ML | Category ID |
|------------------|--------------|-------------|
| Eletrônicos > Áudio | Fones de Ouvido | MLB147982 |
| Casa e Decoração | Iluminação | MLB123456 |
| Esportes | Fitness | MLB789012 |

*(IDs de exemplo - consultar API do ML)*

---

## 3. Tratamento de Imagens

### Problemas Comuns em Imagens de Fornecedores

- [ ] Baixa resolução
- [ ] Marca d'água do fornecedor
- [ ] Fundo inadequado (Mercado Livre exige fundo branco)
- [ ] Tamanho inconsistente
- [ ] Compressão excessiva

### Fluxo de Processamento

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Download  │───▶│  Redimensionar │───▶│  Remover   │───▶│  Otimizar   │
│   Imagem    │    │  (min 1000px) │    │  Fundo/    │    │  (WebP/JPG) │
│             │    │               │    │  Marca     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────┐
                                                         │   Upload    │
                                                         │   (S3/Imgur)│
                                                         └─────────────┘
```

### Requisitos Mercado Livre para Imagens

| Requisito | Especificação |
|-----------|---------------|
| Resolução mínima | 1000x1000 pixels |
| Formato | JPG, PNG, WebP |
| Fundo | Branco ou neutro |
| Marca d'água | **Não permitido** |
| Texto na imagem | **Não permitido** |
| Quantidade | Até 30 imagens por produto |

### Ferramentas Sugeridas

| Tarefa | Ferramenta |
|--------|------------|
| Processamento | Python Pillow, OpenCV |
| Remoção de fundo | remove.bg API, Background Remover |
| Hospedagem | AWS S3, Cloudinary, Imgur API |
| Otimização | TinyPNG API, Squoosh |

---

## 4. Publicação no Mercado Livre

### Fluxo API

```python
# 1. Autenticar
POST /oauth/token → access_token

# 2. Publicar produto
POST /items
  Headers: Authorization: Bearer {access_token}
  Body: {
    "title": "...",
    "category_id": "...",
    "price": ...,
    "pictures": [...],
    ...
  }

# 3. Adicionar descrição
POST /items/{item_id}/description
  Body: { "plain_text": "..." }

# 4. Salvar ID gerado
item_id → Banco de dados local
```

### Mapeamento de IDs

| Dado | WeDrop | → | Mercado Livre |
|------|--------|---|---------------|
| SKU | `WD12345` | → | `seller_custom_id` |
| Preço Custo | `R$ 50,00` | → | Calcular preço venda |
| Estoque | `100 un` | → | `available_quantity` |

### Cálculo de Preço de Venda

```
preço_venda = preço_custo + markup + taxas + frete

Onde:
- preço_custo: Valor do fornecedor
- markup: Lucro desejado (ex: 30%)
- taxas: Taxa ML (~12-19%)
- frete: Custo médio de envio
```

---

## 5. Estrutura de Dados

### Schema do Produto Processado

```json
{
  "wedrop_id": "32425-001",
  "wedrop_sku": "WD12345",
  "wedrop_url": "https://dash.wedrop.com.br/catalog/32425/prod/123",
  
  "ml_item_id": null,
  "ml_status": "pending",
  
  "data": {
    "title": "Produto Exemplo",
    "category_id": "MLB123456",
    "price": 99.90,
    "currency_id": "BRL",
    "available_quantity": 100,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "pictures": [
      {"source": "https://cdn.meusite.com/prod1-1.jpg"},
      {"source": "https://cdn.meusite.com/prod1-2.jpg"}
    ],
    "description": "Descrição completa...",
    "attributes": [...],
    "channels": ["marketplace", "mshops"]
  },
  
  "processed_at": "2026-04-19T10:00:00Z",
  "published_at": null
}
```

---

## 6. Estrutura de Pastas Sugerida

```
chelvys-mercado-livre/
├── src/
│   ├── wedrop/
│   │   ├── extractor.py      # Scraping/extração
│   │   └── models.py         # Modelos de dados
│   │
│   ├── enrichment/
│   │   ├── enricher.py       # Enriquecimento de dados
│   │   ├── category_mapper.py # Mapeamento de categorias
│   │   └── prompts.py        # Prompts para IA
│   │
│   ├── images/
│   │   ├── processor.py      # Processamento de imagens
│   │   ├── upscaler.py       # Melhoria de resolução
│   │   └── uploader.py       # Upload para CDN
│   │
│   ├── mercadolivre/
│   │   ├── api.py            # Cliente API ML
│   │   ├── auth.py           # Autenticação OAuth
│   │   └── publisher.py      # Publicação de produtos
│   │
│   └── utils/
│       ├── config.py
│       ├── logger.py
│       └── database.py
│
├── data/
│   ├── raw/                  # Dados brutos extraídos
│   ├── processed/            # Dados processados
│   └── images/               # Imagens processadas
│
├── docs/
│   ├── API_PUBLICACAO.md
│   ├── FLUXO_PROCESSAMENTO.md
│   └── ...
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py
```

---

## 7. Checklist de Implementação

### Fase 1: Extração
- [ ] Configurar autenticação WeDrop
- [ ] Criar scraper do catálogo
- [ ] Exportar dados para JSON
- [ ] Salvar imagens localmente

### Fase 2: Enriquecimento
- [ ] Criar prompt para enriquecer títulos
- [ ] Criar prompt para expandir descrições
- [ ] Mapear categorias WeDrop → ML
- [ ] Adicionar atributos específicos

### Fase 3: Imagens
- [ ] Download automático de imagens
- [ ] Redimensionar para 1000x1000 mínimo
- [ ] Remover marcas d'água/fundo
- [ ] Upload para CDN
- [ ] Obter URLs públicas

### Fase 4: Publicação
- [ ] Configurar OAuth ML
- [ ] Implementar cliente API
- [ ] Publicar produtos teste
- [ ] Validar publicação

### Fase 5: Automação
- [ ] Criar pipeline completo
- [ ] Adicionar logs e monitoramento
- [ ] Tratar erros e retries
- [ ] Dashboard de status

---

## 8. Considerações Importantes

### Termos de Uso WeDrop
⚠️ **Atenção:** Verificar se os termos da WeDrop permitem:
- Scraping automatizado
- Revenda via marketplaces
- Uso de imagens dos produtos

### Limites da API Mercado Livre
- 2 requisições/segundo (aplicações novas)
- Até 50 req/seg (aplicações estabelecidas)
- Implementar rate limiting e retry

### Qualidade dos Dados
- Sempre validar dados antes de publicar
- Manter backup local de todos os produtos
- Logar todas as publicações e erros
