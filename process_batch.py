#!/usr/bin/env python3
"""
バッチ処理結果の手動処理スクリプト
完了したバッチジョブの結果からAnkiカードを生成します
"""

import sys
from pathlib import Path
import logging
from main import AnkiCardGenerator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anki_generator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_batch_status():
    """バッチジョブの状況確認"""
    try:
        generator = AnkiCardGenerator(force_batch=False)  # バッチ処理結果処理時は強制フラグは不要
        completed_jobs = generator.process_completed_batch_jobs()
        
        if completed_jobs:
            print(f"\n🎉 {len(completed_jobs)}個のバッチジョブが完了しました！")
            for job in completed_jobs:
                print(f"  📁 {job['output_file']} ({job['card_count']}枚)")
        else:
            print("✅ 新たに完了したバッチジョブはありません")
            
        return len(completed_jobs)
        
    except Exception as e:
        logger.error(f"バッチ状況確認エラー: {e}")
        print(f"❌ エラー: {e}")
        return 0


def main():
    """メイン関数"""
    print("=== バッチ処理結果の手動処理 ===")
    
    try:
        completed_count = check_batch_status()
        
        if completed_count > 0:
            print(f"\n✨ {completed_count}個のバッチが正常に処理されました")
            print("📱 生成されたAPKGファイルをAnkiにインポートしてください")
        else:
            print("\n💡 ヒント:")
            print("  - バッチジョブが完了するまでお待ちください")
            print("  - Google Cloud Console でジョブ状況を確認できます")
            
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
