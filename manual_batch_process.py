#!/usr/bin/env python3
"""
バッチ処理結果の手動取得・処理スクリプト
Cloud Storageから直接結果を取得してAnkiカードを生成
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import logging
from google.cloud import storage

# 既存のモジュールをインポート
from main import AnkiCardGenerator
from anki_builder import AnkiCardBuilder
import config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_batch_results_manual(bucket_name: str, prefix: str) -> list:
    """Cloud Storageから手動でバッチ結果をダウンロード"""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        results = []
        for blob in bucket.list_blobs(prefix=prefix):
            if blob.name.endswith('.jsonl'):
                logger.info(f"結果ファイルをダウンロード: {blob.name}")
                content = blob.download_as_text()
                
                for line in content.strip().split('\n'):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            results.append(result)
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析エラー: {e}")
                            continue
        
        logger.info(f"取得した結果数: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"結果ダウンロードエラー: {e}")
        return []


def create_anki_cards_from_results(results: list, image_files: list) -> str:
    """バッチ結果からAnkiカードを作成"""
    try:
        anki_builder = AnkiCardBuilder()
        media_files = []
        
        for result, image_path in zip(results, image_files):
            try:
                # レスポンスから解説文を抽出
                if "response" in result and result["response"]:
                    response = result["response"]
                    if "candidates" in response and response["candidates"]:
                        candidate = response["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            description = candidate["content"]["parts"][0]["text"]
                            
                            # Ankiカード作成
                            image_filename = anki_builder.create_card(str(image_path), description)
                            
                            if image_filename:
                                media_files.append(str(image_path))
                                logger.info(f"✓ カード作成完了: {Path(image_path).name}")
                            else:
                                logger.error(f"✗ カード作成失敗: {Path(image_path).name}")
                else:
                    logger.error(f"✗ 無効なレスポンス: {Path(image_path).name}")
                    
            except Exception as e:
                logger.error(f"カード作成エラー {Path(image_path).name}: {e}")
                continue
        
        if media_files:
            # Ankiデッキをエクスポート
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"anki_batch_cards_manual_{timestamp}.apkg"
            
            anki_builder.export_deck(str(output_file), media_files)
            logger.info(f"Ankiデッキエクスポート完了: {output_file}")
            
            return str(output_file)
        else:
            logger.warning("作成できたカードがありません")
            return ""
            
    except Exception as e:
        logger.error(f"Ankiカード作成エラー: {e}")
        return ""


def main():
    """メイン関数"""
    print("=== バッチ処理結果の手動取得・処理 ===")
    
    # 設定値
    bucket_name = f"{config.PROJECT_ID}-anki-batch-processing"
    output_prefix = "batch_outputs/20250714_204616/"  # 今回のバッチ処理の出力フォルダ
    image_files = ["img\\スクリーンショット 2025-07-08 165631.png"]  # 処理した画像ファイル
    
    print(f"バケット: {bucket_name}")
    print(f"出力フォルダ: {output_prefix}")
    
    try:
        # 1. Cloud Storageから結果をダウンロード
        results = download_batch_results_manual(bucket_name, output_prefix)
        
        if not results:
            print("❌ バッチ処理結果が見つかりませんでした")
            print("💡 ヒント:")
            print("  - Google Cloud Console でバッチジョブの状況を確認してください")
            print("  - バッチ処理がまだ完了していない可能性があります")
            return 1
        
        # 2. Ankiカードを作成
        output_file = create_anki_cards_from_results(results, image_files)
        
        if output_file:
            print(f"\n🎉 バッチ処理結果の処理が完了しました！")
            print(f"📁 生成ファイル: {output_file}")
            print(f"📱 Ankiにインポートして使用してください")
            return 0
        else:
            print("❌ Ankiカードの作成に失敗しました")
            return 1
            
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
