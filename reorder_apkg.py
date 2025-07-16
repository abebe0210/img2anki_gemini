#!/usr/bin/env python3
"""
既存APKGファイルの順序修正ツール
画像ファイル名の昇順でカードを再構成
"""

import json
import sqlite3
import tempfile
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import logging
from anki_builder import AnkiCardBuilder
from image_validator import ImageValidator

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_cards_from_apkg(apkg_path: str) -> list:
    """APKGファイルからカード情報を抽出"""
    cards = []
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # APKGファイルを展開
            with zipfile.ZipFile(apkg_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            # SQLiteデータベースを読み込み
            db_path = Path(temp_dir) / 'collection.anki2'
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # ノート（カード）情報を取得
                cursor.execute("SELECT flds FROM notes ORDER BY id")
                rows = cursor.fetchall()
                
                for fields_str, in rows:
                    field_list = fields_str.split('\x1f')  # Ankiのフィールド区切り文字
                    if len(field_list) >= 2:
                        image_field = field_list[0]  # 画像フィールド
                        description_field = field_list[1]  # 解説フィールド
                        timestamp_field = field_list[2] if len(field_list) > 2 else ""
                        
                        # 画像ファイル名を抽出
                        import re
                        img_match = re.search(r'src="([^"]+)"', image_field)
                        if img_match:
                            img_name = img_match.group(1)
                            cards.append({
                                'image_name': img_name,
                                'image_field': image_field,
                                'description': description_field,
                                'timestamp': timestamp_field
                            })
                
                conn.close()
                logger.info(f"抽出したカード数: {len(cards)}")
                
    except Exception as e:
        logger.error(f"APKG抽出エラー: {e}")
    
    return cards


def get_sorted_image_files():
    """imgフォルダから画像ファイルをファイル名昇順で取得"""
    validator = ImageValidator()
    image_files = validator.get_valid_images("img")
    
    # ファイル名で昇順ソート
    image_files.sort(key=lambda x: x.name.lower())
    
    logger.info(f"ソート済み画像ファイル数: {len(image_files)}")
    for i, img in enumerate(image_files[:10]):  # 最初の10個を表示
        logger.info(f"  {i+1:2d}. {img.name}")
    
    return image_files


def match_cards_to_images(cards: list, image_files: list) -> list:
    """カードと画像ファイルを正しく対応させる"""
    matched_pairs = []
    
    # 画像ファイル名をキーとした辞書を作成
    card_dict = {card['image_name']: card for card in cards}
    
    print(f"\n🔄 画像ファイル名昇順での対応:")
    
    for i, image_path in enumerate(image_files):
        img_name = image_path.name
        
        if img_name in card_dict:
            card = card_dict[img_name]
            matched_pairs.append((image_path, card))
            print(f"  {i+1:3d}. {img_name} ✓")
        else:
            print(f"  {i+1:3d}. {img_name} ❌ (対応するカードなし)")
            # 対応するカードがない場合はスキップ
    
    logger.info(f"マッチしたペア数: {len(matched_pairs)}")
    return matched_pairs


def create_ordered_apkg(matched_pairs: list) -> str:
    """正しい順序でAPKGファイルを作成"""
    try:
        anki_builder = AnkiCardBuilder()
        media_files = []
        
        print(f"\n🎴 ファイル名昇順でAPKG作成:")
        
        for i, (image_path, card) in enumerate(matched_pairs):
            try:
                # 既存の解説を使用してカードを作成
                description = card['description']
                
                # Ankiカード作成
                image_filename = anki_builder.create_card(str(image_path), description)
                
                if image_filename:
                    media_files.append(str(image_path))
                    print(f"  {i+1:3d}. ✓ {image_path.name}")
                else:
                    print(f"  {i+1:3d}. ✗ {image_path.name} (カード作成失敗)")
                    
            except Exception as e:
                print(f"  {i+1:3d}. ✗ {image_path.name} (エラー: {e})")
                continue
        
        if media_files:
            # 出力ディレクトリを作成
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # タイムスタンプ付きファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"anki_cards_sorted_{timestamp}.apkg"
            
            # APKGファイルをエクスポート
            anki_builder.export_deck(str(output_file), media_files)
            
            print(f"\n✅ ファイル名昇順APKGファイル作成完了!")
            print(f"📁 ファイル: {output_file}")
            print(f"📊 カード数: {len(media_files)}")
            
            return str(output_file)
        else:
            print(f"\n❌ 作成できたカードがありません")
            return ""
            
    except Exception as e:
        logger.error(f"APKG作成エラー: {e}")
        return ""


def main():
    """メイン関数"""
    print("=== 既存APKGファイルの順序修正ツール ===")
    print("📋 imgファイル名の昇順でカードを再構成します")
    
    # 既存のAPKGファイルパス
    apkg_path = "output/anki_batch_cards_20250716_163710.apkg"
    
    if not Path(apkg_path).exists():
        print(f"❌ APKGファイルが見つかりません: {apkg_path}")
        return 1
    
    try:
        # 1. 既存APKGからカード情報を抽出
        print(f"\n📥 既存APKGファイルからカード抽出中...")
        cards = extract_cards_from_apkg(apkg_path)
        
        if not cards:
            print("❌ カード情報を抽出できませんでした")
            return 1
        
        print(f"✅ {len(cards)}枚のカードを抽出")
        
        # 2. imgフォルダから画像ファイルを昇順で取得
        print(f"\n📁 imgフォルダから画像ファイル取得中...")
        image_files = get_sorted_image_files()
        
        if not image_files:
            print("❌ 有効な画像ファイルがありません")
            return 1
        
        # 3. カードと画像ファイルを対応させる
        print(f"\n🔗 カードと画像ファイルの対応付け...")
        matched_pairs = match_cards_to_images(cards, image_files)
        
        if not matched_pairs:
            print("❌ 対応するペアがありません")
            return 1
        
        # 4. 正しい順序でAPKGファイルを作成
        output_file = create_ordered_apkg(matched_pairs)
        
        if output_file:
            print(f"\n🎉 順序修正が完了しました!")
            print(f"📱 新しいファイルをAnkiにインポートしてください")
            print(f"🗑️  古いファイル ({apkg_path}) は削除してOKです")
            return 0
        else:
            print(f"\n❌ APKGファイルの作成に失敗しました")
            return 1
            
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        print(f"❌ エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
