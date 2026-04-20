# -*- coding: utf-8 -*-
"""
LLM para classificação de categorias do Mercado Livre

Usa modelo de linguagem para interpretar nome do produto WeDrop
e mapear para categoria MLB (Mercado Livre Brasil) correta.
"""

import os
import json
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Categorias principais do MLB (mapeamento manual)
CATEGORIAS_MLB = {
    # Eletrônicos
    "MLB1000": "Eletrônicos, Áudio e Vídeo",
    "MLB1002": "Áudio",
    "MLB147982": "Fones de Ouvido",
    "MLB1719": "Celulares e Smartphones",
    "MLB1051": "Celulares e Telefones",

    # Casa e Decoração
    "MLB1574": "Casa, Móveis e Decoração",
    "MLB1702": "Eletrodomésticos",

    # Veículos
    "MLB5672": "Acessórios para Veículos",
    "MLB1743": "Carros, Motos e Outros",

    # Esportes
    "MLB1276": "Esportes e Fitness",

    # Brinquedos
    "MLB1132": "Brinquedos e Hobbies",

    # Beleza
    "MLB1246": "Beleza e Cuidado Pessoal",

    # Moda
    "MLB1430": "Calçados, Roupas e Bolsas",

    # Agro
    "MLB271599": "Agro",

    # Animais
    "MLB1071": "Animais",
}

# Mapeamento de palavras-chave para categorias
KEYWORD_MAPPING = {
    "fone": "MLB147982",
    "headphone": "MLB147982",
    "earphone": "MLB147982",
    "tws": "MLB147982",
    "bluetooth": "MLB147982",
    "áudio": "MLB1002",
    "audio": "MLB1002",
    "caixa de som": "MLB1002",
    "speaker": "MLB1002",
    "microfone": "MLB1002",

    "celular": "MLB1719",
    "smartphone": "MLB1719",
    "iphone": "MLB1719",
    "samsung": "MLB1719",
    "xiaomi": "MLB1719",

    "tablet": "MLB1051",
    "ipad": "MLB1051",

    "smartwatch": "MLB1051",
    "relógio": "MLB1430",
    "relogio": "MLB1430",

    "notebook": "MLB1000",
    "laptop": "MLB1000",
    "computador": "MLB1000",
    "pc": "MLB1000",

    "tv": "MLB1000",
    "televisão": "MLB1000",
    "televisao": "MLB1000",

    "geladeira": "MLB1702",
    "geladeiro": "MLB1702",
    "fogão": "MLB1702",
    "fogao": "MLB1702",
    "microondas": "MLB1702",
    "lava": "MLB1702",
    "secadora": "MLB1702",

    "sofá": "MLB1574",
    "sofa": "MLB1574",
    "cadeira": "MLB1574",
    "mesa": "MLB1574",
    "cama": "MLB1574",
    "colchão": "MLB1574",
    "colchao": "MLB1574",

    "tênis": "MLB1430",
    "tenis": "MLB1430",
    "roupa": "MLB1430",
    "vestido": "MLB1430",
    "camisa": "MLB1430",
    "calça": "MLB1430",
    "calca": "MLB1430",

    "brinquedo": "MLB1132",
    "jogo": "MLB1132",
    "boneca": "MLB1132",
    "lego": "MLB1132",

    "maquiagem": "MLB1246",
    "cosmético": "MLB1246",
    "cosmetico": "MLB1246",
    "perfume": "MLB1246",
    "creme": "MLB1246",

    "ferramenta": "MLB263532",
    "furadeira": "MLB263532",
    "martelo": "MLB263532",

    "pet": "MLB1071",
    "cachorro": "MLB1071",
    "gato": "MLB1071",
    "ração": "MLB1071",
    "racao": "MLB1071",

    "trator": "MLB271599",
    "agricultura": "MLB271599",
    "semente": "MLB271599",
}


class LLMCategoryClassifier:
    """
    Classificador de categorias usando LLM (Anthropic Claude)

    Fluxo:
    1. Tenta matching por palavras-chave (rápido, gratuito)
    2. Se ambíguo, usa LLM para interpretação semântica
    3. Retorna categoria MLB + confiança
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def classify_keyword(self, produto_nome: str) -> Optional[Tuple[str, str, float]]:
        """
        Classificação por palavras-chave (fallback rápido)

        Returns:
            (category_id, category_name, confidence) ou None
        """
        nome_lower = produto_nome.lower()

        # Buscar melhor match
        best_match = None
        best_score = 0

        for keyword, category_id in KEYWORD_MAPPING.items():
            if keyword in nome_lower:
                # Score baseado no tamanho da keyword (mais específica = maior score)
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = (category_id, CATEGORIAS_MLB.get(category_id, "Desconhecida"))

        if best_match:
            # Confiança baseada no score (normalizado)
            confidence = min(0.9, best_score / 20)
            return (best_match[0], best_match[1], confidence)

        return None

    async def classify_with_llm(self, produto_nome: str, descricao: str = "") -> Optional[Tuple[str, str, float]]:
        """
        Classificação usando Anthropic Claude

        Returns:
            (category_id, category_name, confidence)
        """
        if not self.api_key:
            print("  [WARN] ANTHROPIC_API_KEY não configurada - usando fallback keyword")
            return self.classify_keyword(produto_nome)

        try:
            import anthropic

            client = anthropic.AsyncClient(api_key=self.api_key)

            prompt = f"""
Classifique este produto do Mercado Livre Brasil na categoria correta.

Produto:
Nome: {produto_nome}
Descrição: {descricao or "N/A"}

Categorias disponíveis:
{json.dumps(CATEGORIAS_MLB, indent=2, ensure_ascii=False)}

Responda APENAS no formato JSON:
{{
    "category_id": "MLBXXXXX",
    "category_name": "Nome da Categoria",
    "confidence": 0.85,
    "reasoning": "Breve explicação do porquê"
}}
"""

            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse da resposta
            response_text = response.content[0].text
            result = json.loads(response_text)

            return (
                result.get("category_id"),
                result.get("category_name"),
                result.get("confidence", 0.5)
            )

        except Exception as e:
            print(f"  [WARN] Erro LLM: {e} - usando fallback keyword")
            return self.classify_keyword(produto_nome)

    async def classify(self, produto_nome: str, descricao: str = "") -> Tuple[str, str, float]:
        """
        Classificação principal (keyword primeiro, LLM se necessário)

        Returns:
            (category_id, category_name, confidence)
        """
        print(f"  Classificando: {produto_nome[:50]}...")

        # Tentar keyword primeiro (rápido)
        keyword_result = self.classify_keyword(produto_nome)

        if keyword_result and keyword_result[2] > 0.7:
            # Alta confiança no keyword matching
            print(f"  [OK] Keyword match: {keyword_result[1]} (confiança: {keyword_result[2]:.0%})")
            return keyword_result

        # Se confiança baixa ou nenhum match, usar LLM
        if self.use_llm:
            print(f"  [LLM] Confiança baixa ({keyword_result[2]:.0%} se houver), usando LLM...")
            llm_result = await self.classify_with_llm(produto_nome, descricao)
            if llm_result:
                print(f"  [OK] LLM classification: {llm_result[1]} (confiança: {llm_result[2]:.0%})")
                return llm_result

        # Fallback final
        if keyword_result:
            print(f"  [FALLBACK] Usando keyword: {keyword_result[1]}")
            return keyword_result

        # Categoria genérica
        print(f"  [WARN] Sem match - usando genérica MLB1000")
        return ("MLB1000", "Eletrônicos, Áudio e Vídeo", 0.3)


# Exemplo de uso
async def main():
    classifier = LLMCategoryClassifier(use_llm=True)

    # Testes
    produtos = [
        ("Fone de Ouvido Bluetooth TWS Wireless", "Fone com case carregador"),
        ("Smartphone Samsung Galaxy S24", "Celular 5G 256GB"),
        ("Cadeira Gamer Ergonômica", "Cadeira para escritório"),
        ("Geladeira Frost Free Duplex", "Eletrodoméstico de cozinha"),
    ]

    for nome, desc in produtos:
        print(f"\n{'='*50}")
        result = await classifier.classify(nome, desc)
        print(f"Resultado: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
