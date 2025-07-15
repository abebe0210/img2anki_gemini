#!/usr/bin/env python3
"""
Anki画像解説カード生成ツール - 統合実行スクリプト
画像からAnkiカードを生成するツールの統合セットアップ・実行スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

def check_python_version():
    """Pythonバージョンチェック"""
    if sys.version_info < (3, 8):
        print("❌ エラー: Python 3.8以上が必要です")
        print(f"   現在のバージョン: {sys.version}")
        return False
    print(f"✅ Python: {sys.version.split()[0]}")
    return True

def install_packages():
    """必要パッケージのインストール"""
    print("📦 必要なパッケージをインストールしています...")
    
    try:
        # パッケージのアップグレードも含める
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ], check=True, capture_output=True, text=True)
        print("✅ パッケージインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ パッケージインストール失敗")
        print(f"エラー詳細: {e.stderr}")
        return False

def setup_env():
    """環境設定"""
    print("⚙️ 環境設定を確認しています...")
    
    # .envファイルがない場合は作成
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            print("✅ .envファイルを作成しました")
        else:
            print("❌ .env.exampleファイルが見つかりません")
            return False
    
    # 必要なフォルダを作成
    folders = ["credentials", "img", "output"]
    for folder in folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            folder_path.mkdir(exist_ok=True)
            print(f"✅ {folder}フォルダを作成しました")
    
    print("✅ 環境設定完了")
    return True

def validate_configuration():
    """設定の詳細検証"""
    print("🔍 設定を検証しています...")
    
    try:
        # .envファイルの読み込みテスト
        from dotenv import load_dotenv
        load_dotenv()
        
        project_id = os.getenv('GCP_PROJECT_ID')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # 必須設定の確認
        if not project_id or project_id == "your-gcp-project-id":
            print("⚠️  警告: .envファイルでGCP_PROJECT_IDを設定してください")
            return False
            
        # 認証ファイルの確認
        if credentials_path:
            if not Path(credentials_path).exists():
                print(f"⚠️  警告: 認証情報ファイルが見つかりません: {credentials_path}")
                return False
            print(f"✅ 認証情報ファイル: {credentials_path}")
        else:
            print("⚠️  警告: GOOGLE_APPLICATION_CREDENTIALSが設定されていません")
            return False
            
        print(f"✅ GCPプロジェクト: {project_id}")
        return True
        
    except ImportError:
        print("❌ エラー: python-dotenvがインストールされていません")
        return False
    except Exception as e:
        print(f"❌ 設定検証エラー: {e}")
        return False

def check_images():
    """画像ファイルの確認"""
    print("🖼️  画像ファイルを確認しています...")
    
    img_folder = Path("img")
    if not img_folder.exists():
        print("❌ エラー: imgフォルダが見つかりません")
        return False
    
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = [f for f in img_folder.iterdir() 
                   if f.is_file() and f.suffix.lower() in supported_formats]
    
    if not image_files:
        print("⚠️  警告: imgフォルダに処理可能な画像ファイルがありません")
        print("   サポート形式: JPG, JPEG, PNG, GIF, BMP")
        return False
    
    print(f"✅ 処理可能な画像: {len(image_files)}個")
    
    # バッチ処理に関する情報表示
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        batch_threshold = int(os.getenv('BATCH_THRESHOLD', '10'))
        use_batch = os.getenv('USE_BATCH_PROCESSING', 'true').lower() == 'true'
        
        if use_batch and len(image_files) >= batch_threshold:
            print(f"💡 バッチ処理モード: {len(image_files)}個 ≥ {batch_threshold}個 → 50%コスト削減！")
        elif len(image_files) < batch_threshold:
            print(f"💡 リアルタイム処理モード: {len(image_files)}個 < {batch_threshold}個")
        else:
            print("💡 リアルタイム処理モード")
    except:
        pass
    
    for img in image_files[:5]:  # 最初の5個を表示
        print(f"   - {img.name}")
    if len(image_files) > 5:
        print(f"   ... その他 {len(image_files) - 5}個")
    
    return True

def run_main_program():
    """メインプログラムの実行"""
    print("\n🚀 Ankiカード生成を開始します...")
    
    # 処理モードの選択
    print("\n🎛️ 処理モード選択:")
    print("1. インタラクティブ選択（推奨）")
    print("2. 設定ファイル従う")
    print("3. 高度な選択ツール")
    
    mode_choice = input("\n選択してください (1-3): ").strip()
    
    command = [sys.executable, "main.py"]
    
    if mode_choice == "1":
        command.append("--interactive")
        print("📋 インタラクティブモードで実行します...")
    elif mode_choice == "3":
        print("🔧 高度な選択ツールを起動します...")
        try:
            result = subprocess.run([sys.executable, "mode_selector.py"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 選択ツールエラー: {e}")
            return False
    else:
        print("📋 設定ファイルに従って実行します...")
    
    print("=" * 50)
    
    try:
        # main.pyの存在確認
        if not Path("main.py").exists():
            print("❌ エラー: main.py が見つかりません")
            return False
        
        # メインプログラム実行
        result = subprocess.run(command, check=True)
        
        # 結果確認
        output_files = list(Path("output").glob("*.apkg"))
        if output_files:
            latest_file = max(output_files, key=lambda p: p.stat().st_mtime)
            print(f"\n🎉 処理が完了しました！")
            print(f"📁 生成ファイル: {latest_file}")
            print(f"📱 Ankiにインポートして使用してください")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ プログラム実行エラー: {e}")
        print("\nログファイル anki_generator.log を確認してください。")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return False

def print_setup_instructions():
    """セットアップ手順の表示"""
    print("\n📋 必要なセットアップ:")
    print("1. 【GCP設定】")
    print("   - Google Cloud Platformでプロジェクト作成")
    print("   - Vertex AI APIの有効化")
    print("   - サービスアカウント作成とJSONキーダウンロード")
    print("\n2. 【ローカル設定】")
    print("   - .envファイルを編集してGCP_PROJECT_IDを設定")
    print("   - credentialsフォルダにJSONキーファイルを配置")
    print("   - imgフォルダに処理したい画像を配置")
    print("\n詳細な手順はREADME.mdを参照してください。")

def main():
    """メイン関数"""
    print("🎯 Anki画像解説カード生成ツール")
    print("=" * 50)
    print()
    
    # 基本チェック
    if not check_python_version():
        input("\nEnterキーを押して終了...")
        return 1
    
    # パッケージインストール
    if not install_packages():
        print("\n❌ セットアップに失敗しました")
        input("Enterキーを押して終了...")
        return 1
    
    # 環境設定
    if not setup_env():
        print("\n❌ 環境設定に失敗しました")
        input("Enterキーを押して終了...")
        return 1
    
    # 設定検証
    config_valid = validate_configuration()
    images_available = check_images()
    
    if not config_valid or not images_available:
        print("\n⚠️  セットアップが不完全です")
        print_setup_instructions()
        
        response = input("\nそれでも続行しますか？ (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("処理を中止しました")
            input("\nEnterキーを押して終了...")
            return 0
    else:
        print("\n✅ すべての設定が完了しています")
        response = input("\nAnkiカード生成を開始しますか？ (Y/n): ").strip().lower()
        if response in ['n', 'no']:
            print("処理を中止しました")
            return 0
    
    # メインプログラム実行
    if run_main_program():
        print("\n🌟 すべての処理が正常に完了しました！")
        return 0
    else:
        print("\n❌ 処理中にエラーが発生しました")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nEnterキーを押して終了...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n処理を中断しました")
        sys.exit(1)
