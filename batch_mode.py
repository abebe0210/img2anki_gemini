#!/usr/bin/env python3
"""
バッチ処理専用実行スクリプト
バッチ処理でAnkiカードを生成します
"""

import sys
import subprocess

def main():
    """バッチ処理モードでメインプログラムを実行"""
    print("🚀 バッチ処理モードでAnkiカード生成を開始します")
    print("💰 通常料金の50%でコスト削減処理を実行中...")
    print("=" * 60)
    
    try:
        # バッチ処理モードで実行
        command = [sys.executable, "main.py", "--batch"]
        result = subprocess.run(command, check=True)
        
        print("\n✅ バッチジョブの送信が完了しました！")
        print("⏳ Google Cloudでバッチ処理が実行されます（数分〜数時間）")
        print("\n📋 次のステップ:")
        print("1. しばらく待機してから以下のコマンドで結果を確認:")
        print("   python process_batch.py")
        print("2. または Google Cloud Console で進捗を確認:")
        print("   https://console.cloud.google.com/vertex-ai/batch-predictions")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ バッチ処理エラー: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
