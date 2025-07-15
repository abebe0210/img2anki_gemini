#!/usr/bin/env python3
"""
例外クラス定義モジュール
アプリケーション固有の例外を定義
"""


class AnkiGeneratorError(Exception):
    """Anki生成ツール基底例外クラス"""
    pass


class ConfigurationError(AnkiGeneratorError):
    """設定エラー"""
    pass


class ImageValidationError(AnkiGeneratorError):
    """画像検証エラー"""
    pass


class GeminiProcessingError(AnkiGeneratorError):
    """Gemini処理エラー"""
    pass


class BatchProcessingError(AnkiGeneratorError):
    """バッチ処理エラー"""
    pass


class AnkiExportError(AnkiGeneratorError):
    """Ankiエクスポートエラー"""
    pass
