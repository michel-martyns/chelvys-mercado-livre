"""
Processamento de imagens para Mercado Livre
- Download
- Redimensionar (min 1000x1000)
- Remover fundo
- Otimizar
"""

import httpx
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple


class ImageProcessor:
    """Processador de imagens"""

    MIN_SIZE = 1000  # Tamanho mínimo exigido pelo ML

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def download_imagem(self, url: str) -> Optional[bytes]:
        """Download da imagem"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Erro no download: {e}")
            return None

    def processar_imagem(self, imagem_bytes: bytes) -> Tuple[bytes, Tuple[int, int]]:
        """
        Processar imagem:
        - Redimensionar se necessário (min 1000x1000)
        - Converter para RGB
        - Otimizar qualidade

        Returns:
            (imagem_bytes, (largura, altura))
        """
        img = Image.open(BytesIO(imagem_bytes))

        # Converter para RGB (remover alpha channel se existir)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Criar fundo branco para imagens com transparência
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionar se necessário
        width, height = img.size

        if width < self.MIN_SIZE or height < self.MIN_SIZE:
            # Calcular nova mantendo aspect ratio
            scale = max(self.MIN_SIZE / width, self.MIN_SIZE / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Redimensionado de {width}x{height} para {new_width}x{new_height}")

        # Otimizar e salvar
        output = BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True)

        return output.getvalue(), img.size

    async def processar_url(self, url: str) -> Optional[Tuple[bytes, Tuple[int, int]]]:
        """Download e processamento de imagem por URL"""
        imagem_bytes = await self.download_imagem(url)
        if not imagem_bytes:
            return None

        return self.processar_imagem(imagem_bytes)

    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()
