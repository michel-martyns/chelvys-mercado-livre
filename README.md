# Chelvys - Mercado Livre Automação

Sistema de automação para publicação de produtos WeDrop no Mercado Livre.

## Visão Geral

Este projeto automatiza o fluxo completo de:

1. **Extração** de produtos do catálogo WeDrop (dropshipping)
2. **Enriquecimento** de dados com IA (títulos, descrições, atributos)
3. **Processamento** de imagens (redimensionar, remover fundo, otimizar)
4. **Publicação** automática no Mercado Livre via API

## Estrutura do Projeto

```
chelvys-mercado-livre/
├── docs/                      # Documentação
│   ├── API_PUBLICACAO.md      # API do Mercado Livre
│   ├── FLUXO_PROCESSAMENTO.md # Fluxo WeDrop → ML
│   └── SETUP_MERCADO_LIVRE.md # Setup das credenciais
├── src/                       # Código fonte (a implementar)
├── data/                      # Dados processados
├── .env                       # Credenciais (NÃO COMMITAR)
├── .env.example               # Exemplo de .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Credenciais Configuradas

| Serviço | Status |
|---------|--------|
| WeDrop | ✅ Configurado |
| Mercado Livre API | ✅ App ID e Secret Key salvos |
| Google Cloud | ✅ Service Account configurada |

## Links Úteis

- [WeDrop Dashboard](https://dash.wedrop.com.br/)
- [Catálogo Configurado (32425)](https://dash.wedrop.com.br/catalog/32425)
- [Mercado Livre Developers](https://developers.mercadolivre.com.br/)
- [Google Cloud Console](https://console.cloud.google.com/)

## Próximos Passos

1. Configurar OAuth callback no Cloud Run
2. Obter Access Token do Mercado Livre
3. Implementar extractor WeDrop
4. Implementar pipeline de publicação

## Ambiente

```bash
# Instalar dependências
pip install -r requirements.txt

# Copiar exemplo de .env
cp .env.example .env

# Editar .env com suas credenciais
```
