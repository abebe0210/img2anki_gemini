#!/usr/bin/env python3
"""
Anki画像解説カード生成ツール - ファクトリークラス
各種コンポーネントの生成を管理
"""

from typing import Optional, TYPE_CHECKING
import logging

from gemini_processor import GeminiProcessor
from anki_builder import AnkiCardBuilder
from image_validator import ImageValidator
from batch_processor import BatchProcessor, BatchJobManager, BATCH_PROCESSING_AVAILABLE
from exceptions import ConfigurationError
import config

if TYPE_CHECKING:
    from main import AnkiCardGenerator

logger = logging.getLogger(__name__)


class ComponentFactory:
    """コンポーネント生成ファクトリー"""
    
    @staticmethod
    def create_gemini_processor() -> GeminiProcessor:
        """Geminiプロセッサを作成"""
        try:
            return GeminiProcessor(
                config.PROJECT_ID,
                config.LOCATION,
                config.MODEL_NAME
            )
        except Exception as e:
            raise ConfigurationError(f"Geminiプロセッサの作成に失敗: {e}")
    
    @staticmethod
    def create_anki_builder() -> AnkiCardBuilder:
        """Ankiビルダーを作成"""
        try:
            return AnkiCardBuilder()
        except Exception as e:
            raise ConfigurationError(f"Ankiビルダーの作成に失敗: {e}")
    
    @staticmethod
    def create_image_validator(max_size_mb: int = 10) -> ImageValidator:
        """画像バリデーターを作成"""
        try:
            return ImageValidator(max_size_mb)
        except Exception as e:
            raise ConfigurationError(f"画像バリデーターの作成に失敗: {e}")
    
    @staticmethod
    def create_batch_processor() -> Optional[BatchProcessor]:
        """バッチプロセッサを作成（利用可能な場合）"""
        if not BATCH_PROCESSING_AVAILABLE:
            logger.warning("バッチ処理パッケージが利用できません")
            return None
        
        try:
            return BatchProcessor(config.PROJECT_ID, config.LOCATION)
        except Exception as e:
            logger.error(f"バッチプロセッサの作成に失敗: {e}")
            return None
    
    @staticmethod
    def create_batch_job_manager() -> BatchJobManager:
        """バッチジョブマネージャーを作成"""
        try:
            return BatchJobManager()
        except Exception as e:
            raise ConfigurationError(f"バッチジョブマネージャーの作成に失敗: {e}")


class AnkiGeneratorFactory:
    """Anki生成器ファクトリー"""
    
    @staticmethod
    def create_generator(use_batch_processing: Optional[bool] = None, force_batch: bool = False) -> 'AnkiCardGenerator':
        """Anki生成器を作成"""
        from main import AnkiCardGenerator  # 循環インポート回避
        
        try:
            return AnkiCardGenerator(use_batch_processing, force_batch)
        except Exception as e:
            raise ConfigurationError(f"Anki生成器の作成に失敗: {e}")
