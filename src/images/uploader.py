"""
Upload de imagens para Google Cloud Storage
Estrutura: mercado-livre/{nome-produto}/{imagem1, imagem2, ...}
"""

import os
import re
from pathlib import Path
from google.cloud import storage
from typing import Optional


class GCSUploader:
    """Upload de imagens para GCS"""

    def __init__(self, bucket_name: str, project_id: str):
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    def _normalizar_nome(self, nome: str) -> str:
        """
        Normalizar nome para padrão URL-safe
        Ex: "Fone Bluetooth TWS" -> "fone-bluetooth-tws"
        """
        # Converter para minúsculas
        nome = nome.lower()

        # Remover caracteres especiais
        nome = re.sub(r'[^\w\s-]', '', nome)

        # Substituir espaços por hífens
        nome = re.sub(r'[-\s]+', '-', nome)

        # Remover hífens extras no início/fim
        nome = nome.strip('-')

        return nome

    def _normalizar_imagem_nome(self, index: int, url_original: str) -> str:
        """
        Normalizar nome da imagem
        Ex: imagem1.jpg, imagem2.jpg, ...
        """
        # Extrair extensão da URL original
        ext = Path(url_original).suffix.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            ext = '.jpg'  # Default

        return f"imagem{index + 1}{ext}"

    def upload_imagem(self, imagem_bytes: bytes, produto_nome: str, index: int, url_original: str) -> Optional[str]:
        """
        Fazer upload de uma imagem

        Returns:
            URL pública da imagem ou None se falhar
        """
        try:
            # Normalizar nomes
            pasta_produto = self._normalizar_nome(produto_nome)
            nome_imagem = self._normalizar_imagem_nome(index, url_original)

            # Path no GCS: mercado-livre/{produto}/{imagem}
            blob_path = f"mercado-livre/{pasta_produto}/{nome_imagem}"

            # Criar blob e fazer upload
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(imagem_bytes, content_type='image/jpeg')

            # Tornar pública
            blob.make_public()

            # Retornar URL pública
            return blob.public_url

        except Exception as e:
            print(f"Erro ao fazer upload da imagem: {e}")
            return None

    def upload_imagens(self, imagens_bytes: list[bytes], produto_nome: str, urls_originais: list[str]) -> list[str]:
        """
        Fazer upload de múltiplas imagens

        Returns:
            Lista de URLs públicas
        """
        urls_publicas = []

        for i, (imagem_bytes, url_original) in enumerate(zip(imagens_bytes, urls_originais)):
            url_publica = self.upload_imagem(imagem_bytes, produto_nome, i, url_original)
            if url_publica:
                urls_publicas.append(url_publica)
                print(f"✓ Upload: {url_publica}")
            else:
                print(f"✗ Falha: {url_original}")

        return urls_publicas

    def deletar_imagens_produto(self, produto_nome: str):
        """Deletar todas as imagens de um produto"""
        try:
            pasta = self._normalizar_nome(produto_nome)
            prefix = f"mercado-livre/{pasta}/"

            blobs = self.bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blob.delete()

            print(f"Imagens de '{produto_nome}' deletadas")
        except Exception as e:
            print(f"Erro ao deletar imagens: {e}")


# Exemplo de uso
if __name__ == "__main__":
    uploader = GCSUploader(
        bucket_name="chelvys-ml-images",
        project_id="chelvys"
    )

    # Teste com nome de produto
    nome_teste = "Fone Bluetooth TWS Wireless"
    print(f"Normalizado: {uploader._normalizar_nome(nome_teste)}")
    # Output: fone-bluetooth-tws-wireless
