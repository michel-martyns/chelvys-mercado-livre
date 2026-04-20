"""
Pipeline completo: WeDrop → Processamento → Mercado Livre
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WEDROP_EMAIL = os.getenv("WEDROP_EMAIL")
WEDROP_PASSWORD = os.getenv("WEDROP_PASSWORD")
WEDROP_CATALOG_ID = os.getenv("WEDROP_CATALOG_ID", "32425")

ML_ACCESS_TOKEN = os.getenv("MERCADOLIVRE_ACCESS_TOKEN")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "chelvys")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "chelvys-ml-images")

# Markup e taxas
DEFAULT_MARKUP = float(os.getenv("DEFAULT_MARKUP", "1.3"))
ML_FEE_RATE = float(os.getenv("ML_FEE_RATE", "0.15"))


def calcular_preco_venda(preco_custo: float) -> float:
    """
    Calcular preço de venda considerando markup e taxas

    Fórmula: preco_venda = preco_custo * markup / (1 - taxa_ml)
    """
    preco_base = preco_custo * DEFAULT_MARKUP
    preco_venda = preco_base / (1 - ML_FEE_RATE)
    return round(preco_venda, 2)


async def main():
    """Pipeline principal"""

    print("=" * 60)
    print("Pipeline WeDrop → Mercado Livre")
    print("=" * 60)
    print(f"\nProduto: {WEDROP_CATALOG_ID}")
    print(f"Markup: {DEFAULT_MARKUP}x")
    print(f"Taxa ML: {ML_FEE_RATE * 100}%")
    print()

    # =====================
    # 1. Extração WeDrop
    # =====================
    print("[1/5] Extraindo dados da WeDrop...")

    try:
        from src.wedrop.extractor import WeDropExtractor, Produto

        extractor = WeDropExtractor(WEDROP_EMAIL, WEDROP_PASSWORD)

        # Login
        logged_in = await extractor.login()
        if not logged_in:
            print("⚠️ Falha no login WeDrop - tentando sem autenticação...")

        # Extrair produto
        produto = await extractor.extrair_produto(WEDROP_CATALOG_ID)

        if not produto:
            print("❌ Falha ao extrair produto")
            return

        print(f"✓ Produto: {produto.nome}")
        print(f"  Preço custo: R$ {produto.preco:.2f}")
        print(f"  Imagens: {len(produto.imagens)}")
        print(f"  Estoque: {produto.estoque}")

        await extractor.close()

    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        print("⚠️ Usando dados de exemplo para teste...")

        # Dados de exemplo para teste
        produto = Produto(
            id=WEDROP_CATALOG_ID,
            nome="Fone Bluetooth TWS Wireless Estéreo",
            preco=45.00,
            imagens=["https://exemplo.com/imagem1.jpg"],
            descricao="Fone de ouvido Bluetooth TWS com case carregador",
            sku=f"WD-{WEDROP_CATALOG_ID}",
            categoria="Eletrônicos",
            estoque=100,
            variacoes=[]
        )

    # =====================
    # 2. Processamento Imagens
    # =====================
    print("\n[2/5] Processando imagens...")

    try:
        from src.images.processor import ImageProcessor
        from src.images.uploader import GCSUploader

        processor = ImageProcessor()
        uploader = GCSUploader(GCS_BUCKET_NAME, GCP_PROJECT_ID)

        imagens_processadas = []
        urls_publicas = []

        for i, url in enumerate(produto.imagens[:6]):  # Max 6 imagens
            print(f"  Processando imagem {i + 1}...")

            resultado = await processor.processar_url(url)
            if resultado:
                imagem_bytes, tamanho = resultado
                imagens_processadas.append(imagem_bytes)
                print(f"    Tamanho: {tamanho[0]}x{tamanho[1]}")

        # Upload para GCS
        if imagens_processadas:
            print("  Fazendo upload para GCS...")
            urls_publicas = uploader.upload_imagens(
                imagens_processadas,
                produto.nome,
                produto.imagens[:len(imagens_processadas)]
            )
        else:
            # Usar URLs originais se não processou
            urls_publicas = produto.imagens[:6]

        await processor.close()

        print(f"✓ {len(urls_publicas)} imagens prontas")

    except Exception as e:
        print(f"⚠️ Erro no processamento: {e}")
        urls_publicas = produto.imagens[:6]

    # =====================
    # 3. Enriquecimento
    # =====================
    print("\n[3/5] Enriquecendo dados...")

    # Título otimizado
    titulo_enriquecido = f"{produto.nome} - Original com Garantia"

    # Descrição enriquecida
    descricao_enriquecida = f"""## {produto.nome}

### Características:
- Produto original e de qualidade
- Pronto para uso imediato
- Garantia do fornecedor

### Especificações:
- SKU: {produto.sku}
- Categoria: {produto.categoria}
- Peso: {produto.peso or 'Não informado'}
- Dimensões: {produto.dimensoes or 'Não informado'}

### Conteúdo da Embalagem:
- 1x {produto.nome}
- Manual de instruções
- Caixa original

---

**Envio imediato para todo o Brasil!**
"""

    # Calcular preço
    preco_custo = produto.preco
    preco_venda = calcular_preco_venda(preco_custo)

    print(f"  Título: {titulo_enriquecido[:50]}...")
    print(f"  Preço custo: R$ {preco_custo:.2f}")
    print(f"  Preço venda: R$ {preco_venda:.2f}")

    # =====================
    # 4. Publicação ML
    # =====================
    print("\n[4/5] Publicando no Mercado Livre...")

    try:
        import httpx

        # Preparar payload
        payload = {
            "title": titulo_enriquecido,
            "category_id": "MLB147982",  # Fones de ouvido (ajustar conforme categoria)
            "price": preco_venda,
            "currency_id": "BRL",
            "available_quantity": produto.estoque,
            "buying_mode": "buy_it_now",
            "condition": "new",
            "seller_custom_id": produto.sku,
            "pictures": [
                {"source": url} for url in urls_publicas
            ],
            "channels": ["marketplace", "mshops"],
            "attributes": [
                {"id": "BRAND", "value_name": "Genérico"},
                {"id": "ITEM_CONDITION", "value_name": "new"}
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Criar item
            response = await client.post(
                "https://api.mercadolibre.com/items",
                json=payload,
                headers={
                    "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 201:
                item_data = response.json()
                item_id = item_data.get("id")
                permalink = item_data.get("permalink")

                print(f"✓ Produto publicado!")
                print(f"  ID: {item_id}")
                print(f"  URL: {permalink}")

                # Adicionar descrição
                print("\n  Adicionando descrição...")
                desc_response = await client.post(
                    f"https://api.mercadolibre.com/items/{item_id}/description",
                    json={"plain_text": descricao_enriquecida},
                    headers={
                        "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )

                if desc_response.status_code == 201:
                    print("  ✓ Descrição adicionada")
                else:
                    print(f"  ⚠️ Erro na descrição: {desc_response.text}")

                # Salvar dados do produto
                produto_data = {
                    "wedrop_id": produto.id,
                    "ml_item_id": item_id,
                    "ml_permalink": permalink,
                    "preco_custo": preco_custo,
                    "preco_venda": preco_venda,
                    "estoque": produto.estoque,
                    "data_publicacao": datetime.now().isoformat(),
                    "status": "active"
                }

                # Salvar em arquivo
                data_dir = Path("data/processed")
                data_dir.mkdir(parents=True, exist_ok=True)

                with open(data_dir / f"{item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(produto_data, f, indent=2, ensure_ascii=False)

                print(f"\n✓ Dados salvos em {data_dir / f'{item_id}.json'}")

            else:
                print(f"❌ Erro na publicação: {response.status_code}")
                print(f"  {response.text}")

    except Exception as e:
        print(f"❌ Erro na publicação: {e}")

    # =====================
    # 5. Resumo
    # =====================
    print("\n" + "=" * 60)
    print("Resumo")
    print("=" * 60)
    print(f"Produto: {produto.nome}")
    print(f"Preço custo: R$ {preco_custo:.2f}")
    print(f"Preço venda: R$ {preco_venda:.2f}")
    print(f"Lucro estimado: R$ {(preco_venda - preco_custo):.2f}")
    print(f"Imagens: {len(urls_publicas)}")
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
