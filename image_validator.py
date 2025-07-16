#!/usr/bin/env python3
"""
画像検証モジュール
画像ファイルの妥当性チェック
"""

from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageValidator:
    """画像検証クラス"""
    
    def __init__(self, max_size_mb: int = 10):
        """初期化"""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    def validate_image(self, image_path: str) -> bool:
        """画像ファイルの妥当性をチェック"""
        try:
            path = Path(image_path)
            
            # ファイル存在チェック
            if not path.exists():
                logger.error(f"ファイルが見つかりません: {image_path}")
                return False
            
            # ファイルサイズチェック
            file_size = path.stat().st_size
            if file_size > self.max_size_bytes:
                logger.error(f"ファイルサイズが大きすぎます（{self.max_size_bytes/1024/1024:.0f}MB超過）: {image_path}")
                return False
            
            # 拡張子チェック
            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"サポートされていない画像形式: {image_path}")
                return False
                
            # 画像形式チェック
            try:
                with Image.open(image_path) as img:
                    img.verify()
                logger.debug(f"画像検証OK: {image_path}")
                return True
            except Exception as e:
                logger.error(f"画像形式エラー: {image_path} - {e}")
                return False
                
        except Exception as e:
            logger.error(f"画像検証エラー: {image_path} - {e}")
            return False
    
    def get_valid_images(self, folder_path: str) -> list:
        """フォルダ内の有効な画像ファイル一覧を取得（ファイル名昇順）"""
        folder = Path(folder_path)
        
        if not folder.exists():
            logger.error(f"フォルダが見つかりません: {folder_path}")
            return []
        
        valid_images = []
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                if self.validate_image(str(file_path)):
                    valid_images.append(file_path)
        
        # ファイル名で昇順ソート
        valid_images.sort(key=lambda x: x.name.lower())
        
        logger.info(f"有効な画像ファイル: {len(valid_images)}個（ファイル名昇順）")
        return valid_images
