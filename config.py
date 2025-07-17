"""
Anki画像解説カード生成ツール - 設定管理
環境変数ベースの設定管理システム
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# Google Cloud Platform設定
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'your-gcp-project-id')
LOCATION = os.getenv('GCP_LOCATION', 'asia-northeast1')

# Geminiモデル設定
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')

# Anki設定
DECK_NAME = os.getenv('ANKI_DECK_NAME', '画像解説カード')
MODEL_ID = int(os.getenv('ANKI_MODEL_ID', '1607392319'))
DECK_ID = int(os.getenv('ANKI_DECK_ID', '2059400110'))

# ディレクトリ設定
IMAGE_FOLDER = os.getenv('IMAGE_FOLDER', './img')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', './output')
CREDENTIALS_FOLDER = os.getenv('CREDENTIALS_FOLDER', './credentials')
# 処理設定
API_WAIT_TIME = int(os.getenv('API_WAIT_TIME', '1'))
MAX_RETRY_COUNT = int(os.getenv('MAX_RETRY_COUNT', '3'))
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2048'))  # ピクセル
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

# バッチ処理設定
BATCH_THRESHOLD = int(os.getenv('BATCH_THRESHOLD', '10'))  # バッチ処理を使用する最小画像数
USE_BATCH_PROCESSING = os.getenv('USE_BATCH_PROCESSING', 'true').lower() == 'true'  # バッチ処理を使用するかどうか
BATCH_WAIT_FOR_COMPLETION = os.getenv('BATCH_WAIT_FOR_COMPLETION', 'false').lower() == 'true'  # バッチ完了まで待機するか
BATCH_JOB_SYNC_CREATE = os.getenv('BATCH_JOB_SYNC_CREATE', 'false').lower() == 'true'  # バッチジョブ作成を同期的に行うか

# Google認証情報の設定
google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if google_credentials:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'anki_generator.log')

def validate_config():
    """設定の検証"""
    errors = []
    
    if PROJECT_ID == 'your-gcp-project-id':
        errors.append("GCP_PROJECT_IDが設定されていません")
    
    if google_credentials and not Path(google_credentials).exists():
        errors.append(f"認証情報ファイルが見つかりません: {google_credentials}")
    
    # 必要なディレクトリの確認
    for folder in [IMAGE_FOLDER, OUTPUT_FOLDER, CREDENTIALS_FOLDER]:
        if not Path(folder).exists():
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    return errors

# プロンプト設定
PROMPT_TEMPLATE = """
画像のE資格(ディープラーニングの資格)の例題について、Ankiカードの裏面に表示する解説文を日本語で作成してください。

以下の構造で、HTML形式を使って見やすく整理してください：

**出力形式:**
<div class="image-description">
<h3>📋 解答</h3>
<p>[正解の選択肢:何番目かと選択肢の抜粋]</p>

<h3>🔍 問題解説</h3>
<p>[問題のわかりやすい解説]</p>

<h3>💡 学習ポイント</h3>
<div class="learning-points">
<p>[画像の問題を解くためのポイント]</p>
</div>

<h3>📚 関連知識</h3>
<div class="related-info">
<p>[E資格の文脈における、背景知識、豆知識、関連する概念など]</p>
</div>
</div>

**重要な指示:**
- 指定された出力形式以外の内容は不要です（「わかりました」など）
- 各セクションは必ず含めてください
- HTMLタグを正確に使用してください
- 解説は簡潔で初学者にとっても分かりやすいものに
- E資格の文脈において学習に役立つ実践的な内容を重視
- 専門用語は適度に説明を加える
- 箇条書きや強調を効果的に使用
- 数式がある場合は必ずTeX（LaTeX）形式で記述してください。AnkiのMathJaxで正しく表示されるように、以下の形式を使用してください。
  - インライン数式: \(...\) 例: \(x^2 + y^2 = z^2\)
  - ブロック数式: \[...\] 例: \[E = mc^2\]
- 数式は積極的にTeX形式で表現する
"""
