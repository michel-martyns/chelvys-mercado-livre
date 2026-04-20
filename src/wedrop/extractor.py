"""
Extractor para produtos WeDrop
Extrai informações de produtos do catálogo WeDrop
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Produto:
    """Modelo de produto WeDrop"""
    id: str
    nome: str
    preco: float
    imagens: list[str]
    descricao: str
    sku: str
    categoria: str
    estoque: int
    variacoes: list[dict]
    peso: Optional[str] = None
    dimensoes: Optional[str] = None
    url: str = ""
    data_extracao: str = ""


class WeDropExtractor:
    """Extractor de produtos WeDrop"""

    BASE_URL = "https://dash.wedrop.com.br"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        self.authenticated = False

    async def login(self) -> bool:
        """Fazer login na WeDrop"""
        try:
            # Primeiro acesso para pegar cookies e tokens
            response = await self.client.get("/catalog/32425")

            # Tentar login (ajustar endpoint conforme necessário)
            # Nota: O endpoint exato de login precisa ser inspecionado no site
            login_data = {
                "email": self.email,
                "password": self.password
            }

            # Simular form submission (pode precisar de ajustes)
            response = await self.client.post(
                "/login",
                data=login_data
            )

            if response.status_code == 200:
                self.authenticated = True
                return True

            return False

        except Exception as e:
            print(f"Erro no login: {e}")
            return False

    async def extrair_produto(self, produto_id: str) -> Optional[Produto]:
        """Extrair dados de um produto específico"""

        url = f"/catalog/{produto_id}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extrair nome
            nome = self._extrair_elemento(soup, 'h1') or \
                   self._extrair_elemento(soup, '[itemprop="name"]') or \
                   soup.find('title').text if soup.find('title') else ""

            # Extrair preço
            preco = self._extrair_preco(soup)

            # Extrair imagens
            imagens = self._extrair_imagens(soup)

            # Extrair descrição
            descricao = self._extrair_descricao(soup)

            # Extrair SKU
            sku = self._extrair_sku(soup)

            # Extrair categoria
            categoria = self._extrair_categoria(soup)

            # Extrair estoque
            estoque = self._extrair_estoque(soup)

            # Extrair variações
            variacoes = self._extrair_variacoes(soup)

            # Extrair peso e dimensões
            peso = self._extrair_peso(soup)
            dimensoes = self._extrair_dimensoes(soup)

            produto = Produto(
                id=produto_id,
                nome=nome.strip(),
                preco=preco,
                imagens=imagens,
                descricao=descricao,
                sku=sku,
                categoria=categoria,
                estoque=estoque,
                variacoes=variacoes,
                peso=peso,
                dimensoes=dimensoes,
                url=f"{self.BASE_URL}{url}",
                data_extracao=datetime.now().isoformat()
            )

            return produto

        except Exception as e:
            print(f"Erro ao extrair produto {produto_id}: {e}")
            return None

    def _extrair_elemento(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extrair texto de um elemento"""
        try:
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else None
        except:
            return None

    def _extrair_preco(self, soup: BeautifulSoup) -> float:
        """Extrair preço do produto"""
        try:
            # Tentar vários seletores comuns
            selectors = [
                '[data-price]',
                '.price',
                '.product-price',
                '[itemprop="price"]',
                'span:contains("R$")'
            ]

            for selector in selectors:
                try:
                    el = soup.select_one(selector)
                    if el:
                        # Pegar atributo data-price ou texto
                        preco_str = el.get('data-price') or el.get_text(strip=True)
                        # Limpar e converter
                        preco_str = preco_str.replace('R$', '').replace('.', '').replace(',', '.')
                        return float(preco_str.strip())
                except:
                    continue

            return 0.0
        except:
            return 0.0

    def _extrair_imagens(self, soup: BeautifulSoup) -> list[str]:
        """Extrair URLs das imagens"""
        imagens = []
        try:
            # Galeria de imagens
            img_elements = soup.select('.product-image img, .gallery img, [itemprop="image"]')

            for img in img_elements:
                src = img.get('data-src') or img.get('src')
                if src and src.startswith('http'):
                    imagens.append(src)

            # Se não encontrou, tentar pegar a imagem principal
            if not imagens:
                main_img = soup.select_one('.main-image img, .product-primary-image img')
                if main_img:
                    src = main_img.get('data-src') or main_img.get('src')
                    if src:
                        imagens.append(src)

        except Exception as e:
            print(f"Erro ao extrair imagens: {e}")

        return imagens

    def _extrair_descricao(self, soup: BeautifulSoup) -> str:
        """Extrair descrição do produto"""
        try:
            desc_div = soup.select_one('.product-description, .description, [itemprop="description"]')
            if desc_div:
                return desc_div.get_text(separator='\n', strip=True)
            return ""
        except:
            return ""

    def _extrair_sku(self, soup: BeautifulSoup) -> str:
        """Extrair SKU do produto"""
        try:
            sku_el = soup.select_one('.sku, [itemprop="sku"], .product-sku')
            if sku_el:
                return sku_el.get_text(strip=True)
            return ""
        except:
            return ""

    def _extrair_categoria(self, soup: BeautifulSoup) -> str:
        """Extrair categoria do produto"""
        try:
            cat_el = soup.select_one('.category, .breadcrumb li:last-child, [itemprop="category"]')
            if cat_el:
                return cat_el.get_text(strip=True)
            return ""
        except:
            return ""

    def _extrair_estoque(self, soup: BeautifulSoup) -> int:
        """Extrair quantidade em estoque"""
        try:
            estoque_el = soup.select_one('.stock, .availability, .quantity-available')
            if estoque_el:
                texto = estoque_el.get_text(strip=True).lower()
                if 'esgotado' in texto or 'sem estoque' in texto:
                    return 0
                # Tentar extrair número
                import re
                match = re.search(r'\d+', texto)
                if match:
                    return int(match.group())
            return 100  # Default se não encontrou
        except:
            return 100

    def _extrair_variacoes(self, soup: BeautifulSoup) -> list[dict]:
        """Extrair variações (cores, tamanhos)"""
        variacoes = []
        try:
            # Cores
            cores = soup.select('.color-option, .variation-color')
            for cor in cores:
                variacoes.append({
                    'tipo': 'cor',
                    'nome': cor.get('data-name') or cor.get_text(strip=True),
                    'disponivel': 'disabled' not in cor.get('class', [])
                })

            # Tamanhos
            tamanhos = soup.select('.size-option, .variation-size')
            for tam in tamanhos:
                variacoes.append({
                    'tipo': 'tamanho',
                    'nome': tam.get('data-name') or tam.get_text(strip=True),
                    'disponivel': 'disabled' not in tam.get('class', [])
                })

        except Exception as e:
            print(f"Erro ao extrair variações: {e}")

        return variacoes

    def _extrair_peso(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrair peso do produto"""
        try:
            peso_el = soup.select_one('.weight, .product-weight')
            if peso_el:
                return peso_el.get_text(strip=True)
            return None
        except:
            return None

    def _extrair_dimensoes(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrair dimensões do produto"""
        try:
            dim_el = soup.select_one('.dimensions, .product-dimensions')
            if dim_el:
                return dim_el.get_text(strip=True)
            return None
        except:
            return None

    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()
