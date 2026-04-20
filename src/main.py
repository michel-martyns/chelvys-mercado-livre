# -*- coding: utf-8 -*-
"""
Pipeline completo: WeDrop -> Processamento -> Mercado Livre
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

# Carregar variaveis de ambiente
load_dotenv()

# Configuracoes
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
    Calcular preco de venda considerando markup e taxas

    Formula: preco_venda = preco_custo * markup / (1 - taxa_ml)
    """
    preco_base = preco_custo * DEFAULT_MARKUP
    preco_venda = preco_base / (1 - ML_FEE_RATE)
    return round(preco_venda, 2)


async def main():
    """Pipeline principal"""

    print("=" * 60)
    print("Pipeline WeDrop - Mercado Livre")
    print("=" * 60)
    print(f"\nProduto: {WEDROP_CATALOG_ID}")
    print(f"Markup: {DEFAULT_MARKUP}x")
    print(f"Taxa ML: {ML_FEE_RATE * 100}%")
    print()

    # =====================
    # 1. Extracao WeDrop
    # =====================
    print("[1/5] Extraindo dados da WeDrop...")

    try:
        from wedrop.extractor import WeDropExtractor, Produto

        extractor = WeDropExtractor(WEDROP_EMAIL, WEDROP_PASSWORD)

        # Login
        logged_in = await extractor.login()
        if not logged_in:
            print("[WARN] Falha no login WeDrop - tentando sem autenticação...")

        # Extrair produto
        produto = await extractor.extrair_produto(WEDROP_CATALOG_ID)

        if not produto:
            print("[ERRO] Falha ao extrair produto")
            return

        print(f"[OK] Produto: {produto.nome}")
        print(f"  Preco custo: R$ {produto.preco:.2f}")
        print(f"  Imagens: {len(produto.imagens)}")
        print(f"  Estoque: {produto.estoque}")

        await extractor.close()

    except Exception as e:
        print(f"[ERRO] Erro na extracao: {e}")
        print("[WARN] Usando dados de exemplo para teste...")

        # Dados de exemplo para teste
        from dataclasses import dataclass
        from typing import Optional, List

        @dataclass
        class Produto:
            id: str
            nome: str
            preco: float
            imagens: List[str]
            descricao: str
            sku: str
            categoria: str
            estoque: int
            variacoes: list
            peso: Optional[str] = None
            dimensoes: Optional[str] = None
            url: str = ""
            data_extracao: str = ""

        produto = Produto(
            id=WEDROP_CATALOG_ID,
            nome="Fone Bluetooth TWS Wireless Estereo",
            preco=45.00,
            imagens=["https://picsum.photos/seed/product1/800/800.jpg"],
            descricao="Fone de ouvido Bluetooth TWS com case carregador",
            sku=f"WD-{WEDROP_CATALOG_ID}",
            categoria="Eletronicos",
            estoque=100,
            variacoes=[]
        )

    # =====================
    # 2. Processamento Imagens
    # =====================
    print("\n[2/5] Processando imagens...")

    try:
        from images.processor import ImageProcessor
        from images.uploader import GCSUploader

        processor = ImageProcessor(use_ai_enhance=True)
        uploader = GCSUploader(GCS_BUCKET_NAME, GCP_PROJECT_ID)

        imagens_processadas = []
        urls_publicas = []

        for i, url in enumerate(produto.imagens[:6]):  # Max 6 imagens
            print(f"  Processando imagem {i + 1}...")

            resultado = await processor.processar_url(url)
            if resultado:
                imagem_bytes, tamanho, status = resultado
                imagens_processadas.append(imagem_bytes)
                print(f"    Tamanho: {tamanho[0]}x{tamanho[1]} - {status}")

        # Upload para GCS
        if imagens_processadas:
            print("  Fazendo upload para GCS...")
            urls_publicas = uploader.upload_imagens(
                imagens_processadas,
                produto.nome,
                produto.imagens[:len(imagens_processadas)]
            )
        else:
            # Usar URLs originais se nao processou
            urls_publicas = produto.imagens[:6]

        await processor.close()

        print(f"[OK] {len(urls_publicas)} imagens prontas")

    except Exception as e:
        print(f"[WARN] Erro no processamento: {e}")
        urls_publicas = produto.imagens[:6]

    # =====================
    # 3. Enriquecimento + Classificação LLM
    # =====================
    print("\n[3/5] Enriquecendo dados e classificando categoria...")

    try:
        from utils.llm_category import LLMCategoryClassifier

        classifier = LLMCategoryClassifier(use_llm=True)
        categoria_id, categoria_nome, confianca = await classifier.classify(
            produto.nome,
            produto.descricao
        )

        print(f"  Categoria: {categoria_nome} ({categoria_id})")
        print(f"  Confiança: {confianca:.0%}")

    except Exception as e:
        print(f"  [WARN] Erro na classificação LLM: {e}")
        categoria_id = "MLB147982"  # Fallback: Fones de ouvido
        categoria_nome = "Fones de Ouvido"

    # Titulo otimizado
    titulo_enriquecido = f"{produto.nome} - Original com Garantia"

    # Descricao enriquecida
    descricao_enriquecida = f"""## {produto.nome}

### Caracteristicas:
- Produto original e de qualidade
- Pronto para uso imediato
- Garantia do fornecedor

### Especificacoes:
- SKU: {produto.sku}
- Categoria: {categoria_nome}
- Peso: {produto.peso or 'Nao informado'}
- Dimensoes: {produto.dimensoes or 'Nao informado'}

### Conteudo da Embalagem:
- 1x {produto.nome}
- Manual de instrucoes
- Caixa original

---

**Envio imediato para todo o Brasil!**
"""

    # Calcular preco
    preco_custo = produto.preco
    preco_venda = calcular_preco_venda(preco_custo)

    print(f"  Titulo: {titulo_enriquecido[:50]}...")
    print(f"  Preco custo: R$ {preco_custo:.2f}")
    print(f"  Preco venda: R$ {preco_venda:.2f}")

    # =====================
    # 4. Publicacao ML
    # =====================
    print("\n[4/5] Publicando no Mercado Livre...")

    try:
        import httpx

        # Preparar payload (User Products model para seller com tag user_product_seller)
        payload = {
            "category_id": categoria_id,
            "family_name": produto.nome[:60],  # Nome da família (catálogo)
            "price": preco_venda,
            "currency_id": "BRL",
            "available_quantity": produto.estoque,
            "buying_mode": "buy_it_now",
            "condition": "new",
            "listing_type_id": "gold_special",
            "pictures": [
                {"source": url} for url in urls_publicas
            ],
            "attributes": [
                {"id": "BRAND", "value_name": "Generico"},
                {"id": "SELLER_PACKAGE_HEIGHT", "value_name": "5 cm"},
                {"id": "SELLER_PACKAGE_WIDTH", "value_name": "10 cm"},
                {"id": "SELLER_PACKAGE_LENGTH", "value_name": "12 cm"},
                {"id": "SELLER_PACKAGE_WEIGHT", "value_name": "150 g"}
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

                print(f"[OK] Produto publicado!")
                print(f"  ID: {item_id}")
                print(f"  URL: {permalink}")

                # Adicionar descricao
                print("\n  Adicionando descricao...")
                desc_response = await client.post(
                    f"https://api.mercadolibre.com/items/{item_id}/description",
                    json={"plain_text": descricao_enriquecida},
                    headers={
                        "Authorization": f"Bearer {ML_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )

                if desc_response.status_code == 201:
                    print("  [OK] Descricao adicionada")
                else:
                    print(f"  [WARN] Erro na descricao: {desc_response.text}")

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
                data_dir = Path(__file__).parent.parent / "data" / "processed"
                data_dir.mkdir(parents=True, exist_ok=True)

                with open(data_dir / f"{item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(produto_data, f, indent=2, ensure_ascii=False)

                print(f"\n[OK] Dados salvos em {data_dir / f'{item_id}.json'}")

            else:
                print(f"[ERRO] Erro na publicacao: {response.status_code}")
                print(f"  {response.text}")

    except Exception as e:
        print(f"[ERRO] Erro na publicacao: {e}")

    # =====================
    # 5. Resumo
    # =====================
    print("\n" + "=" * 60)
    print("Resumo")
    print("=" * 60)
    print(f"Produto: {produto.nome}")
    print(f"Preco custo: R$ {preco_custo:.2f}")
    print(f"Preco venda: R$ {preco_venda:.2f}")
    print(f"Lucro estimado: R$ {(preco_venda - preco_custo):.2f}")
    print(f"Imagens: {len(urls_publicas)}")
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
