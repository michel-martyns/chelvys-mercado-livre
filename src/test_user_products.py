# -*- coding: utf-8 -*-
"""
Teste com User Products API (modelo 2026)
Para vendedores com tag 'user_product_seller'
"""

import os
import sys
import json
import httpx
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

ML_ACCESS_TOKEN = os.getenv("MERCADOLIVRE_ACCESS_TOKEN")

# Produto de teste
PRODUTO = {
    "id": "32425",
    "nome": "Fone de Ouvido Bluetooth TWS Wireless Estereo Hi-Fi",
    "family_name": "Fone TWS Wireless Estereo",  # Nome da familia
    "preco_custo": 45.00,
    "categoria_id": "MLB147982",
    "estoque": 50,
    "sku": "WD-32425-TWS",
    "imagem_url": "https://picsum.photos/seed/tws-headphones/1000/1000.jpg"
}

MARKUP = 1.3
ML_FEE = 0.15


def calcular_preco(custo):
    return round((custo * MARKUP) / (1 - ML_FEE), 2)


async def criar_user_product():
    """
    Criar User Product (modelo 2026 para vendedores habilitados)
    Endpoint: POST /user-products
    """

    preco_venda = calcular_preco(PRODUTO["preco_custo"])

    print("=" * 60)
    print("CRIACAO DE USER PRODUCT (API 2026)")
    print("=" * 60)

    print(f"\nProduto: {PRODUTO['nome']}")
    print(f"Family Name: {PRODUTO['family_name']}")
    print(f"Preco custo: R$ {PRODUTO['preco_custo']:.2f}")
    print(f"Preco venda: R$ {preco_venda:.2f}")
    print(f"Lucro estimado: R$ {(preco_venda - PRODUTO['preco_custo']):.2f}")

    # Payload para User Products API
    payload = {
        "family_name": PRODUTO["family_name"],
        "category_id": PRODUTO["categoria_id"],
        "price": preco_venda,
        "currency_id": "BRL",
        "available_quantity": PRODUTO["estoque"],
        "buying_mode": "buy_it_now",
        "condition": "new",
        "seller_custom_id": PRODUTO["sku"],
        "listing_type_id": "gold_special",
        "pictures": [
            {"source": PRODUTO["imagem_url"]}
        ],
        "attributes": [
            {"id": "BRAND", "value_name": "Generica"},
            {"id": "ITEM_CONDITION", "value_name": "new"},
            {"id": "MODEL", "value_name": "TWS Wireless"}
        ]
    }

    print("\nEnviando para API (/user-products)...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # User Products endpoint
            response = await client.post(
                "https://api.mercadolibre.com/user-products",
                json=payload,
                headers={
                    "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                item_id = data.get("id")
                permalink = data.get("permalink")
                status = data.get("status")

                print(f"\n[SUCCESS] User Product criado!")
                print(f"  Item ID: {item_id}")
                print(f"  Status: {status}")
                print(f"  URL: {permalink}")

                # Salvar dados
                dados = {
                    "wedrop_id": PRODUTO["id"],
                    "ml_item_id": item_id,
                    "ml_permalink": permalink,
                    "ml_status": status,
                    "tipo": "user_product",
                    "family_name": PRODUTO["family_name"],
                    "preco_custo": PRODUTO["preco_custo"],
                    "preco_venda": preco_venda,
                    "estoque": PRODUTO["estoque"],
                    "data_publicacao": datetime.now().isoformat()
                }

                output_dir = Path(__file__).parent.parent / "data" / "processed"
                output_dir.mkdir(parents=True, exist_ok=True)

                with open(output_dir / f"{item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=2, ensure_ascii=False)

                print(f"\nDados salvos em: {output_dir / f'{item_id}.json'}")

                return item_id

            else:
                erro = response.json()
                print(f"\n[ERRO] {response.status_code}")
                print(f"  Mensagem: {erro.get('message', 'N/A')}")
                print(f"  Causa: {json.dumps(erro.get('cause', []), indent=2)}")

                # Tentar fallback para items tradicionais
                if "family_name" in str(erro):
                    print("\n[TENTANDO FALLBACK PARA ITEMS TRADICIONAL]")
                    return await criar_item_tradicional()

                return None

    except Exception as e:
        print(f"[ERRO] {e}")
        return None


async def criar_item_tradicional():
    """
    Fallback: Criar item tradicional (para vendedores nao habilitados no User Products)
    Endpoint: POST /items
    """

    preco_venda = calcular_preco(PRODUTO["preco_custo"])

    print("\n" + "=" * 60)
    print("FALLBACK: ITEMS TRADICIONAL")
    print("=" * 60)

    payload = {
        "title": PRODUTO["nome"],
        "category_id": PRODUTO["categoria_id"],
        "price": preco_venda,
        "currency_id": "BRL",
        "available_quantity": PRODUTO["estoque"],
        "buying_mode": "buy_it_now",
        "condition": "new",
        "listing_type_id": "gold_special",
        "pictures": [
            {"source": PRODUTO["imagem_url"]}
        ],
        "attributes": [
            {"id": "BRAND", "value_name": "Generica"},
            {"id": "ITEM_CONDITION", "value_name": "new"}
        ]
    }

    print("\nEnviando para API (/items)...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.mercadolibre.com/items",
                json=payload,
                headers={
                    "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code == 201:
                data = response.json()
                item_id = data.get("id")
                permalink = data.get("permalink")
                status = data.get("status")

                print(f"\n[SUCCESS] Item tradicional criado!")
                print(f"  Item ID: {item_id}")
                print(f"  Status: {status}")
                print(f"  URL: {permalink}")

                # Adicionar descricao
                descricao = f"""## {PRODUTO['nome']}

### Caracteristicas:
- Produto original com garantia
- Envio imediato para todo Brasil

### Especificacoes:
- SKU: {PRODUTO['sku']}
- Condicao: Novo
- Marca: Generica
"""

                desc_resp = await client.post(
                    f"https://api.mercadolibre.com/items/{item_id}/description",
                    json={"plain_text": descricao},
                    headers={"Authorization": f"Bearer {ML_ACCESS_TOKEN}"}
                )

                if desc_resp.status_code == 201:
                    print("  [OK] Descricao adicionada")

                return item_id

            else:
                print(f"\n[ERRO] {response.text}")
                return None

    except Exception as e:
        print(f"[ERRO] {e}")
        return None


async def main():
    """Teste completo"""
    print("\n" + "=" * 60)
    print("TESTE USER PRODUCTS API - Produto 32425")
    print("=" * 60)

    # Tentar User Products primeiro
    item_id = await criar_user_product()

    if item_id:
        print("\n" + "=" * 60)
        print("SUCESSO! Produto publicado")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("FALHA - Verifique os erros acima")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
