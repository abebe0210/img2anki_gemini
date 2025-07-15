#!/usr/bin/env python3
"""
Ankiカード生成モジュール
genankiを使用したAnkiカードとデッキの生成
"""

import os
import genanki
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

import config

logger = logging.getLogger(__name__)


class AnkiCardBuilder:
    """Ankiカード構築クラス"""
    
    def __init__(self):
        """初期化"""
        self.model = self._create_anki_model()
        self.deck = genanki.Deck(config.DECK_ID, config.DECK_NAME)
        logger.info(f"Ankiデッキ作成完了: {config.DECK_NAME}")
    
    def _create_anki_model(self) -> genanki.Model:
        """Ankiモデルを作成"""
        return genanki.Model(
            config.MODEL_ID,
            '画像解説カード',
            fields=[
                {'name': 'Image'},
                {'name': 'Description'},
                {'name': 'Timestamp'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                    <div style="text-align: center; margin-bottom: 15px;">
                        {{Image}}
                    </div>
                    <div style="text-align: center; font-size: 11px; opacity: 0.7; margin-top: 10px;">
                        作成日時: {{Timestamp}}
                    </div>
                    ''',
                    'afmt': '''
                    {{FrontSide}}
                    <hr id="answer">
                    <div class="description">
                        <div class="image-description">{{Description}}</div>
                    </div>
                    
                    <script type="text/javascript">
                    // MathJax設定とTeX数式表示の有効化
                    if (typeof MathJax !== 'undefined') {
                        MathJax.Hub.Config({
                            tex2jax: {
                                inlineMath: [['\\\\(', '\\\\)']],
                                displayMath: [['\\\\[', '\\\\]']],
                                processEscapes: true,
                                processEnvironments: true
                            },
                            "HTML-CSS": {
                                styles: {
                                    ".MathJax": {
                                        "color": "inherit !important"
                                    }
                                }
                            }
                        });
                        MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
                    }
                    </script>
                    ''',
                },
            ],
            css=self._get_card_css()
        )
    
    def _get_card_css(self) -> str:
        """カードのCSSスタイルを取得"""
        return """
        /* ベーススタイル（ライトテーマ・ダークテーマ対応） */
        .card {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            text-align: left;
            color: var(--canvas-default);
            background-color: var(--canvas-default-bg);
            padding: 15px;
            line-height: 1.6;
            max-width: 100%;
            margin: 0 auto;
            box-sizing: border-box;
            font-size: 14px;
            word-wrap: break-word;
        }
        
        /* Ankiテーマに対応したフォールバック色 */
        @media (prefers-color-scheme: light) {
            .card {
                color: #1a1a1a !important;
                background-color: #ffffff !important;
            }
        }
        
        @media (prefers-color-scheme: dark) {
            .card {
                color: #e0e0e0 !important;
                background-color: #1e1e1e !important;
            }
        }
        
        /* Android Anki対応（強制色設定） */
        .card * {
            color: inherit !important;
        }
        
        img {
            max-width: 100%;
            max-height: 300px;
            height: auto;
            width: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            display: block;
            margin: 10px auto;
            user-select: none;
            -webkit-user-select: none;
        }
        
        .description {
            margin-top: 15px;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #007acc;
            background-color: rgba(120, 120, 120, 0.1);
            color: inherit !important;
        }
        
        /* Geminiが生成するHTML用スタイル */
        .image-description h3 {
            color: #007acc !important;
            font-size: 16px !important;
            margin: 12px 0 8px 0 !important;
            padding-bottom: 4px !important;
            border-bottom: 1px solid rgba(120, 120, 120, 0.3) !important;
            font-weight: bold !important;
        }
        
        .image-description ul {
            margin: 8px 0 !important;
            padding-left: 18px !important;
        }
        
        .image-description li {
            margin: 4px 0 !important;
            line-height: 1.4 !important;
            color: inherit !important;
        }
        
        .image-description strong {
            font-weight: 600 !important;
            color: inherit !important;
        }
        
        .image-description p {
            color: inherit !important;
            margin: 8px 0 !important;
        }
        
        /* 情報ボックス */
        .learning-points, .related-info {
            border-radius: 6px;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid rgba(120, 120, 120, 0.3);
            background-color: rgba(120, 120, 120, 0.1);
            color: inherit !important;
        }
        
        .learning-points {
            border-color: rgba(0, 122, 204, 0.4);
            background-color: rgba(0, 122, 204, 0.1);
        }
        
        .related-info {
            border-color: rgba(255, 99, 71, 0.4);
            background-color: rgba(255, 99, 71, 0.1);
        }
        
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, #007acc, transparent);
            margin: 15px 0;
        }
        
        /* TeX数式表示スタイル */
        .MathJax {
            color: inherit !important;
        }
        
        .MathJax_Display {
            margin: 1em 0 !important;
            text-align: center !important;
        }
        
        .MathJax_Preview {
            color: inherit !important;
        }
        
        /* インライン数式 */
        .MathJax .math {
            color: inherit !important;
            background-color: transparent !important;
        }
        
        /* ブロック数式 */
        .MathJax_Display .math {
            background-color: rgba(120, 120, 120, 0.05) !important;
            padding: 8px 12px !important;
            border-radius: 4px !important;
            border: 1px solid rgba(120, 120, 120, 0.2) !important;
            margin: 10px 0 !important;
        }
        
        /* スマホ向け追加スタイル */
        @media screen and (max-width: 480px) {
            .card {
                padding: 10px;
                font-size: 13px;
            }
            
            img {
                max-height: 250px;
                margin: 8px auto;
            }
            
            .description {
                padding: 10px;
                margin-top: 10px;
            }
            
            .image-description h3 {
                font-size: 15px !important;
            }
            
            /* モバイルでの数式表示調整 */
            .MathJax_Display .math {
                font-size: 0.9em !important;
                padding: 6px 8px !important;
            }
            
            .MathJax {
                font-size: 0.9em !important;
            }
        }
        
        /* ダークモードでの数式表示調整 */
        @media (prefers-color-scheme: dark) {
            .MathJax_Display .math {
                background-color: rgba(255, 255, 255, 0.05) !important;
                border-color: rgba(255, 255, 255, 0.2) !important;
            }
            
            .MathJax {
                color: #e0e0e0 !important;
            }
        }
        """
    
    def create_card(self, image_path: str, description: str) -> Optional[str]:
        """Ankiカードを作成"""
        try:
            # 画像ファイル名を取得
            image_filename = os.path.basename(image_path)
            
            # HTMLで画像を表示
            image_html = f'<img src="{image_filename}" alt="{image_filename}">'
            
            # 解説文の処理
            description_html = self._process_description(description)
            
            # タイムスタンプ
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Ankiノート作成
            note = genanki.Note(
                model=self.model,
                fields=[image_html, description_html, timestamp]
            )
            
            self.deck.add_note(note)
            logger.info(f"Ankiカード作成完了: {image_filename}")
            
            return image_filename
            
        except Exception as e:
            logger.error(f"Ankiカード作成エラー: {image_path} - {e}")
            return None
    
    def _process_description(self, description: str) -> str:
        """解説文の処理（HTMLタグチェック等）"""
        if '<div class="image-description">' in description:
            return description
        else:
            # HTMLタグがない場合の処理（フォールバック）
            return f'<div class="image-description"><p>{description.replace(chr(10), "</p><p>")}</p></div>'
    
    def export_deck(self, output_path: str, media_files: Optional[List[str]] = None) -> None:
        """Ankiデッキをapkgファイルとしてエクスポート"""
        try:
            package = genanki.Package(self.deck)
            
            # メディアファイルがある場合は追加
            if media_files:
                package.media_files = media_files
                logger.info(f"メディアファイル追加: {len(media_files)}個")
            
            package.write_to_file(output_path)
            logger.info(f"Ankiデッキエクスポート完了: {output_path}")
            
        except Exception as e:
            logger.error(f"エクスポートエラー: {e}")
            raise
    
    def get_card_count(self) -> int:
        """デッキ内のカード数を取得"""
        return len(self.deck.notes)
