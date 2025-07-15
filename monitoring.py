#!/usr/bin/env python3
"""
パフォーマンスとリソース使用状況監視モジュール
"""

import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}
    
    def start(self) -> None:
        """監視開始"""
        self.start_time = time.time()
        self.metrics = {
            'start_time': datetime.now().isoformat(),
            'start_memory': psutil.virtual_memory().percent,
            'start_cpu': psutil.cpu_percent()
        }
        logger.info("パフォーマンス監視開始")
    
    def stop(self) -> Dict[str, Any]:
        """監視終了"""
        if self.start_time is None:
            logger.warning("監視が開始されていません")
            return {}
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        self.metrics.update({
            'end_time': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'end_memory': psutil.virtual_memory().percent,
            'end_cpu': psutil.cpu_percent(),
            'peak_memory': psutil.virtual_memory().percent
        })
        
        logger.info(f"処理完了: {duration:.2f}秒")
        return self.metrics
    
    def get_memory_usage(self) -> float:
        """現在のメモリ使用率を取得"""
        return psutil.virtual_memory().percent
    
    def get_disk_usage(self, path: str = ".") -> Dict[str, float]:
        """ディスク使用量を取得"""
        usage = psutil.disk_usage(path)
        return {
            'total_gb': usage.total / (1024**3),
            'used_gb': usage.used / (1024**3),
            'free_gb': usage.free / (1024**3),
            'usage_percent': (usage.used / usage.total) * 100
        }


class ResourceChecker:
    """リソース使用状況チェッククラス"""
    
    @staticmethod
    def check_available_space(min_gb: float = 1.0) -> bool:
        """利用可能ディスク容量をチェック"""
        usage = psutil.disk_usage(".")
        free_gb = usage.free / (1024**3)
        
        if free_gb < min_gb:
            logger.warning(f"ディスク容量不足: {free_gb:.2f}GB < {min_gb}GB")
            return False
        return True
    
    @staticmethod
    def check_memory_usage(max_percent: float = 85.0) -> bool:
        """メモリ使用率をチェック"""
        memory_percent = psutil.virtual_memory().percent
        
        if memory_percent > max_percent:
            logger.warning(f"メモリ使用率が高すぎます: {memory_percent:.1f}% > {max_percent}%")
            return False
        return True
    
    @staticmethod
    def check_image_folder_size(folder_path: str) -> Dict[str, Any]:
        """画像フォルダのサイズをチェック"""
        folder = Path(folder_path)
        if not folder.exists():
            return {'exists': False, 'total_size_mb': 0, 'file_count': 0}
        
        total_size = 0
        file_count = 0
        
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        total_size_mb = total_size / (1024**2)
        
        return {
            'exists': True,
            'total_size_mb': round(total_size_mb, 2),
            'file_count': file_count,
            'avg_size_mb': round(total_size_mb / file_count, 2) if file_count > 0 else 0
        }


class BatchCostCalculator:
    """バッチ処理コスト計算クラス"""
    
    def __init__(self):
        # Gemini 1.5 Flash の料金 (2024年現在の参考値)
        self.realtime_cost_per_1k_tokens = 0.000075  # USD
        self.batch_cost_per_1k_tokens = 0.0000375    # USD (50% off)
        self.avg_tokens_per_image = 1000  # 推定値
    
    def calculate_savings(self, image_count: int) -> Dict[str, float]:
        """コスト削減効果を計算"""
        total_tokens = image_count * self.avg_tokens_per_image
        
        realtime_cost = (total_tokens / 1000) * self.realtime_cost_per_1k_tokens
        batch_cost = (total_tokens / 1000) * self.batch_cost_per_1k_tokens
        
        savings = realtime_cost - batch_cost
        savings_percent = (savings / realtime_cost) * 100 if realtime_cost > 0 else 0
        
        return {
            'image_count': image_count,
            'estimated_tokens': total_tokens,
            'realtime_cost_usd': round(realtime_cost, 4),
            'batch_cost_usd': round(batch_cost, 4),
            'savings_usd': round(savings, 4),
            'savings_percent': round(savings_percent, 1)
        }
    
    def should_use_batch(self, image_count: int, threshold: int = 10) -> Dict[str, Any]:
        """バッチ処理を使用すべきかの判定"""
        cost_analysis = self.calculate_savings(image_count)
        
        recommendation = {
            'use_batch': image_count >= threshold,
            'reason': '',
            **cost_analysis
        }
        
        if image_count >= threshold:
            recommendation['reason'] = f"バッチ処理推奨: ${cost_analysis['savings_usd']:.4f} ({cost_analysis['savings_percent']:.1f}%) のコスト削減"
        else:
            recommendation['reason'] = f"リアルタイム処理推奨: 画像数が少ない ({image_count} < {threshold})"
        
        return recommendation
