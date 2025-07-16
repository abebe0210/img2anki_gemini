#!/usr/bin/env python3
"""
画像内容と解説文の照合による正しい対応関係の復元
"""

import json
import re
from pathlib import Path
import logging
from google.cloud import storage
from image_validator import ImageValidator
from anki_builder import AnkiCardBuilder
from datetime import datetime
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def intelligent_match_results_to_images(results, image_files):
    """画像ファイル名と解説内容を照合して正しい対応を見つける"""
    matched_pairs = []
    used_results = set()
    
    print("🔍 画像と解説の内容照合を開始...")
    
    for img_idx, image_path in enumerate(image_files):
        best_match_idx = -1
        best_score = 0
        best_reason = ""
        
        print(f"\n📸 画像 {img_idx+1}: {image_path.name}")
        
        for res_idx, result in enumerate(results):
            if res_idx in used_results:
                continue
                
            if "response" in result and result["response"]:
                response = result["response"]
                if "candidates" in response and response["candidates"]:
                    candidate = response["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        description = candidate["content"]["parts"][0]["text"]
                        
                        # 複数の照合方法を試す
                        score, reason = calculate_comprehensive_match_score(
                            image_path.name, description
                        )
                        
                        if score > best_score:
                            best_score = score
                            best_match_idx = res_idx
                            best_reason = reason
        
        if best_match_idx >= 0 and best_score > 0.1:  # 最低スコア閾値
            matched_pairs.append((image_path, results[best_match_idx]))
            used_results.add(best_match_idx)
            print(f"  ✅ マッチ → 結果 {best_match_idx+1} (スコア: {best_score:.2f}, 理由: {best_reason})")
        else:
            print(f"  ❌ マッチする解説が見つかりません")
            # とりあえず使われていない最初の結果を使用
            for res_idx, result in enumerate(results):
                if res_idx not in used_results:
                    matched_pairs.append((image_path, result))
                    used_results.add(res_idx)
                    print(f"  ⚠️  フォールバック → 結果 {res_idx+1}")
                    break
    
    return matched_pairs


def calculate_comprehensive_match_score(filename, description):
    """包括的なマッチングスコアを計算"""
    score = 0
    reasons = []
    
    filename_lower = filename.lower()
    description_lower = description.lower()
    
    # 1. ファイル名の日時と内容の関連性
    date_match = re.search(r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        if year in description or f"{month}/{day}" in description:
            score += 0.3
            reasons.append("日付一致")
    
    # 2. スクリーンショット関連
    if 'screenshot' in filename_lower or 'スクリーンショット' in filename_lower:
        if any(word in description_lower for word in ['画面', 'スクリーン', 'ウィンドウ', 'ブラウザ', 'アプリ']):
            score += 0.4
            reasons.append("スクリーンショット")
    
    # 3. 数学・学習関連
    if any(word in filename_lower for word in ['math', '数学', 'equation', '問題']):
        if any(word in description_lower for word in ['数式', '計算', '数学', '方程式', '関数', '問題']):
            score += 0.5
            reasons.append("数学内容")
    
    # 4. グラフ・チャート関連
    if any(word in filename_lower for word in ['graph', 'chart', 'グラフ', 'チャート']):
        if any(word in description_lower for word in ['グラフ', 'チャート', '軸', 'データ', '分布']):
            score += 0.4
            reasons.append("グラフ")
    
    # 5. 特定の番号や識別子
    number_match = re.search(r'(\d+)', filename)
    if number_match:
        number = number_match.group(1)
        if number in description:
            score += 0.2
            reasons.append(f"番号{number}")
    
    # 6. ファイル拡張子前の単語
    name_part = Path(filename).stem
    words = re.findall(r'[a-zA-Z]+', name_part)
    for word in words:
        if len(word) > 3 and word.lower() in description_lower:
            score += 0.3
            reasons.append(f"単語'{word}'")
    
    # 7. E資格関連の特定パターン
    if any(word in filename_lower for word in ['e資格', 'deep', 'learning', 'ai']):
        if any(word in description_lower for word in ['深層学習', 'ディープラーニング', 'ai', '人工知能', 'ニューラル']):
            score += 0.6
            reasons.append("E資格/AI")
    
    reason_text = ", ".join(reasons) if reasons else "一致なし"
    return score, reason_text


def create_matched_anki_deck(matched_pairs):
    """正しくマッチされたペアからAnkiデッキを作成"""
    try:
        anki_builder = AnkiCardBuilder()
        media_files = []
        successful_cards = 0
        
        print(f"\n🎴 Ankiカード作成開始 ({len(matched_pairs)}ペア)")
        
        for image_path, result in matched_pairs:
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
                                successful_cards += 1
                                print(f"  ✓ {successful_cards:3d}. {image_path.name}")
                            else:
                                print(f"  ✗ カード作成失敗: {image_path.name}")
                else:
                    print(f"  ✗ 無効なレスポンス: {image_path.name}")
                    
            except Exception as e:
                print(f"  ✗ エラー {image_path.name}: {e}")
                continue
        
        if media_files:
            # Ankiデッキをエクスポート
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"anki_batch_cards_matched_{timestamp}.apkg"
            
            anki_builder.export_deck(str(output_file), media_files)
            print(f"\n🎉 内容照合済みAnkiデッキ完成: {output_file}")
            print(f"📊 成功カード数: {successful_cards}/{len(matched_pairs)}")
            return str(output_file)
        else:
            print("\n❌ 作成できたカードがありません")
            return ""
            
    except Exception as e:
        print(f"\n❌ Ankiデッキ作成エラー: {e}")
        return ""


def main():
    """メイン関数"""
    print("=== 画像内容照合による順序修正 ===")
    print("💰 APIコストは発生しません（既存結果を再利用）")
    
    try:
        # 最新のバッチ結果を取得
        from debug_correspondence import find_latest_batch_results, download_and_analyze_results
        
        prefix = find_latest_batch_results()
        if not prefix:
            print("❌ バッチ処理結果が見つかりません")
            return 1
        
        # 画像ファイル一覧を取得
        validator = ImageValidator()
        image_files = validator.get_valid_images("img")
        image_files.sort(key=lambda x: x.name)
        
        # バッチ結果をダウンロード
        bucket_name = f"{config.PROJECT_ID}-anki-batch-processing"
        results = download_and_analyze_results(bucket_name, prefix)
        
        if not results:
            print("❌ バッチ結果を取得できません")
            return 1
        
        print(f"📊 画像ファイル: {len(image_files)}個")
        print(f"📊 バッチ結果: {len(results)}個")
        
        # 内容照合による正しいマッチングを実行
        matched_pairs = intelligent_match_results_to_images(results, image_files)
        
        if not matched_pairs:
            print("❌ マッチングに失敗しました")
            return 1
        
        # 正しい対応でAnkiデッキを作成
        output_file = create_matched_anki_deck(matched_pairs)
        
        if output_file:
            print(f"\n✅ 内容照合による順序修正が完了しました！")
            print(f"📁 新しいファイル: {output_file}")
            print(f"🗑️  古いファイルは削除してOKです")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
