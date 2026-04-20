# -*- coding: utf-8 -*-
"""
Teste do Pipeline com produto real do Mercado Livre
Usa imagem de exemplo e publica no ML
"""

import os
import sys
import json
import httpx
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

ML_ACCESS_TOKEN = os.getenv("MERCADOLIVRE_ACCESS_TOKEN")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "chelvys")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "chelvys-ml-images")

# Produto de teste (dados mockados baseados no catalogo 32425)
PRODUTO_TESTE = {
    "id": "32425",
    "nome": "Fone de Ouvido Bluetooth TWS Wireless Estereo Hi-Fi",
    "preco_custo": 45.00,
    "categoria": "Fones de Ouvido",
    "categoria_id": "MLB147982",
    "estoque": 50,
    "sku": "WD-32425-TWS",
    # Imagem de exemplo (placeholder)
    "imagem_url": "https://picsum.photos/seed/tws-headphones/1000/1000.jpg"
}

MARKUP = 1.3
ML_FEE = 0.15


def calcular_preco(custo):
    return round((custo * MARKUP) / (1 - ML_FEE), 2)


async def testar_upload_imagem():
    """Testar upload de imagem para GCS"""
    from images.processor import ImageProcessor
    from images.uploader import GCSUploader

    print("\n" + "=" * 60)
    print("TESTE 1: Upload de Imagem para GCS")
    print("=" * 60)

    try:
        processor = ImageProcessor(use_ai_enhance=True)
        uploader = GCSUploader(GCS_BUCKET_NAME, GCP_PROJECT_ID)

        print(f"\nBaixando imagem: {PRODUTO_TESTE['imagem_url']}")
        resultado = await processor.processar_url(PRODUTO_TESTE["imagem_url"])

        if resultado:
            imagem_bytes, tamanho, status = resultado
            print(f"Imagem processada: {tamanho[0]}x{tamanho[1]} - {status}")

            print("\nFazendo upload para GCS...")
            urls = uploader.upload_imagens(
                [imagem_bytes],
                PRODUTO_TESTE["nome"],
                [PRODUTO_TESTE["imagem_url"]]
            )

            if urls:
                print(f"[OK] Upload concluido!")
                print(f"URL publica: {urls[0]}")
                await processor.close()
                return urls[0]

        await processor.close()
        return None

    except Exception as e:
        print(f"[ERRO] {e}")
        print("[INFO] Usando imagem direta do URL...")
        return PRODUTO_TESTE["imagem_url"]


async def testar_publicacao_ml(imagem_url: str):
    """Testar publicacao no Mercado Livre"""

    print("\n" + "=" * 60)
    print("TESTE 2: Publicacao no Mercado Livre")
    print("=" * 60)

    preco_venda = calcular_preco(PRODUTO_TESTE["preco_custo"])

    print(f"\nProduto: {PRODUTO_TESTE['nome']}")
    print(f"Preco custo: R$ {PRODUTO_TESTE['preco_custo']:.2f}")
    print(f"Preco venda: R$ {preco_venda:.2f}")
    print(f"Markup: {MARKUP}x | Taxa ML: {ML_FEE*100}%")
    print(f"Lucro estimado: R$ {(preco_venda - PRODUTO_TESTE['preco_custo']):.2f}")

    # Payload para API do ML (User Products model 2026)
    # Nota: User Products usa endpoint /user-products para criacao
    # Para teste, vamos usar o endpoint tradicional de items
    payload = {
        "title": PRODUTO_TESTE["nome"],
        "category_id": PRODUTO_TESTE["categoria_id"],
        "price": preco_venda,
        "currency_id": "BRL",
        "available_quantity": PRODUTO_TESTE["estoque"],
        "buying_mode": "buy_it_now",
        "condition": "new",
        "listing_type_id": "gold_special",  # Tipo de anuncio
        "pictures": [
            {"source": imagem_url}
        ],
        "attributes": [
            {"id": "BRAND", "value_name": "Generica"},
            {"id": "ITEM_CONDITION", "value_name": "new"},
            {"id": "MODEL", "value_name": "TWS Wireless"}
        ],
        "description": {
            "plain_text": f"""## {PRODUTO_TESTE['nome']}

### Caracteristicas Principais:
- Tecnologia Bluetooth 5.0 de ultima geracao
- Som estereo Hi-Fi de alta qualidade
- Design ergonomico e confortavel
- Case carregador portatil
- Compativel com Android e iOS

### Especificacoes Tecnicas:
- SKU: {PRODUTO_TESTE['sku']}
- Categoria: {PRODUTO_TESTE['categoria']}
- Condicao: Novo
- Marca: Generica
- Modelo: TWS Wireless

### Conteudo da Embalagem:
- 1x Fone de Ouvido TWS
- 1x Case Carregador
- 1x Cabo USB
- 1x Manual de Instrucoes

---

**ENVIO IMEDIATO PARA TODO O BRASIL!**
**GARANTIA DE 90 DIAS!**
"""
        }
    }

    print("\nEnviando para API do Mercado Livre...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Publicar item
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

                print(f"\n[SUCCESS] Produto publicado!")
                print(f"  Item ID: {item_id}")
                print(f"  Status: {status}")
                print(f"  URL: {permalink}")

                # Salvar dados
                dados = {
                    "wedrop_id": PRODUTO_TESTE["id"],
                    "ml_item_id": item_id,
                    "ml_permalink": permalink,
                    "ml_status": status,
                    "preco_custo": PRODUTO_TESTE["preco_custo"],
                    "preco_venda": preco_venda,
                    "estoque": PRODUTO_TESTE["estoque"],
                    "data_publicacao": datetime.now().isoformat()
                }

                output_dir = Path(__file__).parent.parent / "data" / "processed"
                output_dir.mkdir(parents=True, exist_ok=True)

                with open(output_dir / f"{item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=2, ensure_ascii=False)

                print(f"\nDados salvos em: {output_dir / f'{item_id}.json'}")

                return item_id

            else:
                print(f"\n[ERRO] {response.text}")
                return None

    except Exception as e:
        print(f"[ERRO] {e}")
        return None


async def main():
    """Pipeline de teste completo"""

    print("\n" + "=" * 60)
    print("PIPELINE DE TESTE - Produto 32425")
    print("=" * 60)

    # Teste 1: Upload imagem
    imagem_url = await testar_upload_imagem()

    if not imagem_url:
        print("\n[ERRO] Falha no processamento de imagens")
        return

    # Teste 2: Publicacao ML
    item_id = await testar_publicacao_ml(imagem_url)

    if item_id:
        print("\n" + "=" * 60)
        print("PIPELINE CONCLUIDO COM SUCESSO!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("PIPELINE FALHOU - Verifique os erros acima")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
