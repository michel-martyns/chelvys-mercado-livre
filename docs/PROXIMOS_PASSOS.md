# Próximos Passos - Configuração OAuth Mercado Livre

## Status Atual

✅ **Cloud Run Deployed:** https://ml-oauth-callback-783579532864.southamerica-east1.run.app

---

## Passo 1: Configurar Redirect URI no Mercado Livre

1. Acesse: https://applications.mercadolivre.com.br/
2. Selecione a aplicação **"Auto Publicador WeDrop"**
3. Vá em **"Redirect URIs"**
4. Adicione este URI:
   ```
   https://ml-oauth-callback-783579532864.southamerica-east1.run.app/callback
   ```
5. Clique em **Save**

---

## Passo 2: Iniciar Fluxo OAuth

### Opção A: Pelo Navegador (Recomendado)

1. Acesse no navegador:
   ```
   https://ml-oauth-callback-783579532864.southamerica-east1.run.app/
   ```

2. Clique em **"Autorizar Aplicação"**

3. Faça login no Mercado Livre

4. Autorize a aplicação

5. Será redirecionado de volta para o Cloud Run

6. Os tokens serão exibidos na página

### Opção B: URL Direta

Acesse diretamente:
```
https://auth.mercadolivre.com.br/authorization?response_type=code&client_id=2968420069553527&redirect_uri=https://ml-oauth-callback-783579532864.southamerica-east1.run.app/callback
```

---

## Passo 3: Copiar Tokens

Após autorizar, a página mostrará:

```
✅ Sucesso!
Tokens obtidos e salvos em .env_tokens

Resumo:
- User ID: 123456789
- Access Token: APP_USR-...
- Refresh Token: TGRT-...
- Expira em: 6 horas
```

**Copie o Access Token e Refresh Token**

---

## Passo 4: Atualizar .env

Edite o arquivo `.env` localmente:

```env
MERCADOLIVRE_ACCESS_TOKEN=APP_USR-xxxxxxxxxxxxx-xxxxxxxxxxxxxx
MERCADOLIVRE_REFRESH_TOKEN=TGRT-xxxxxxxxxxxxx-xxxxxxxxxxxxxx
```

---

## Passo 5: Testar API

```bash
# Teste simples
curl -X GET "https://api.mercadolivre.com/users/me" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

Resposta esperada:
```json
{
  "id": 123456789,
  "nickname": "seu_usuario",
  "email": "seu@email.com"
}
```

---

## Passo 6: Ver Logs do Cloud Run (Opcional)

```bash
# Ver logs em tempo real
gcloud run services logs tail ml-oauth-callback \
  --region southamerica-east1 \
  --project chelvys
```

---

## Refresh Token (Importante!)

O **Access Token expira em 6 horas**. Para renovar:

```bash
curl -X POST https://api.mercadolivre.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "2968420069553527",
    "client_secret": "lyKuvr5QcDGknAnxUksoOlKDBhaj8GRS",
    "grant_type": "refresh_token",
    "refresh_token": "SEU_REFRESH_TOKEN"
  }'
```

---

## Comandos Úteis

### Ver status do serviço
```bash
gcloud run services describe ml-oauth-callback \
  --region southamerica-east1 \
  --project chelvys
```

### Ver URL do serviço
```bash
gcloud run services describe ml-oauth-callback \
  --region southamerica-east1 \
  --format="value(status.url)"
```

### Deletar serviço (se necessário)
```bash
gcloud run services delete ml-oauth-callback \
  --region southamerica-east1 \
  --project chelvys
```

---

## Resumo das URLs

| Serviço | URL |
|---------|-----|
| Cloud Run (OAuth) | https://ml-oauth-callback-783579532864.southamerica-east1.run.app |
| Mercado Livre Apps | https://applications.mercadolivre.com.br/ |
| API ML (Teste) | https://api.mercadolivre.com/users/me |
