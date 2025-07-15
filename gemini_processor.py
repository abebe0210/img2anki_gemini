#!/usr/bin/env python3
"""
Gemini処理モジュール
Vertex AI Geminiを使用した画像解説生成
"""

import base64
import time
from pathlib import Path
from typing import Optional
import logging

# Vertex AI インポート
try:
    import vertexai
    try:
        from vertexai.preview.generative_models import GenerativeModel, Part
        VERTEX_AI_AVAILABLE = True
        VERTEX_AI_VERSION = "preview"
    except ImportError:
        try:
            from vertexai.generative_models import GenerativeModel, Part
            VERTEX_AI_AVAILABLE = True
            VERTEX_AI_VERSION = "new"
        except ImportError:
            VERTEX_AI_AVAILABLE = False
            VERTEX_AI_VERSION = None
except ImportError:
    VERTEX_AI_AVAILABLE = False
    VERTEX_AI_VERSION = None

import config
from image_validator import ImageValidator

logger = logging.getLogger(__name__)


class GeminiProcessor:
    """Gemini処理クラス"""
    
    def __init__(self, project_id: str, location: str, model_name: str):
        """初期化"""
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Vertex AI パッケージが利用できません")
        
        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(model_name)
        self.validator = ImageValidator()
        
        logger.info(f"Gemini初期化完了: {model_name} (バージョン: {VERTEX_AI_VERSION})")
    
    def generate_description(self, image_path: str, retry_count: Optional[int] = None) -> str:
        """Geminiを使用して画像の解説を生成"""
        if retry_count is None:
            retry_count = config.MAX_RETRY_COUNT
            
        for attempt in range(retry_count):
            try:
                logger.info(f"Gemini解説生成開始 (試行 {attempt + 1}/{retry_count}): {Path(image_path).name}")
                
                # 画像の検証とエンコード
                image_part = self._prepare_image_part(image_path)
                if not image_part:
                    return "画像の読み込みに失敗しました。"
                
                # Geminiに画像と共にプロンプトを送信
                response = self.model.generate_content([
                    config.PROMPT_TEMPLATE,
                    image_part
                ])
                
                if response.text:
                    logger.info(f"Gemini解説生成完了: {Path(image_path).name}")
                    return response.text.strip()
                else:
                    logger.warning(f"Geminiから空の応答: {Path(image_path).name}")
                    if attempt < retry_count - 1:
                        time.sleep(2)  # リトライ前に待機
                        continue
                    return "解説の生成に失敗しました（応答なし）。"
                
            except Exception as e:
                logger.error(f"Gemini API エラー (試行 {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(5)  # リトライ前に待機
                    continue
                return f"解説の生成に失敗しました。エラー: {str(e)}"
        
        return "解説の生成に失敗しました（最大試行回数超過）。"
    
    def _prepare_image_part(self, image_path: str) -> Optional[Part]:
        """画像をGemini用のPartオブジェクトとして準備"""
        try:
            # 画像検証
            if not self.validator.validate_image(image_path):
                return None
            
            # 画像をBase64エンコード
            image_base64 = self._encode_image_to_base64(image_path)
            if not image_base64:
                return None
            
            # MIMEタイプ判定
            mime_type = self._get_mime_type(image_path)
            
            # 画像データをPartオブジェクトとして準備
            image_part = Part.from_data(
                data=base64.b64decode(image_base64),
                mime_type=mime_type
            )
            
            return image_part
            
        except Exception as e:
            logger.error(f"画像準備エラー: {image_path} - {e}")
            return None
    
    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """画像をBase64エンコード"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                logger.debug(f"画像エンコード完了: {image_path}")
                return encoded_string
        except Exception as e:
            logger.error(f"画像エンコードエラー: {image_path} - {e}")
            return None
    
    def _get_mime_type(self, image_path: str) -> str:
        """ファイル拡張子からMIMEタイプを判定"""
        path = Path(image_path)
        suffix = path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        return mime_map.get(suffix, 'image/jpeg')


def is_available() -> bool:
    """Vertex AIが利用可能かチェック"""
    return VERTEX_AI_AVAILABLE


def get_version() -> Optional[str]:
    """Vertex AIのバージョンを取得"""
    return VERTEX_AI_VERSION
