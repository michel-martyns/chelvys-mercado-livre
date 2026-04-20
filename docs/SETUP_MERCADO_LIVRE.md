# Passo a Passo - Configuração API Mercado Livre

## Visão Geral

Para usar a API do Mercado Livre, você precisa:
1. Criar conta no Portal de Desenvolvedores
2. Registrar uma aplicação
3. Obter credenciais (App ID e Secret Key)
4. Gerar Access Token via OAuth

---

## Passo 1: Acessar o Portal de Desenvolvedores

1. Acesse: **https://developers.mercadolivre.com.br/**
2. Clique em **"Criar conta"** ou **"Fazer login"**
3. Use sua conta do Mercado Livre (a mesma que você vende/compra)

---

## Passo 2: Criar uma Aplicação

1. Após login, vá para **"Minhas Aplicações"** ou **"My Apps"**
2. Clique em **"Criar nova aplicação"** / **"Create new app"**
3. Preencha o formulário:

| Campo | Valor Sugerido |
|-------|----------------|
| **Nome da aplicação** | `Auto Publicador WeDrop` |
| **Descrição** | `Sistema de publicação automática de produtos` |
| **URL de redirecionamento** | `https://oauth.pstmn.io/v1/callback` |
| **Tipo de aplicação** | `Private` (uso próprio) |

4. Aceite os termos e clique em **"Criar"**

---

## Passo 3: Obter App ID e Secret Key

Após criar a aplicação, você verá:

```
┌─────────────────────────────────────────┐
│  Application: Auto Publicador WeDrop    │
├─────────────────────────────────────────┤
│  App ID: 1234567890123456               │
│  Secret Key: abc123def456ghi789jkl012   │
└─────────────────────────────────────────┘
```

**⚠️ IMPORTANTE:**
- Copie **App ID** e **Secret Key** imediatamente
- Guarde em local seguro (não compartilhe)
- O Secret Key só é mostrado uma vez!

---

## Passo 4: Configurar Redirect URI

1. Na página da aplicação, vá em **"Redirect URIs"**
2. Adicione: `https://oauth.pstmn.io/v1/callback`
3. Clique em **"Save"**

**Nota:** Este URI é usado pelo Postman e ferramentas similares para capturar o código de autorização.

---

## Passo 5: Gerar Access Token

### Via Postman (Recomendado)

1. Baixe o Postman: https://www.postman.com/downloads/
2. Crie uma nova collection
3. Adicione uma requisição OAuth 2.0
4. Configure:
   - **Callback URL**: `https://oauth.pstmn.io/v1/callback`
   - **Auth URL**: `https://auth.mercadolivre.com.br/authorization`
   - **Access Token URL**: `https://api.mercadolivre.com/oauth/token`
   - **Client ID**: Seu App ID
   - **Client Secret**: Sua Secret Key
   - **Scope**: `read write`
   - **State**: (gerar aleatório)
   - **Client Authentication**: `Send as basic auth header`

5. Clique em **"Get New Access Token"**
6. Autorize a aplicação
7. O token será salvo automaticamente

### Via cURL (Alternativo)

1. Acesse no navegador:
   ```
   https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={SEU_APP_ID}&redirect_uri=https://oauth.pstmn.io/v1/callback
   ```

2. Autorize e copie o código da URL resultante

3. Troque o código pelo token:
   ```bash
   curl -X POST https://api.mercadolivre.com/oauth/token \
     -H 'Content-Type: application/json' \
     -d '{
       "client_id": "SEU_APP_ID",
       "client_secret": "SUA_SECRET_KEY",
       "grant_type": "authorization_code",
       "redirect_uri": "https://oauth.pstmn.io/v1/callback",
       "code": "CODIGO_AQUI"
     }'
   ```

### Resposta Esperada

```json
{
  "access_token": "APP_USR-1234567890123456-abcdef123456...",
  "token_type": "bearer",
  "expires_in": 21600,
  "refresh_token": "TGRT-1234567890123456-ghijkl789012...",
  "scope": "read write",
  "user_id": 123456789
}
```

---

## Passo 6: Atualizar o Arquivo .env

```env
# Credenciais Mercado Livre API
MERCADOLIVRE_APP_ID=1234567890123456
MERCADOLIVRE_SECRET_KEY=abc123def456ghi789jkl012
MERCADOLIVRE_ACCESS_TOKEN=APP_USR-1234567890123456-abcdef...
MERCADOLIVRE_REFRESH_TOKEN=TGRT-1234567890123456-ghijkl...
```

---

## Passo 7: Testar a API

```bash
curl -X GET "https://api.mercadolivre.com/users/me" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

---

## Resumo das Credenciais

| Credencial | Onde Obter | Validade | Uso |
|------------|------------|----------|-----|
| **App ID** | Portal Developers | Permanente | Identificar aplicação |
| **Secret Key** | Portal Developers | Permanente | Autenticar aplicação |
| **Access Token** | OAuth Flow | 6 horas | Fazer requisições |
| **Refresh Token** | OAuth Flow | 30 dias | Renovar Access Token |

---

## Links Úteis

- [Portal de Desenvolvedores](https://developers.mercadolivre.com.br/)
- [Guia de Autenticação](https://developers.mercadolivre.com.br/pt_br/autenticacao-e-autorizacao)
- [Referência da API](https://developers.mercadolivre.com.br/en_us/)
- [Postman OAuth Helper](https://www.postman.com/)
