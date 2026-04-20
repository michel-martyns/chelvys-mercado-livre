"""
OAuth Callback Handler for Mercado Livre
Deployed on Google Cloud Run to receive OAuth redirects
"""

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ML OAuth Callback")

# Configurações
APP_ID = os.getenv("MERCADOLIVRE_APP_ID")
SECRET_KEY = os.getenv("MERCADOLIVRE_SECRET_KEY")
REDIRECT_URI = os.getenv("CLOUD_RUN_URL", "https://oauth-callback-*.a.run.app/callback")


@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """Recebe o código de autorização do Mercado Livre"""
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(f"""
        <html>
            <head><title>Erro - OAuth</title></head>
            <body style="font-family: Arial; padding: 40px;">
                <h1 style="color: #e74c3c;">❌ Erro na Autorização</h1>
                <p><strong>Erro:</strong> {error}</p>
                <p><strong>Descrição:</strong> {request.query_params.get('error_description', 'N/A')}</p>
            </body>
        </html>
        """)

    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização não recebido")

    # Trocar código pelo access token
    token_url = "https://api.mercadolivre.com/oauth/token"
    payload = {
        "client_id": APP_ID,
        "client_secret": SECRET_KEY,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=payload)

    if response.status_code != 200:
        return HTMLResponse(f"""
        <html>
            <head><title>Erro - Token</title></head>
            <body style="font-family: Arial; padding: 40px;">
                <h1 style="color: #e74c3c;">❌ Erro ao Obter Token</h1>
                <p><strong>Status:</strong> {response.status_code}</p>
                <pre>{response.text}</pre>
            </body>
        </html>
        """)

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    user_id = token_data.get("user_id")
    expires_in = token_data.get("expires_in", 21600)

    # Salvar tokens em arquivo (em produção, usar Secret Manager)
    env_file = ".env_tokens"
    with open(env_file, "w") as f:
        f.write(f"MERCADOLIVRE_ACCESS_TOKEN={access_token}\n")
        f.write(f"MERCADOLIVRE_REFRESH_TOKEN={refresh_token}\n")
        f.write(f"MERCADOLIVRE_USER_ID={user_id}\n")
        f.write(f"MERCADOLIVRE_EXPIRES_IN={expires_in}\n")

    return HTMLResponse(f"""
    <html>
        <head><title>Sucesso - OAuth</title></head>
        <body style="font-family: Arial; padding: 40px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #27ae60;">✅ Sucesso!</h1>
                <p>Tokens obtidos e salvos em <code>.env_tokens</code></p>

                <h3>Resumo:</h3>
                <ul>
                    <li><strong>User ID:</strong> {user_id}</li>
                    <li><strong>Access Token:</strong> <code>{access_token[:20]}...</code></li>
                    <li><strong>Refresh Token:</strong> <code>{refresh_token[:20]}...</code></li>
                    <li><strong>Expira em:</strong> {expires_in // 3600} horas</li>
                </ul>

                <h3>Próximos passos:</h3>
                <ol>
                    <li>Copie os tokens do arquivo <code>.env_tokens</code></li>
                    <li>Cole no arquivo <code>.env</code> principal</li>
                    <li>Teste a API com: <code>curl -H "Authorization: Bearer {access_token}" https://api.mercadolivre.com/users/me</code></li>
                </ol>

                <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                    ⚠️ O Access Token expira em {expires_in // 3600} horas. Use o Refresh Token para renovar.
                </p>
            </div>
        </body>
    </html>
    """)


@app.get("/health")
async def health():
    """Health check para Cloud Run"""
    return {"status": "healthy"}


@app.get("/")
async def index():
    """Página inicial com instruções"""
    auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}"

    return HTMLResponse(f"""
    <html>
        <head><title>ML OAuth Handler</title></head>
        <body style="font-family: Arial; padding: 40px;">
            <h1>🔐 Mercado Livre OAuth Handler</h1>
            <p>Este serviço recebe o callback de autorização do Mercado Livre.</p>

            <h2>Iniciar Autorização:</h2>
            <a href="{auth_url}" style="display: inline-block; padding: 12px 24px; background: #3498db; color: white; text-decoration: none; border-radius: 4px;">
                Autorizar Aplicação
            </a>

            <h2>Endpoints:</h2>
            <ul>
                <li><code>GET /callback</code> - Recebe o código OAuth</li>
                <li><code>GET /health</code> - Health check</li>
            </ul>
        </body>
    </html>
    """)
