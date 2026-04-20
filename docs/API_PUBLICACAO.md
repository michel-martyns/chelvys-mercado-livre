# Documentação API Mercado Livre - Publicação de Produtos

## Visão Geral

Esta documentação descreve o fluxo completo para publicação de produtos na plataforma do Mercado Livre utilizando a API oficial.

---

## 1. Autenticação

### OAuth 2.0

A API do Mercado Livre utiliza autenticação OAuth 2.0. Todas as requisições devem incluir o access token no header.

**Header obrigatório:**
```
Authorization: Bearer {ACCESS_TOKEN}
```

### Obtenção do Access Token

1. Acesse o [Mercado Livre Developers](https://developers.mercadolivre.com.br/)
2. Crie uma aplicação para obter `APP_ID` e `SECRET_KEY`
3. Redirecione o usuário para autorização:
   ```
   https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}
   ```
4. Troque o código recebido pelo access token:
   ```
   POST https://api.mercadolivre.com/oauth/token
   ```

**Body da requisição:**
```json
{
  "client_id": "{APP_ID}",
  "client_secret": "{SECRET_KEY}",
  "grant_type": "authorization_code",
  "redirect_uri": "{REDIRECT_URI}",
  "code": "{AUTH_CODE}"
}
```

### Refresh Token

O access token expira após 6 horas. Use o refresh token para obter um novo:

```
POST https://api.mercadolivre.com/oauth/token
```

**Body:**
```json
{
  "client_id": "{APP_ID}",
  "client_secret": "{SECRET_KEY}",
  "grant_type": "refresh_token",
  "refresh_token": "{REFRESH_TOKEN}"
}
```

---

## 2. Publicação de Produto

### Endpoint Principal

```
POST https://api.mercadolivre.com/items
```

### Campos Obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `title` | string | Título do produto (máx. 60 caracteres) |
| `category_id` | string | ID da categoria do produto |
| `price` | number | Preço do produto |
| `currency_id` | string | Moeda (BRL para Brasil, USD para outros) |
| `available_quantity` | integer | Quantidade disponível em estoque |
| `buying_mode` | string | Modo de compra (geralmente "buy_it_now") |
| `condition` | string | Condição: `new`, `used`, `not_applicable` |
| `pictures` | array | Lista de URLs das imagens do produto |

### Campos Importantes Adicionais

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `description` | string | **DEPRECIADO** - Usar endpoint separado |
| `seller_custom_id` | string | ID personalizado do vendedor |
| `video_id` | string | ID do vídeo (se houver) |
| `attributes` | array | Atributos específicos da categoria |
| `channels` | array | Canais de publicação: `["marketplace", "mshops"]` |
| `item_condition` | string | Nova forma de definir condição (dentro de attributes) |

### Exemplo de Requisição

```bash
curl -X POST https://api.mercadolivre.com/items \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \
  -d '{
    "title": "Produto Exemplo",
    "category_id": "MLB1234",
    "price": 99.90,
    "currency_id": "BRL",
    "available_quantity": 100,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "pictures": [
      {
        "source": "https://exemplo.com/imagem1.jpg"
      },
      {
        "source": "https://exemplo.com/imagem2.jpg"
      }
    ],
    "channels": ["marketplace", "mshops"],
    "attributes": [
      {
        "id": "BRAND",
        "value_name": "Marca Exemplo"
      }
    ]
  }'
```

### Exemplo de Resposta (Sucesso)

```json
{
  "id": "MLB1234567890",
  "status": "active",
  "seller_id": 123456,
  "date_created": "2026-04-19T10:00:00.000Z",
  "permalink": "https://produto.mercadolivre.com.br/MLB-1234567890"
}
```

---

## 3. Adicionar Descrição

Desde setembro de 2021, a descrição deve ser enviada em um endpoint separado **após** criar o item.

### Endpoint

```
POST https://api.mercadolivre.com/items/{ITEM_ID}/description
```

### Exemplo de Requisição

```bash
curl -X POST https://api.mercadolivre.com/items/MLB1234567890/description \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \
  -d '{
    "plain_text": "Descrição completa do produto.

Este é um exemplo de descrição em texto puro.

## Características:
- Alta qualidade
- Durabilidade
- Garantia de 12 meses

## Especificações:
- Dimensões: 10x10x5 cm
- Peso: 500g
- Cor: Preto"
  }'
```

### Formato com HTML

Também é possível enviar descrição em HTML:

```json
{
  "html": "<p>Descrição com <strong>formatação HTML</strong></p>"
}
```

---

## 4. Canais de Publicação

Use o array `channels` para definir onde o produto será publicado:

| Canal | Valor | Descrição |
|-------|-------|-----------|
| Marketplace | `"marketplace"` | Publicação no site principal do Mercado Livre |
| Mercado Shops | `"mshops"` | Publicação na loja virtual integrada |

### Exemplos

**Apenas no Marketplace:**
```json
"channels": ["marketplace"]
```

**Marketplace e Mercado Shops:**
```json
"channels": ["marketplace", "mshops"]
```

**Apenas Mercado Shops:**
```json
"channels": ["mshops"]
```

---

## 5. Condição do Produto

### Forma Antiga (ainda suportada)

```json
{
  "condition": "new"
}
```

### Forma Nova (recomendada para novas implementações)

```json
{
  "attributes": [
    {
      "id": "ITEM_CONDITION",
      "value_name": "new"
    }
  ]
}
```

**Valores possíveis:**
- `new` - Novo
- `used` - Usado
- `not_applicable` - Não se aplica

---

## 6. Fluxo Completo de Publicação

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE PUBLICAÇÃO                       │
└─────────────────────────────────────────────────────────────┘

1. OBTER TOKEN
   POST /oauth/token
   │
   ▼
2. CRIAR ITEM
   POST /items
   │
   ▼
3. ADICIONAR DESCRIÇÃO
   POST /items/{ITEM_ID}/description
   │
   ▼
4. (OPCIONAL) ADICIONAR VARIAÇÕES
   PUT /items/{ITEM_ID}
   │
   ▼
5. (OPCIONAL) DEFINIR FRETE
   PUT /items/{ITEM_ID}/shipping
   │
   ▼
6. PRODUTO PUBLICADO ✓
```

---

## 7. Endpoints Úteis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/items/{ITEM_ID}` | Buscar informações de um item |
| `PUT` | `/items/{ITEM_ID}` | Atualizar um item |
| `DELETE` | `/items/{ITEM_ID}` | Excluir um item |
| `POST` | `/items/{ITEM_ID}/description` | Adicionar descrição |
| `PUT` | `/items/{ITEM_ID}/description` | Atualizar descrição |
| `GET` | `/sites` | Listar sites disponíveis |
| `GET` | `/categories/{CATEGORY_ID}` | Buscar categoria |
| `GET` | `/categories/{CATEGORY_ID}/attributes` | Atributos da categoria |

---

## 8. Códigos de Erro Comuns

| Código | Descrição | Solução |
|--------|-----------|---------|
| `400` | Bad Request | Verifique se todos os campos obrigatórios estão presentes |
| `401` | Unauthorized | Token expirado ou inválido - faça refresh |
| `403` | Forbidden | Permissões insuficientes |
| `404` | Not Found | Item ou categoria não existe |
| `429` | Too Many Requests | Limite de requisições excedido - aguarde |
| `500` | Internal Server Error | Erro no servidor - tente novamente |

---

## 9. Rate Limits

| Tipo de Acesso | Limite |
|----------------|--------|
| Aplicação nova | 2 requisições/segundo |
| Aplicação estabelecida | Até 50 requisições/segundo |

**Header de resposta com limites:**
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 49
X-RateLimit-Reset: 1682000000
```

---

## 10. Links Oficiais

- [Portal de Desenvolvedores](https://developers.mercadolivre.com.br/)
- [Guia de Publicação de Produtos](https://developers.mercadolivre.com.br/pt_br/gerenciamento-de-vendas/publicacao-de-produtos)
- [Referência da API](https://developers.mercadolivre.com.br/en_us/)
- [User Products (Novo Modelo)](https://developers.mercadolivre.com.br/pt_br/user-products)

---

## 11. Observações Importantes

### Mudanças Recentes

1. **`exclusive_channel` removido** - Use o array `channels` para definir canais
2. **`condition` depreciado** - Novas implementações devem usar `item_condition` dentro de `attributes`
3. **Descrição separada** - Desde 2021, descrição deve ser enviada via endpoint separado
4. **User Products** - Novo modelo de publicação em transição para novos desenvolvedores

### Melhores Práticas

- Sempre faça cache das categorias e atributos para evitar requisições desnecessárias
- Implemente retry com backoff exponencial para erros 429
- Mantenha o token sempre atualizado usando refresh_token
- Valide os dados localmente antes de enviar para a API
