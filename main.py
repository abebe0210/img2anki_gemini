#!/usr/bin/env python3
"""
Anki画像解説カード生成ツール (リファクタリング版)
モジュール化により保守性を向上
"""

import os
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

# モジュールのインポート
try:
    from gemini_processor import GeminiProcessor, is_available as gemini_available
    from anki_builder import AnkiCardBuilder
    from image_validator import ImageValidator
    from batch_processor import BatchProcessor, BatchJobManager, BATCH_PROCESSING_AVAILABLE
    from monitoring import PerformanceMonitor, ResourceChecker, BatchCostCalculator
    from exceptions import ConfigurationError, AnkiGeneratorError
except ImportError as e:
    print(f"モジュールインポートエラー: {e}")
    print("必要なモジュールファイルが見つかりません")
    exit(1)

import config

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


class AnkiCardGenerator:
    """Anki カード生成メインクラス（リファクタリング版）"""
    
    def __init__(self, use_batch_processing=None, force_batch=False):
        """初期化"""
        # Gemini可用性チェック
        if not gemini_available():
            raise ConfigurationError("Vertex AI パッケージが利用できません。パッケージを再インストールしてください。")
        
        # リソースチェック
        checker = ResourceChecker()
        if not checker.check_available_space():
            logger.warning("ディスク容量が不足している可能性があります")
        if not checker.check_memory_usage():
            logger.warning("メモリ使用率が高くなっています")
        
        # バッチ処理設定
        if use_batch_processing is None:
            use_batch_processing = config.USE_BATCH_PROCESSING
        
        self.use_batch_processing = use_batch_processing and BATCH_PROCESSING_AVAILABLE
        self.force_batch = force_batch  # コマンドライン引数による強制指定
        
        # 各コンポーネントの初期化
        try:
            self.gemini = GeminiProcessor(config.PROJECT_ID, config.LOCATION, config.MODEL_NAME)
            self.anki_builder = AnkiCardBuilder()
            self.image_validator = ImageValidator()
            self.cost_calculator = BatchCostCalculator()
        except Exception as e:
            raise ConfigurationError(f"コンポーネント初期化エラー: {e}")
        
        # バッチ処理用の初期化
        if self.use_batch_processing:
            try:
                self.batch_processor = BatchProcessor(config.PROJECT_ID, config.LOCATION)
                self.job_manager = BatchJobManager()
                if self.force_batch:
                    logger.info(f"バッチ処理モードが強制有効です（画像数制限無視）")
                else:
                    logger.info(f"バッチ処理モードが有効です（{config.BATCH_THRESHOLD}個以上の画像で50%コスト削減）")
            except Exception as e:
                logger.error(f"バッチ処理初期化エラー: {e}")
                if self.force_batch:
                    # 強制モードの場合はエラーで終了
                    raise ConfigurationError(f"バッチ処理強制モードでの初期化失敗: {e}")
                else:
                    # 通常モードの場合はバッチ処理を無効化
                    self.use_batch_processing = False
                    logger.warning("バッチ処理を無効化してリアルタイム処理モードに変更します")
        
        if not self.use_batch_processing:
            if not BATCH_PROCESSING_AVAILABLE:
                logger.info("リアルタイム処理モード（バッチ処理パッケージが利用できません）")
            else:
                logger.info("リアルタイム処理モード")
    
    def process_images_folder(self, images_folder_path: str) -> List[str]:
        """画像フォルダ内の全画像を処理"""
        # 有効な画像ファイルを取得
        image_files = self.image_validator.get_valid_images(images_folder_path)
        
        if not image_files:
            logger.warning("処理可能な画像ファイルが見つかりません。")
            return []
        
        logger.info(f"{len(image_files)}個の画像を処理開始")
        
        # バッチ処理または通常処理の選択
        # 強制指定の場合は画像数制限を無視
        if self.use_batch_processing and (self.force_batch or len(image_files) >= config.BATCH_THRESHOLD):
            if self.force_batch and len(image_files) < config.BATCH_THRESHOLD:
                logger.info(f"⚠️ 画像数が少ない（{len(image_files)} < {config.BATCH_THRESHOLD}）ですが、コマンドライン引数により強制的にバッチ処理を実行します")
            return self._process_images_batch(image_files)
        else:
            return self._process_images_individual(image_files)
    
    def _process_images_individual(self, image_files: List[Path]) -> List[str]:
        """個別処理（リアルタイム処理）- 画像ファイル名昇順で処理"""
        logger.info("リアルタイム処理を開始します（画像ファイル名昇順）")
        
        # 画像ファイルを名前で昇順ソート（確実に順序を保証）
        sorted_image_files = sorted(image_files, key=lambda x: x.name.lower())
        
        media_files = []
        
        for i, image_path in enumerate(sorted_image_files, 1):
            logger.info(f"処理中 ({i}/{len(sorted_image_files)}): {image_path.name}")
            
            # Geminiで解説生成
            description = self.gemini.generate_description(str(image_path))
            
            # Ankiカード作成
            image_filename = self.anki_builder.create_card(str(image_path), description)
            
            if image_filename:
                media_files.append(str(image_path))
                logger.info(f"  ✓ 完了: {image_path.name}")
            else:
                logger.error(f"  ✗ 失敗: {image_path.name}")
            
            # API制限対策：少し待機
            if i < len(image_files):
                time.sleep(config.API_WAIT_TIME)
        
        logger.info(f"リアルタイム処理完了: {len(media_files)}/{len(image_files)} ファイル")
        return media_files
    
    def _process_images_batch(self, image_files: List[Path]) -> List[str]:
        """バッチ処理（コスト削減版）"""
        logger.info(f"バッチ処理を開始します（{len(image_files)}個の画像）")
        
        try:
            # 1. バッチリクエスト準備
            batch_requests = self.batch_processor.prepare_batch_requests(image_files)
            
            # 2. バッチ入力をアップロード
            input_uri = self.batch_processor.upload_batch_input(batch_requests)
            
            # 3. バッチジョブ作成
            job_id = self.batch_processor.create_batch_job(input_uri, config.MODEL_NAME)
            
            # 4. 設定に応じて待機または手動処理
            if config.BATCH_WAIT_FOR_COMPLETION:
                results = self.batch_processor.wait_for_completion(job_id)
                media_files = self._create_cards_from_batch_results(results, image_files)
                logger.info(f"バッチ処理完了: {len(media_files)}個のカード生成")
                return media_files
            else:
                # 手動実行モード
                self.job_manager.save_job_info(job_id, image_files)
                logger.info("バッチジョブを送信しました。完了後に手動で結果を処理してください。")
                logger.info(f"ジョブID: {job_id}")
                logger.info("完了確認: python process_batch.py")
                return []  # 手動実行なのでメディアファイルは空
                
        except ImportError as e:
            # パッケージが利用できない場合のみフォールバック（強制モードでない場合）
            if not self.force_batch:
                logger.error(f"バッチ処理パッケージエラー: {e}")
                logger.info("リアルタイム処理にフォールバック")
                return self._process_images_individual(image_files)
            else:
                logger.error(f"バッチ処理パッケージエラー（強制モード）: {e}")
                raise e
        except Exception as e:
            # 強制モードの場合は一切フォールバックしない
            if self.force_batch:
                logger.error(f"バッチ処理エラー（強制モード）: {e}")
                logger.error("--batch フラグが指定されているため、リアルタイム処理にフォールバックしません")
                raise e
            else:
                # 通常モードでも基本的にはエラーとして扱う
                logger.error(f"バッチ処理エラー: {e}")
                logger.info("バッチ処理が失敗しました。エラーを確認してください。")
                raise e
    
    def _create_cards_from_batch_results(self, results: List[Dict[str, Any]], image_files: List[Path]) -> List[str]:
        """バッチ処理結果からAnkiカードを作成（画像ファイル名昇順）"""
        media_files = []
        
        # 画像ファイル名をキーとした辞書を作成
        image_dict = {img.name: img for img in image_files}
        
        # 結果をcustomId（画像ファイル名）でソートして処理順序を保証
        sorted_results = []
        for result in results:
            custom_id = result.get("customId")
            if custom_id and custom_id in image_dict:
                sorted_results.append(result)
            else:
                logger.warning(f"対応する画像ファイルが見つかりません: {custom_id}")
        
        # customId（画像ファイル名）で昇順ソート
        sorted_results.sort(key=lambda x: x.get("customId", "").lower())
        
        logger.info(f"バッチ結果を画像ファイル名昇順で処理開始")
        
        for result in sorted_results:
            try:
                # customIdから対応する画像ファイルを特定
                custom_id = result.get("customId")
                image_path = image_dict[custom_id]
                
                if "response" in result and result["response"]:
                    # 成功した場合
                    response = result["response"]
                    if "candidates" in response and response["candidates"]:
                        candidate = response["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            description = candidate["content"]["parts"][0]["text"]
                            
                            # Ankiカード作成
                            image_filename = self.anki_builder.create_card(str(image_path), description)
                            
                            if image_filename:
                                media_files.append(str(image_path))
                                logger.info(f"  ✓ バッチ処理完了: {image_path.name}")
                            else:
                                logger.error(f"  ✗ カード作成失敗: {image_path.name}")
                else:
                    # エラーの場合
                    error_msg = result.get("status", "不明なエラー")
                    logger.error(f"  ✗ バッチ処理エラー {image_path.name}: {error_msg}")
                    
            except Exception as e:
                logger.error(f"結果処理エラー: {e}")
                continue
        
        return media_files
    
    def process_completed_batch_jobs(self) -> List[Dict[str, Any]]:
        """完了したバッチジョブの結果を処理"""
        if not self.use_batch_processing:
            logger.info("バッチ処理が無効です")
            return []
        
        jobs = self.job_manager.get_pending_jobs()
        
        if not jobs:
            logger.info("処理待ちのバッチジョブはありません")
            return []
        
        completed_jobs = []
        remaining_jobs = []
        
        for job_info in jobs:
            job_id = job_info["job_id"]
            try:
                from google.cloud import aiplatform
                job = aiplatform.BatchPredictionJob(job_id)
                
                # refresh() メソッドの存在を確認してから使用
                try:
                    job.refresh()
                except AttributeError:
                    # refresh() メソッドが存在しない場合は、状態を直接取得
                    pass
                
                # job.state の取得方法を改善
                try:
                    if hasattr(job, 'state'):
                        if hasattr(job.state, 'name'):
                            state = job.state.name
                        else:
                            state = str(job.state)
                    else:
                        # 別の方法で状態を取得
                        state = job._gca_resource.state.name if hasattr(job._gca_resource, 'state') else "UNKNOWN"
                except Exception:
                    logger.warning(f"通常の方法でジョブ状態取得に失敗: {job_id}")
                    # 代替手段を試す
                    state = self._check_job_status_alternative(job_id)
                
                logger.info(f"ジョブ {job_id} の状態: {state}")
                
                if state == "JOB_STATE_SUCCEEDED":
                    logger.info(f"完了ジョブを処理中: {job_id}")
                    
                    # 結果をダウンロード
                    results = self.batch_processor.download_batch_results(job)
                    
                    # Ankiカード作成
                    image_files = [Path(path) for path in job_info["image_files"]]
                    media_files = self._create_cards_from_batch_results(results, image_files)
                    
                    if media_files:
                        # Ankiデッキをエクスポート
                        output_dir = Path("output")
                        output_dir.mkdir(exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file = output_dir / f"anki_batch_cards_{timestamp}.apkg"
                        self.anki_builder.export_deck(str(output_file), media_files)
                        
                        completed_jobs.append({
                            "job_id": job_id,
                            "output_file": str(output_file),
                            "card_count": len(media_files)
                        })
                        
                        logger.info(f"✅ バッチジョブ完了: {len(media_files)}枚のカード → {output_file}")
                
                elif state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
                    logger.error(f"❌ バッチジョブ失敗: {job_id} (状態: {state})")
                else:
                    # まだ実行中
                    remaining_jobs.append(job_info)
                    logger.info(f"⏳ 実行中: {job_id} (状態: {state})")
                    
            except Exception as e:
                logger.error(f"ジョブ処理エラー {job_id}: {e}")
                remaining_jobs.append(job_info)
        
        # 未完了のジョブ情報を更新
        self.job_manager.update_jobs(remaining_jobs)
        
        return completed_jobs
    
    def export_deck(self, output_path: str, media_files: List[str]) -> None:
        """Ankiデッキをエクスポート"""
        self.anki_builder.export_deck(output_path, media_files)
    
    def _check_job_status_alternative(self, job_id: str) -> str:
        """代替手段でバッチジョブの状態を確認"""
        try:
            import subprocess
            import json
            
            # gcloud CLI を使用してジョブ状態を確認
            cmd = [
                "gcloud", "ai", "batch-prediction-jobs", "describe", 
                job_id.split('/')[-1],  # ジョブIDのみを抽出
                "--region", config.LOCATION,
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                job_info = json.loads(result.stdout)
                state = job_info.get('state', 'UNKNOWN')
                logger.info(f"gcloud CLI で取得した状態: {state}")
                return state
            else:
                logger.warning(f"gcloud CLI エラー: {result.stderr}")
                return "UNKNOWN"
                
        except Exception as e:
            logger.debug(f"gcloud CLI による状態確認に失敗: {e}")
            return "UNKNOWN"

def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Anki画像解説カード生成ツール")
    
    parser.add_argument(
        '--batch', 
        action='store_true', 
        help='バッチ処理を強制的に有効にする'
    )
    
    parser.add_argument(
        '--no-batch', 
        action='store_true', 
        help='バッチ処理を強制的に無効にする（リアルタイム処理）'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='インタラクティブモードで処理方法を選択'
    )
    
    parser.add_argument(
        '--images-folder',
        type=str,
        default=None,
        help='画像フォルダのパスを指定'
    )
    
    return parser.parse_args()


def interactive_batch_selection(image_count: int) -> bool:
    """インタラクティブなバッチ処理選択"""
    print(f"\n📊 処理モード選択 ({image_count}個の画像)")
    print("=" * 50)
    
    # コスト計算を表示
    try:
        from monitoring import BatchCostCalculator
        calculator = BatchCostCalculator()
        cost_info = calculator.should_use_batch(image_count, config.BATCH_THRESHOLD)
        
        print(f"💰 コスト分析:")
        print(f"   推定トークン数: {cost_info['estimated_tokens']:,}")
        print(f"   リアルタイム処理: ${cost_info['realtime_cost_usd']:.4f}")
        print(f"   バッチ処理: ${cost_info['batch_cost_usd']:.4f}")
        if cost_info['savings_usd'] > 0:
            print(f"   💡 バッチ処理で ${cost_info['savings_usd']:.4f} ({cost_info['savings_percent']:.1f}%) 節約！")
        print()
    except:
        pass
    
    if BATCH_PROCESSING_AVAILABLE and image_count >= config.BATCH_THRESHOLD:
        print("🚀 利用可能な処理モード:")
        print("1. バッチ処理（推奨）- 50%コスト削減、非同期処理")
        print("2. リアルタイム処理 - 即座に結果取得、通常料金")
        
        while True:
            choice = input("\n処理モードを選択してください (1/2): ").strip()
            if choice == "1":
                print("✅ バッチ処理モードを選択しました")
                return True
            elif choice == "2":
                print("✅ リアルタイム処理モードを選択しました")
                return False
            else:
                print("❌ 1または2を入力してください")
    else:
        if not BATCH_PROCESSING_AVAILABLE:
            print("ℹ️  バッチ処理パッケージが利用できないため、リアルタイム処理で実行します")
        else:
            print(f"ℹ️  画像数が少ない（{image_count} < {config.BATCH_THRESHOLD}）ため、リアルタイム処理で実行します")
        return False


def check_configuration():
    """設定の確認"""
    errors = []
    
    if config.PROJECT_ID == "your-gcp-project-id":
        errors.append("GCPプロジェクトIDが設定されていません (.envファイルでGCP_PROJECT_IDを設定してください)")
    
    google_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not google_creds:
        errors.append("GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていません (.envファイルで設定してください)")
    elif not os.path.exists(google_creds):
        errors.append(f"認証情報ファイルが見つかりません: {google_creds}")
    
    return errors


def main():
    """メイン関数"""
    # コマンドライン引数解析
    args = parse_arguments()
    
    print("=== Anki画像解説カード生成ツール ===")
    logger.info("プログラム開始")
    
    # 設定確認
    config_errors = check_configuration()
    if config_errors:
        for error in config_errors:
            logger.error(error)
            print(f"エラー: {error}")
        print("\nREADME.mdの設定手順を確認してください。")
        return 1
    
    try:
        # 画像フォルダの決定
        images_folder = args.images_folder if args.images_folder else config.IMAGE_FOLDER
        
        # 有効な画像ファイルを事前チェック
        from image_validator import ImageValidator
        validator = ImageValidator()
        image_files = validator.get_valid_images(images_folder)
        
        if not image_files:
            print("処理可能な画像がありませんでした。")
            logger.warning("処理可能な画像なし")
            return 1
        
        # バッチ処理モードの決定
        use_batch_processing = None
        force_batch = False
        
        if args.batch and args.no_batch:
            print("❌ エラー: --batch と --no-batch を同時に指定することはできません")
            return 1
        elif args.batch:
            use_batch_processing = True
            force_batch = True
            print("🚀 コマンドライン引数によりバッチ処理モードを強制有効化")
        elif args.no_batch:
            use_batch_processing = False
            print("⚡ コマンドライン引数によりリアルタイム処理モードを強制有効化")
        elif args.interactive:
            use_batch_processing = interactive_batch_selection(len(image_files))
        else:
            # デフォルト設定を使用
            print(f"📋 設定ファイルに従って処理します（バッチ処理: {config.USE_BATCH_PROCESSING}）")
        
        # カード生成器を初期化
        generator = AnkiCardGenerator(use_batch_processing, force_batch)
        
        # 画像フォルダを処理
        media_files = generator.process_images_folder(images_folder)
        
        # バッチ処理手動モードの場合の特別処理
        if (generator.use_batch_processing and 
            not config.BATCH_WAIT_FOR_COMPLETION and 
            not media_files):
            print(f"\n=== バッチ処理送信完了 ===")
            print(f"バッチジョブが正常に送信されました。")
            print(f"Google Cloudでバッチ処理が実行されます（数分〜数時間）")
            print(f"\n📋 次のステップ:")
            print(f"1. しばらく待機してから以下のコマンドで結果を確認:")
            print(f"   python process_batch.py")
            print(f"2. Google Cloud Console で進捗を確認:")
            print(f"   https://console.cloud.google.com/vertex-ai/batch-predictions")
            logger.info("バッチ処理手動モード: ジョブ送信完了")
            return 0
        elif media_files:
            # outputフォルダを作成
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Ankiデッキをエクスポート
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"anki_image_cards_{timestamp}.apkg"
            generator.export_deck(str(output_file), media_files)
            
            print(f"\n=== 完了 ===")
            print(f"処理した画像数: {len(media_files)}")
            print(f"出力ファイル: {output_file}")
            print(f"Ankiにインポートして使用してください。")
            logger.info(f"プログラム正常終了: {output_file}")
            return 0
        else:
            print("処理可能な画像がありませんでした。")
            logger.warning("処理可能な画像なし")
            return 1
            
    except Exception as e:
        logger.error(f"プログラムエラー: {e}", exc_info=True)
        print(f"エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
