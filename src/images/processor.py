"""
Processamento de imagens para Mercado Livre
Padrões atualizados 2026:
- Tamanho: 1200x1200 (ideal para zoom)
- Formato: JPG/PNG
- Modo: RGB
- Fundo: Branco/neutro
- Peso: < 2MB (ideal 500KB)
- Quantidade: até 10 imagens
"""

import httpx
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from typing import Optional, Tuple
import base64


class ImageProcessor:
    """
    Processador de imagens com IA para Mercado Livre

    Padrões ML 2026:
    - 1200x1200 pixels (ativo zoom)
    - RGB, 72 DPI
    - JPG/PNG, < 10MB
    - Sem marca d'água
    """

    TARGET_SIZE = 1200  # Tamanho ideal para zoom no ML
    MIN_SIZE = 500      # Mínimo absoluto
    MAX_SIZE = 1920     # Máximo permitido
    QUALITY = 85        # Qualidade JPG (balanceado)
    MAX_WEIGHT_MB = 2   # Peso máximo em MB

    def __init__(self, use_ai_enhance: bool = True):
        self.use_ai_enhance = use_ai_enhance
        self.client = httpx.AsyncClient(timeout=60.0)

    async def download_imagem(self, url: str) -> Optional[bytes]:
        """Download da imagem"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Erro no download: {e}")
            return None

    def _remove_fundo(self, img: Image.Image) -> Image.Image:
        """
        Remover fundo e substituir por branco
        Usa algoritmo de detecção de bordas + flood fill
        """
        try:
            # Converter para RGBA se necessário
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Obter dados dos pixels
            pixels = img.load()
            width, height = img.size

            # Detectar cor do canto (assume-se que é o fundo)
            corner_color = pixels[0, 0]

            # Tolerância para variação de cor
            tolerance = 30

            # Criar nova imagem com fundo branco
            white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))

            # Máscara para o produto
            mask = Image.new('L', img.size, 0)
            mask_pixels = mask.load()

            for y in range(height):
                for x in range(width):
                    pixel = pixels[x, y]
                    # Verificar se é diferente do fundo
                    if len(pixel) >= 3:
                        diff = sum(abs(pixel[i] - corner_color[i]) for i in range(min(3, len(pixel))))
                        if diff > tolerance:
                            mask_pixels[x, y] = 255

            # Composite do produto sobre fundo branco
            white_bg.paste(img, mask=mask)

            return white_bg.convert('RGB')

        except Exception as e:
            print(f"Erro na remoção de fundo: {e}")
            return img.convert('RGB') if img.mode != 'RGB' else img

    def _ai_enhance(self, img: Image.Image) -> Image.Image:
        """
        Aplicar melhorias com técnicas de IA/similares:
        - Sharpen (nitidez)
        - Contraste
        - Saturação
        - Brightness
        """
        # Nitidez (unsharp mask simulation)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

        # Contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)  # +15% contraste

        # Cor/ Saturação
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.1)  # +10% saturação

        # Brilho
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)  # +5% brilho

        return img

    def _upscale_ia(self, img: Image.Image, scale: float = 2.0) -> Image.Image:
        """
        Upscale usando algoritmo ESRAN-like (Lanczos + enhancements)

        Nota: Para ESRGAN real, usar:
        - pip install realesrgan
        - from realesrgan import RealESRGANer

        Esta implementação usa uma aproximação com Lanczos + sharpen
        """
        if scale <= 1.0:
            return img

        # Upscale com Lanczos (melhor qualidade)
        new_size = (int(img.width * scale), int(img.height * scale))
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)

        # Aplicar sharpen para compensar blur do resize
        upscaled = upscaled.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=5))

        return upscaled

    def processar_imagem(self, imagem_bytes: bytes) -> Tuple[bytes, Tuple[int, int], str]:
        """
        Processar imagem seguindo padrões ML 2026:
        - Redimensionar para 1200x1200
        - Converter para RGB
        - Aplicar melhorias (IA-like)
        - Otimizar peso

        Returns:
            (imagem_bytes, (largura, altura), status)
        """
        img = Image.open(BytesIO(imagem_bytes))

        # Logs do original
        original_size = img.size
        original_mode = img.mode
        print(f"    Original: {original_size[0]}x{original_size[1]} ({original_mode})")

        # 1. Converter para RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            # Detectar e remover fundo transparente
            if img.mode == 'RGBA':
                # Verificar se tem transparência significativa
                alpha = img.split()[-1]
                if alpha.getbbox() is None or alpha.getextrema()[0] < 255:
                    img = self._remove_fundo(img)
                else:
                    img = img.convert('RGB')
            else:
                img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 2. Redimensionar para o tamanho ideal
        width, height = img.size

        if width < self.MIN_SIZE or height < self.MIN_SIZE:
            # Precisa de upscale
            scale = max(self.TARGET_SIZE / width, self.TARGET_SIZE / height)
            if scale > 1.0 and self.use_ai_enhance:
                print(f"    AI Upscale: {scale:.1f}x")
                img = self._upscale_ia(img, scale)
            else:
                img = img.resize((self.TARGET_SIZE, self.TARGET_SIZE), Image.Resampling.LANCZOS)
        elif width > self.MAX_SIZE or height > self.MAX_SIZE:
            # Downscale
            scale = min(self.MAX_SIZE / width, self.MAX_SIZE / height)
            new_size = (int(width * scale), int(height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"    Downscale: {scale:.2f}x")
        else:
            # Está no range, ajustar para quadrado se necessário
            if width != height:
                # Crop central quadrado
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                img = img.crop((left, top, left + size, top + size))

        # 3. Aplicar melhorias (IA-like)
        if self.use_ai_enhance:
            print(f"    Aplicando AI enhancements...")
            img = self._ai_enhance(img)

        # 4. Garantir 1200x1200 final
        if img.size != (self.TARGET_SIZE, self.TARGET_SIZE):
            img = img.resize((self.TARGET_SIZE, self.TARGET_SIZE), Image.Resampling.LANCZOS)

        # 5. Otimizar e salvar
        output = BytesIO()
        img.save(output, format='JPEG', quality=self.QUALITY, optimize=True, progressive=True)

        # Verificar peso
        weight_mb = len(output.getvalue()) / (1024 * 1024)
        status = f"OK ({weight_mb:.2f}MB)"

        # Se muito pesado, reduzir qualidade
        while weight_mb > self.MAX_WEIGHT_MB and self.QUALITY > 50:
            output = BytesIO()
            self.QUALITY -= 5
            img.save(output, format='JPEG', quality=self.QUALITY, optimize=True)
            weight_mb = len(output.getvalue()) / (1024 * 1024)
            status = f"Comprimido ({weight_mb:.2f}MB, Q={self.QUALITY})"

        print(f"    Final: {img.size[0]}x{img.size[1]} - {status}")

        return output.getvalue(), img.size, status

    async def processar_url(self, url: str) -> Optional[Tuple[bytes, Tuple[int, int], str]]:
        """Download e processamento de imagem por URL"""
        imagem_bytes = await self.download_imagem(url)
        if not imagem_bytes:
            return None

        return self.processar_imagem(imagem_bytes)

    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()


# Exemplo de uso com ESRGAN real (opcional)
def setup_esrgan():
    """
    Configurar ESRGAN para upscaling real com IA

    pip install realesrgan-opencv
    """
    try:
        from realesrgan import RealESRGANer
        import cv2
        import numpy as np

        # Modelo pré-treinado
        model = RealESRGANer(
            scale=4,
            model_path='weights/RealESRGAN_x4plus.pth',
            model='RealESRGAN_x4plus',
            pre_pad=0,
            half=True,
            device=None
        )

        return model
    except ImportError:
        print("Real-ESRGAN não instalado. Use: pip install realesrgan")
        return None
