#!/usr/bin/env python3
"""
リアルタイム処理専用実行スクリプト
リアルタイムでAnkiカードを生成します
"""

import sys
import subprocess

def main():
    """リアルタイム処理モードでメインプログラムを実行"""
    print("⚡ リアルタイム処理モードでAnkiカード生成を開始します")
    print("🔄 即座に結果を取得する処理を実行中...")
    print("=" * 60)
    
    try:
        # リアルタイム処理モードで実行
        command = [sys.executable, "main.py", "--no-batch"]
        result = subprocess.run(command, check=True)
        
        print("\n✅ リアルタイム処理が完了しました！")
        print("📁 outputフォルダをチェックして、生成されたAPKGファイルをAnkiにインポートしてください")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ リアルタイム処理エラー: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
