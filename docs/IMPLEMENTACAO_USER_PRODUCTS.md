# Implementação User Products API - Mercado Livre

**Data:** 2026-04-19  
**Status:** Em andamento - Descoberta de API

## Contexto

Vendedor **CHELVYS** (ID: 384397682) possui a tag `user_product_seller`, o que exige o uso do modelo **User Products** (catálogo 2026) em vez do endpoint tradicional `/items`.

## Tags do Vendedor

```
- normal
- business
- messages_as_seller
- eshop
- user_product_seller  <-- CRÍTICO: exige User Products model
```

## Descobertas da API

### 1. Endpoints que NÃO funcionam (404)

```python
# User Products endpoint - não existe
POST /user-products  # 404

# Catalog Products - não existe
GET  /catalog/products
POST /catalog/products

# Families/Domains - não existem
GET /families?category_id=...
GET /domains/search?...

# Category attributes - não encontrado
GET /categories/MLB147982
GET /categories/MLB147982/attributes

# Decorations - não encontrado
GET /decorations/section?...
```

### 2. Endpoint que FUNCIONA

```python
POST https://api.mercadolibre.com/items
```

**Porém** requer:
- `family_name` (obrigatório para user_product_seller)
- **NÃO** pode ter `title` (vem do catálogo)
- Atributos específicos da categoria
- Categoria deve ser **leaf category**

### 3. Erros Encontrados e Soluções

#### Erro 1: Missing family_name
```json
{
  "message": "body.required_fields",
  "cause": ["The body does not contains some or none of the following properties [family_name]"]
}
```
**Solução:** Adicionar `family_name` ao payload

#### Erro 2: Invalid field 'title'
```json
{
  "message": "body.invalid_fields",
  "cause": ["The fields [title] are invalid for requested call"]
}
```
**Solução:** Remover `title` - User Products usa catálogo, título é derivado do `family_name`

#### Erro 3: ITEM_CONDITION invalid
```json
{
  "message": "Couldn't obtain a valid item condition mapping from ITEM_CONDITION attribute"
}
```
**Solução:** Usar `value_id` em vez de `value_name` (ainda em teste)

#### Erro 4: Missing package dimensions
```json
{
  "message": "The attributes [seller_package_height, seller_package_width, seller_package_length, seller_package_weight] are all required"
}
```
**Solução:** Adicionar atributos de dimensão do pacote

#### Erro 5: Invalid category (not leaf)
```json
{
  "message": "Is not allowed to post in category MLB1000. Make sure you're posting in a leaf category"
}
```
**Solução:** Usar categoria final (leaf), não categoria pai

#### Erro 6: Build-title validation
```json
{
  "message": "Error getting resource /decorations/build-title with params [...]",
  "cause": ["attributes are required"]
}
```
**Solução:** Adicionar atributo BRAND

### 4. Estrutura do Payload (User Products)

```python
payload = {
    "category_id": "MLBXXXXX",  # Leaf category obrigatório
    "price": 68.82,
    "currency_id": "BRL",
    "available_quantity": 50,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_special",
    "family_name": "Nome da Família no Catálogo",
    "pictures": [
        {"source": "https://..."}
    ],
    "attributes": [
        {"id": "BRAND", "value_name": "Generic"},
        {"id": "SELLER_PACKAGE_HEIGHT", "value_name": "5 cm"},
        {"id": "SELLER_PACKAGE_WIDTH", "value_name": "10 cm"},
        {"id": "SELLER_PACKAGE_LENGTH", "value_name": "12 cm"},
        {"id": "SELLER_PACKAGE_WEIGHT", "value_name": "150 g"}
    ]
}
```

### 5. Categorias Exploradas

```
MLB1000: Eletrônicos, Áudio e Vídeo
  └── MLB1002: Áudio (não é leaf)
      └── [subcategorias não mapeadas completamente]

MLB147982: Fones de Ouvido (categoria original do teste)
  - Retorna 404 em /categories/MLB147982
  - Possivelmente desativada ou renomeada
```

### 6. Próximos Passos Necessários

1. **Encontrar leaf category válida para fones TWS**
   - Explorar MLB1002 (Áudio) completamente
   - Ou usar categoria genérica de acessórios

2. **Identificar atributos obrigatórios da categoria**
   - Endpoint de attributes não responde
   - Tentar tentativa e erro ou consultar docs oficiais

3. **Vincular produto ao catálogo**
   - `family_name` deve existir no catálogo do ML
   - Possível necessidade de criar família primeiro

4. **Testar com produto real do catálogo**
   - Usar family_id existente
   - Ou criar nova família via endpoint apropriado

## Código de Teste Criado

Arquivo: `src/test_user_products.py`

```python
# Estrutura atual (fallback incluso)
async def criar_user_product():
    payload = {
        "family_name": "Fone TWS Wireless Estereo",
        "category_id": "MLB147982",
        "price": preco_venda,
        # ... atributos básicos
    }
    # POST /user-products (404)
    # Fallback: /items tradicional

async def criar_item_tradicional():
    # Fallback para sellers sem tag user_product_seller
    payload = {
        "title": "Produto Teste",
        "category_id": "...",
        # ... campos tradicionais
    }
```

## Lições Aprendidas

1. **User Products API é diferente do modelo tradicional**
   - Não usa `title`, usa `family_name` vinculado ao catálogo
   - Exige atributos específicos (dimensões, peso)
   - Categoria deve ser leaf

2. **API do ML tem limitações de documentação**
   - Muitos endpoints retornam 404
   - Domínio `api.mercadolibre.com` funciona, `api.mercadolivre.com.br` não
   - Necessário explorar via tentativa e erro

3. **Vendedor com user_product_seller tem restrições**
   - Não pode criar items com `title` livre
   - Deve vincular ao catálogo existente
   - Fluxo é mais rígido porém padronizado

## Referências

- Developers ML: http://developers.mercadolibre.com
- OAuth Callback: https://ml-oauth-callback-783579532864.southamerica-east1.run.app/callback
- Seller ID: 384397682 (CHELVYS)
