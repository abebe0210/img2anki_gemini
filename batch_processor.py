#!/usr/bin/env python3
"""
バッチ処理モジュール
Vertex AI バッチ予測APIを使用したGeminiバッチ処理
"""

import os
import json
import uuid
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# バッチ処理用のインポート
try:
    from google.cloud import aiplatform
    from google.cloud import storage
    BATCH_PROCESSING_AVAILABLE = True
except ImportError:
    BATCH_PROCESSING_AVAILABLE = False

import config

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Vertex AI バッチ処理管理クラス"""
    
    def __init__(self, project_id: str, location: str):
        """初期化"""
        if not BATCH_PROCESSING_AVAILABLE:
            raise ImportError("バッチ処理パッケージが利用できません")
        
        self.project_id = project_id
        self.location = location
        self.bucket_name = f"{project_id}-anki-batch-processing"
        
        # AI Platform 初期化
        aiplatform.init(project=project_id, location=location)
        self.storage_client = storage.Client()
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """バッチ処理用のCloud Storageバケットを確保"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(
                    self.bucket_name,
                    location=self.location
                )
                logger.info(f"バッチ処理用バケット作成: {self.bucket_name}")
            else:
                logger.info(f"バッチ処理用バケット確認: {self.bucket_name}")
        except Exception as e:
            logger.error(f"バケット作成エラー: {e}")
            raise
    
    def upload_image_to_storage(self, image_path: Path) -> str:
        """画像をCloud Storageにアップロード"""
        blob_name = f"images/{uuid.uuid4()}-{image_path.name}"
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        
        blob.upload_from_filename(str(image_path))
        
        return f"gs://{self.bucket_name}/{blob_name}"
    
    def prepare_batch_requests(self, image_files: List[Path]) -> List[str]:
        """バッチ処理用のリクエストデータを準備"""
        batch_requests = []
        
        for image_path in image_files:
            try:
                # 画像をCloud Storageにアップロード
                image_uri = self.upload_image_to_storage(image_path)
                
                # MIMEタイプ判定
                mime_type = self._get_mime_type(image_path)
                
                # バッチリクエスト形式
                request = {
                    "request": {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {"text": config.PROMPT_TEMPLATE},
                                    {
                                        "fileData": {
                                            "fileUri": image_uri,
                                            "mimeType": mime_type
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                batch_requests.append(json.dumps(request))
                logger.debug(f"バッチリクエスト準備完了: {image_path.name}")
                
            except Exception as e:
                logger.error(f"バッチリクエスト準備エラー {image_path}: {e}")
                continue
        
        return batch_requests
    
    def _get_mime_type(self, image_path: Path) -> str:
        """ファイル拡張子からMIMEタイプを判定"""
        suffix = image_path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        return mime_map.get(suffix, 'image/jpeg')
    
    def upload_batch_input(self, batch_requests: List[str]) -> str:
        """バッチ入力をCloud Storageにアップロード"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"batch_input_{timestamp}.jsonl"
        
        # 一時ファイルに書き込み
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            for request in batch_requests:
                f.write(request + '\n')
            temp_path = f.name
        
        try:
            # Cloud Storageにアップロード
            blob_name = f"batch_inputs/{input_filename}"
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(temp_path)
            
            input_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"バッチ入力アップロード完了: {input_uri}")
            
            return input_uri
            
        finally:
            # 一時ファイル削除
            os.unlink(temp_path)
    
    def create_batch_job(self, input_uri: str, model_name: str) -> str:
        """バッチ予測ジョブを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_name = f"anki-batch-job-{timestamp}"
        output_uri = f"gs://{self.bucket_name}/batch_outputs/{timestamp}/"
        
        try:
            # 同期的作成か非同期的作成かを設定で決定
            sync_create = config.BATCH_JOB_SYNC_CREATE
            
            job = aiplatform.BatchPredictionJob.create(
                job_display_name=job_name,
                model_name=f"publishers/google/models/{model_name}",
                instances_format="jsonl",
                predictions_format="jsonl",
                gcs_source=input_uri,
                gcs_destination_prefix=output_uri,
                sync=sync_create
            )
            
            if sync_create:
                # 同期的作成の場合はすぐにアクセス可能
                job_id = job.name
                logger.info(f"バッチジョブ同期作成完了: {job_id}")
            else:
                # 非同期作成の場合は少し待機してからアクセス
                import time
                time.sleep(2)
                
                # ジョブが作成されるまで少し待機（最大10秒）
                for attempt in range(5):
                    try:
                        job_id = job.name
                        logger.info(f"バッチジョブ非同期作成完了: {job_id}")
                        break
                    except Exception as e:
                        if attempt < 4:
                            logger.debug(f"ジョブ名取得試行 {attempt + 1}/5: {e}")
                            time.sleep(2)
                        else:
                            # 最後の試行でも失敗した場合、job.resource_nameを試す
                            try:
                                job_id = job.resource_name
                                logger.info(f"バッチジョブ作成完了（resource_name使用）: {job_id}")
                                break
                            except Exception:
                                raise e
            
            logger.info(f"出力先: {output_uri}")
            return job_id
                        
        except Exception as e:
            logger.error(f"バッチジョブ作成エラー: {e}")
            raise e
    
    def wait_for_completion(self, job_id: str, timeout: int = 1800) -> List[Dict[str, Any]]:
        """バッチジョブの完了を待機"""
        logger.info("バッチジョブの完了を待機中...")
        
        job = aiplatform.BatchPredictionJob(job_id)
        start_time = time.time()
        
        while True:
            # refresh() メソッドの存在を確認してから使用
            try:
                job.refresh()
            except AttributeError:
                # refresh() メソッドが存在しない場合はスキップ
                pass
            
            # 状態取得の改善
            try:
                if hasattr(job, 'state'):
                    if hasattr(job.state, 'name'):
                        state = job.state.name
                    else:
                        state = str(job.state)
                else:
                    state = job._gca_resource.state.name if hasattr(job._gca_resource, 'state') else "UNKNOWN"
            except Exception as e:
                logger.warning(f"ジョブ状態取得エラー: {e}")
                state = "UNKNOWN"
            
            logger.info(f"ジョブ状態: {state}")
            
            if state == "JOB_STATE_SUCCEEDED":
                logger.info("バッチジョブ完了")
                break
            elif state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
                raise Exception(f"バッチジョブ失敗: {state}")
            elif time.time() - start_time > timeout:
                raise Exception("バッチジョブタイムアウト")
            
            time.sleep(30)  # 30秒間隔でチェック
        
        # 結果を取得
        return self.download_batch_results(job)
    
    def download_batch_results(self, job) -> List[Dict[str, Any]]:
        """バッチ処理結果をダウンロード"""
        results = []
        
        # 出力ファイルを取得
        output_info = job.output_info
        output_location = output_info.gcs_output_directory
        
        # GSパスからバケット名とプレフィックスを抽出
        gs_path = output_location.replace("gs://", "")
        bucket_name, prefix = gs_path.split("/", 1)
        
        bucket = self.storage_client.bucket(bucket_name)
        
        # 結果ファイルをダウンロード
        for blob in bucket.list_blobs(prefix=prefix):
            if blob.name.endswith('.jsonl'):
                content = blob.download_as_text()
                for line in content.strip().split('\n'):
                    if line.strip():
                        results.append(json.loads(line))
        
        logger.info(f"バッチ結果取得完了: {len(results)}件")
        return results


class BatchJobManager:
    """バッチジョブ管理クラス"""
    
    def __init__(self, job_file: str = "batch_jobs.json"):
        self.job_file = Path(job_file)
    
    def save_job_info(self, job_id: str, image_files: List[Path]) -> None:
        """バッチジョブ情報を保存"""
        job_info = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "image_files": [str(path) for path in image_files],
            "status": "RUNNING"
        }
        
        # 既存のジョブ情報を読み込み
        jobs = self._load_jobs()
        jobs.append(job_info)
        
        # ファイルに保存
        with open(self.job_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"ジョブ情報を保存しました: {self.job_file}")
    
    def _load_jobs(self) -> List[Dict[str, Any]]:
        """ジョブ情報を読み込み"""
        if not self.job_file.exists():
            return []
        
        try:
            with open(self.job_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """未完了のジョブ一覧を取得"""
        return self._load_jobs()
    
    def update_jobs(self, remaining_jobs: List[Dict[str, Any]]) -> None:
        """ジョブ情報を更新"""
        with open(self.job_file, 'w', encoding='utf-8') as f:
            json.dump(remaining_jobs, f, ensure_ascii=False, indent=2)
