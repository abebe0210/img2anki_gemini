#!/usr/bin/env python3
"""
処理モード選択スクリプト
バッチ処理またはリアルタイム処理を直感的に選択できます
"""

import sys
import subprocess
from pathlib import Path
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

def check_images():
    """画像ファイルの確認"""
    img_folder = Path("img")
    if not img_folder.exists():
        return []
    
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = [f for f in img_folder.iterdir() 
                   if f.is_file() and f.suffix.lower() in supported_formats]
    return image_files

def calculate_cost_savings(image_count):
    """コスト削減効果を計算"""
    # Gemini 1.5 Flash の料金 (参考値)
    realtime_cost_per_1k_tokens = 0.000075  # USD
    batch_cost_per_1k_tokens = 0.0000375    # USD (50% off)
    avg_tokens_per_image = 1000  # 推定値
    
    total_tokens = image_count * avg_tokens_per_image
    realtime_cost = (total_tokens / 1000) * realtime_cost_per_1k_tokens
    batch_cost = (total_tokens / 1000) * batch_cost_per_1k_tokens
    savings = realtime_cost - batch_cost
    savings_percent = (savings / realtime_cost) * 100 if realtime_cost > 0 else 0
    
    return {
        'realtime_cost': realtime_cost,
        'batch_cost': batch_cost,
        'savings': savings,
        'savings_percent': savings_percent
    }

def show_mode_selection(image_count):
    """処理モード選択画面を表示"""
    print("🎯 Anki画像解説カード生成ツール - 処理モード選択")
    print("=" * 60)
    print(f"📊 処理対象画像数: {image_count}個")
    
    if image_count > 0:
        cost_info = calculate_cost_savings(image_count)
        print(f"\n💰 コスト分析:")
        print(f"   推定処理料金:")
        print(f"   - リアルタイム処理: ${cost_info['realtime_cost']:.4f}")
        print(f"   - バッチ処理:       ${cost_info['batch_cost']:.4f}")
        if cost_info['savings'] > 0:
            print(f"   - 削減額:           ${cost_info['savings']:.4f} ({cost_info['savings_percent']:.1f}%)")
    
    print("\n🚀 利用可能な処理モード:")
    print()
    print("1. 🔥 バッチ処理モード")
    print("   ├ 📉 コスト削減: 通常料金の50%")
    print("   ├ ⚡ 効率的: 大量画像の一括処理")
    print("   ├ 🔄 非同期処理: ジョブ送信後は待機不要")
    print("   └ 💡 推奨: 10個以上の画像処理時")
    print()
    print("2. ⚡ リアルタイム処理モード")
    print("   ├ 🚀 即座に結果取得")
    print("   ├ 👀 リアルタイム進捗確認")
    print("   ├ 💸 通常料金")
    print("   └ 💡 推奨: 少量画像または急ぎの場合")
    print()
    print("3. 🔧 設定変更")
    print("   └ .envファイルの設定を変更")
    print()
    print("0. ❌ 終了")
    
    while True:
        choice = input("\n処理モードを選択してください (0-3): ").strip()
        
        if choice == "1":
            return "batch"
        elif choice == "2":
            return "realtime"
        elif choice == "3":
            return "settings"
        elif choice == "0":
            return "exit"
        else:
            print("❌ 0-3の数字を入力してください")

def run_batch_mode():
    """バッチ処理モードで実行"""
    print("\n🚀 バッチ処理モードで実行します...")
    print("💰 通常料金の50%でコスト削減処理を開始")
    print("=" * 50)
    
    try:
        command = [sys.executable, "main.py", "--batch"]
        result = subprocess.run(command, check=True)
        
        print("\n✅ バッチジョブの送信が完了しました！")
        print("⏳ Google Cloudでバッチ処理が実行されます（数分〜数時間）")
        print("\n📋 次のステップ:")
        print("1. しばらく待機してから以下のコマンドで結果を確認:")
        print("   python process_batch.py")
        print("2. または Google Cloud Console で進捗を確認:")
        print("   https://console.cloud.google.com/vertex-ai/batch-predictions")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ バッチ処理エラー: {e}")
        return False

def run_realtime_mode():
    """リアルタイム処理モードで実行"""
    print("\n⚡ リアルタイム処理モードで実行します...")
    print("🔄 即座に結果を取得する処理を開始")
    print("=" * 50)
    
    try:
        command = [sys.executable, "main.py", "--no-batch"]
        result = subprocess.run(command, check=True)
        
        print("\n✅ リアルタイム処理が完了しました！")
        print("📁 outputフォルダをチェックして、生成されたAPKGファイルをAnkiにインポートしてください")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ リアルタイム処理エラー: {e}")
        return False

def show_settings():
    """設定表示・変更"""
    print("\n🔧 現在の設定:")
    print("=" * 30)
    
    # .env設定を表示
    project_id = os.getenv('GCP_PROJECT_ID', '未設定')
    use_batch = os.getenv('USE_BATCH_PROCESSING', 'true')
    batch_threshold = os.getenv('BATCH_THRESHOLD', '10')
    wait_completion = os.getenv('BATCH_WAIT_FOR_COMPLETION', 'false')
    
    print(f"📋 GCPプロジェクト: {project_id}")
    print(f"🚀 バッチ処理デフォルト: {use_batch}")
    print(f"🔢 バッチ処理閾値: {batch_threshold}個")
    print(f"⏳ バッチ完了待機: {wait_completion}")
    
    print("\n💡 設定を変更するには .env ファイルを編集してください")
    print("📝 設定ファイルの場所: .env")
    
    input("\nEnterキーを押して戻る...")

def main():
    """メイン関数"""
    try:
        # 画像ファイルチェック
        image_files = check_images()
        image_count = len(image_files)
        
        if image_count == 0:
            print("⚠️  警告: imgフォルダに処理可能な画像ファイルがありません")
            print("📁 サポート形式: JPG, JPEG, PNG, GIF, BMP")
            input("\nEnterキーを押して終了...")
            return 1
        
        while True:
            choice = show_mode_selection(image_count)
            
            if choice == "batch":
                if run_batch_mode():
                    break
                else:
                    input("\nEnterキーを押して続行...")
                    
            elif choice == "realtime":
                if run_realtime_mode():
                    break
                else:
                    input("\nEnterキーを押して続行...")
                    
            elif choice == "settings":
                show_settings()
                
            elif choice == "exit":
                print("👋 処理を終了しました")
                return 0
        
        print("\n🌟 処理が正常に完了しました！")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 処理を中断しました")
        return 1
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nEnterキーを押して終了...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 処理を中断しました")
        sys.exit(1)
