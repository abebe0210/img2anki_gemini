# 📚 Anki画像解説カード生成ツール

画像ファイルからGemini（Vertex AI）を使用して解説文を自動生成し、Ankiの学習カードを作成するツールです。

## 🚀 クイックスタート

```powershell
python run.py
```

**このコマンド一つで全て完了！**
- 必要パッケージの自動インストール
- 環境設定ファイルの自動作成
- フォルダの自動作成
- 設定確認と実行
- **NEW**: インタラクティブなバッチ処理選択

## 💰 バッチ処理でコスト削減

**10個以上の画像を処理する場合、自動的にバッチ処理モードに切り替わり、料金が50%削減されます！**

### 🎛️ 手動切り替えオプション

#### 1. インタラクティブモード（推奨）
```powershell
python run.py  # 実行時に処理方法を選択
# または
python main.py --interactive
```
実行時にバッチ処理かリアルタイム処理かを対話的に選択できます。

#### 2. 高度な選択ツール（NEW!）
```powershell
python mode_selector.py  # 視覚的で分かりやすいモード選択
```
コスト分析と詳細説明付きで処理モードを選択できます。

#### 3. コマンドライン指定
```powershell
# バッチ処理を強制的に有効化（画像数制限を無視）
python main.py --batch

# リアルタイム処理を強制的に有効化  
python main.py --no-batch

# インタラクティブ選択
python main.py --interactive

# 画像フォルダを指定
python main.py --images-folder ./my-images
```

**💡 重要**: 
- `--batch`フラグを使用すると、通常の画像数制限（10個以上）を無視して、1個の画像でもバッチ処理を実行できます
- `--batch`指定時は、エラーが発生してもリアルタイム処理にフォールバックしません（意図を尊重）

#### 4. 設定ファイル
```env
# .envファイルでデフォルト動作を設定
USE_BATCH_PROCESSING=true  # デフォルトでバッチ処理
BATCH_THRESHOLD=10         # バッチ処理を使用する最小画像数
```

### バッチ処理の特徴
- 📉 **コスト削減**: 通常料金の50%OFF
- ⚡ **効率的**: 大量画像の一括処理
- 🔄 **自動切換**: 10個以上で自動有効化
- 🛡️ **強制モード**: `--batch`指定時はフォールバックなし
- � **安定性**: パッケージ不足時のみリアルタイム処理に切替

### 🚀 推奨：手動実行モード

バッチ処理は非同期で実行されるため、手動実行モードがおすすめです：

```powershell
# 1. バッチジョブを送信（即座に完了）
python run.py

# 2. 後でバッチ結果を処理（ジョブ完了後に実行）
python process_batch.py
```

### ⚙️ バッチ処理モード設定

```env
# 手動実行モード（推奨）- ジョブ送信後すぐに終了
BATCH_WAIT_FOR_COMPLETION=false

# 自動待機モード - ジョブ完了まで30分間待機
BATCH_WAIT_FOR_COMPLETION=true
```

### 📋 バッチ処理の流れ

1. **ジョブ送信**: `python run.py` でバッチジョブを送信
2. **待機**: Google Cloudでバッチ処理が実行される（数分〜数時間）
3. **結果処理**: `python process_batch.py` で完了したジョブを処理
4. **Ankiカード生成**: APKGファイルが自動生成される

### 🎛️ 実行オプション一覧

```powershell
# === 推奨：簡単実行スクリプト ===
python run.py                       # インタラクティブ選択 + 自動セットアップ
python mode_selector.py             # 🆕 高度な選択ツール（コスト分析付き）
python batch_mode.py                # バッチ処理専用
python realtime_mode.py             # リアルタイム処理専用

# === 直接実行（上級者向け） ===
python main.py                      # 設定ファイルに従って実行
python main.py --interactive        # 処理方法を対話的に選択
python main.py --batch              # バッチ処理を強制実行（画像数制限無視）
python main.py --no-batch           # リアルタイム処理を強制実行
python main.py --images-folder ./my-images  # 画像フォルダを指定

# === バッチ処理結果の確認・処理 ===
python process_batch.py             # 完了したバッチジョブを処理
```

### 🎯 どのスクリプトを使うべきか？

| スクリプト | 用途 | 特徴 |
|---|---|---|
| `python run.py` | **初心者推奨** | 全自動セットアップ + インタラクティブ選択 |
| `python mode_selector.py` | **🆕 視覚的選択** | コスト分析付き詳細選択ツール |
| `python batch_mode.py` | **大量画像処理** | バッチ処理専用、50%コスト削減 |
| `python realtime_mode.py` | **少量・急ぎ** | リアルタイム処理専用、即座に結果 |
| `python main.py --interactive` | **柔軟な制御** | コマンドライン + インタラクティブ |

### 🔍 ジョブ状況確認

```powershell
# バッチジョブの状況確認
python process_batch.py

# Google Cloud Console での確認
# https://console.cloud.google.com/vertex-ai/batch-predictions
```

### 設定カスタマイズ
`.env`ファイルでバッチ処理をカスタマイズ可能：

```env
# バッチ処理を使用するかどうか（true/false）
USE_BATCH_PROCESSING=true

# バッチ処理を使用する最小画像数（デフォルト: 10）
BATCH_THRESHOLD=10

# バッチ完了まで待機するか（手動処理推奨: false）
BATCH_WAIT_FOR_COMPLETION=false

# バッチジョブ作成を同期的に行うか（エラー回避: true推奨）
BATCH_JOB_SYNC_CREATE=false
```

## 📁 プロジェクト構造

```
anki/
├── main.py              # メインプログラム
├── run.py               # 🌟統合実行・セットアップスクリプト
├── mode_selector.py     # 🆕高度な処理モード選択ツール
├── batch_mode.py        # 🚀バッチ処理専用スクリプト
├── realtime_mode.py     # ⚡リアルタイム処理専用スクリプト
├── process_batch.py     # バッチ結果処理スクリプト
├── config.py            # 設定管理
├── requirements.txt     # 必要パッケージ
├── .env                 # 環境設定（作成後）
├── .env.example         # 環境設定テンプレート
├── .gitignore           # Git除外設定
├── credentials/         # 認証情報フォルダ
│   └── README.md
├── img/                 # 処理対象画像フォルダ
└── output/              # 生成されたAPKGファイル
```

## �️ 初回セットアップ

### 1. Google Cloud Platform (GCP) の設定

#### 1.1 プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. プロジェクトIDをメモしておく

#### 1.2 Vertex AI APIの有効化
1. GCPコンソールで「APIとサービス」→「ライブラリ」へ移動
2. "Vertex AI API" を検索して有効化

#### 1.3 サービスアカウントの作成
1. 「IAMと管理」→「サービスアカウント」で新規作成
2. 設定：
   - 名前: `anki-generator`
   - 役割: `Vertex AI User`
3. JSONキーをダウンロード

### 2. ローカル設定

#### 2.1 環境設定
```powershell
python run.py
```
実行後、自動作成される `.env` ファイルを編集：

```env
# 必須設定
GCP_PROJECT_ID=your-actual-project-id

# 認証情報ファイルのパス
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-key.json

# オプション設定
GCP_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.5-flash
ANKI_DECK_NAME=画像解説カード
```

#### 2.2 認証情報配置
ダウンロードしたJSONファイルを `credentials/` フォルダに配置

#### 2.3 画像配置
処理したい画像を `img/` フォルダに配置

## 🎯 機能

### ✨ 主要機能
- **自動画像解析**: Gemini AIによる高精度な画像内容分析
- **💰 バッチ処理**: 10個以上の画像で50%コスト削減
- **構造化解説**: 概要・詳細・学習ポイント・関連知識の4段階構成
- **TeX数式対応**: 数学・物理・化学式を美しく表示
- **レスポンシブデザイン**: デスクトップ・モバイル・ダークモード対応
- **Anki完全互換**: APKGファイル形式でエクスポート

### 📱 表示サポート
- **デスクトップAnki**: Windows, Mac, Linux
- **モバイルAnki**: iOS, Android
- **ダークモード**: 全プラットフォーム対応
- **TeX数式**: MathJax による美しい数式表示

### 🎨 カード構成
- **表面**: 画像 + 作成日時
- **裏面**: 
  - 📋 概要
  - 🔍 詳細解説  
  - 💡 学習ポイント
  - 📚 関連知識

## 🔧 使用方法

### 基本的な使い方
1. 画像を `img/` フォルダに配置
2. `python run.py` を実行
3. 処理方法を選択（インタラクティブモード時）
4. 生成された `.apkg` ファイルをAnkiにインポート

### 処理方法の選択指針
- **バッチ処理**: 10個以上の画像、50%コスト削減、非同期処理
- **リアルタイム処理**: 即座に結果が欲しい場合、少量の画像

### コマンドライン実行例
```powershell
# 基本実行（推奨）
python run.py

# バッチ処理で実行
python main.py --batch

# リアルタイム処理で実行
python main.py --no-batch

# 別フォルダの画像を処理
python main.py --images-folder C:\MyImages --interactive
```

### 対応画像形式
- JPG/JPEG
- PNG  
- GIF
- BMP

### TeX数式記法
数学的な内容は自動的にTeX形式で生成されます：
- インライン数式: `\(E = mc^2\)`
- ブロック数式: `\[x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}\]`

## 🚨 トラブルシューティング

### よくある問題

**1. 認証エラー**
```
解決: .envファイルのGCP_PROJECT_IDとGOOGLE_APPLICATION_CREDENTIALSを確認
```

**2. パッケージエラー**
```powershell
pip install --upgrade google-cloud-aiplatform
```

**3. 画像が処理されない**
```
解決: imgフォルダに対応形式の画像があることを確認
```

**4. 数式が表示されない**
```
解決: AnkiでMathJaxアドオンが有効になっていることを確認
```

### ログ確認
エラーの詳細は `anki_generator.log` ファイルで確認できます。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能要求は、GitHubのIssuesでお気軽にご連絡ください。

---

**Happy Learning with Anki! 📚✨**
- HTML形式の美しい解説レイアウト

## ⚙️ 環境変数設定

`.env`ファイルで設定を管理（自動作成されます）：

```env
# GCP設定
GCP_PROJECT_ID=your-actual-project-id
GCP_LOCATION=asia-northeast1
GEMINI_MODEL=gemini-2.5-flash

# 認証情報
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-key.json

# Anki設定
ANKI_DECK_NAME=画像解説カード

# バッチ処理設定（コスト削減）
USE_BATCH_PROCESSING=true
BATCH_THRESHOLD=10
```

## �️ 画像の準備

`img`フォルダに処理したい画像ファイルを配置してください。
**サポート形式**：JPG, JPEG, PNG, GIF, BMP

## 🎨 生成される解説の特徴

最新版では、Ankiカードの裏面に最適化されたHTML形式での解説生成：

### 解説の構造
1. **📋 概要** - 画像の基本的な内容
2. **🔍 詳細解説** - 主要な要素、注目ポイント、技術的側面
3. **💡 学習ポイント** - 重要な概念や知識
4. **📚 関連知識** - 背景知識や豆知識

### HTML出力の特徴
- 構造化されたHTML形式で見やすい表示
- セクションごとに色分けされた背景
- 絵文字アイコンで視覚的に分かりやすく
- Ankiカードでの表示に最適化されたスタイル

## 🔧 上級者向け（手動実行）

直接メインプログラムを実行したい場合：

```powershell
# パッケージインストール
pip install -r requirements.txt

# プログラム実行
python main_enhanced.py  # 推奨（ログ機能付き）
# または
python main.py          # 基本版
```

## 📁 ファイル構成

```
anki/
├── img/                         # 画像フォルダ
├── credentials/                 # 認証情報フォルダ
│   ├── README.md               # 認証情報の説明
│   └── service-account-key.json # GCPサービスアカウントキー
├── run_anki.py                 # 🚀統合実行スクリプト（メイン）
├── main_enhanced.py            # 改良版メインプログラム
├── main.py                     # 基本版メインプログラム  
├── config.py                   # 設定ファイル
├── .env                        # 環境変数設定ファイル
├── .env.example               # 環境変数設定テンプレート
├── requirements.txt           # 必要パッケージ
├── README.md                  # このファイル
├── SETUP.md                   # 詳細セットアップガイド
└── anki_image_cards_*.apkg    # 生成されるAnkiデッキ
```

## 🔧 Ankiへのインポート

1. Ankiアプリを起動
2. 「ファイル」→「インポート」を選択
3. 生成された`anki_image_cards_*.apkg`ファイルを選択
4. インポート設定を確認して実行

## ❓ トラブルシューティング

### よくあるエラー

1. **認証エラー**
   ```
   認証情報ファイルが見つかりません
   ```
   **対処法**：
   - `.env`ファイルの`GCP_PROJECT_ID`を設定
   - `credentials`フォルダにJSONファイルを配置

2. **パッケージエラー**
   ```
   ModuleNotFoundError: No module named 'genanki'
   ```
   **対処法**：
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **画像なしエラー**
   ```
   処理可能な画像ファイルがありません
   ```
   **対処法**：
   - `img`フォルダに画像ファイル（JPG、PNG等）を配置

4. **API制限エラー**
   ```
   Gemini API エラー: 429 Too Many Requests
   ```
   **対処法**：
   - しばらく待ってから再実行
   - `.env`の`API_WAIT_TIME`を増やす

### ログの確認

実行時に詳細なログが表示されます。エラーが発生した場合は、ログメッセージを確認してください。

## ⚡ カスタマイズ

### プロンプトの変更
`config.py`の`PROMPT_TEMPLATE`を編集してGeminiへの指示をカスタマイズ

### カードデザインの変更  
`main_enhanced.py`のCSSセクションを編集してカードの見た目を変更

### API設定の調整
`.env`ファイルで`API_WAIT_TIME`や`MAX_RETRY_COUNT`を調整

## 📱 スマホAnkiでの使用について

このツールで生成されたカードは、スマホ版Ankiでも見やすく表示されるよう最適化されています：

### 表示の特徴
- **ライト・ダークテーマ対応**：Ankiのテーマ設定に自動で適応
- **レスポンシブデザイン**：画面サイズに応じてフォント・画像サイズを調整
- **色彩の最適化**：背景とのコントラストを保ち、文字の可読性を向上

### スマホでの推奨設定
1. **Anki設定**：
   - 「設定」→「表示」→「カードの最大幅」を80-90%に設定
   - 「画質を向上」をオンに設定

2. **フォントサイズ調整**：
   - 「設定」→「表示」→「フォントサイズ」で好みに調整
   - 画面が小さい場合は「小」を推奨

3. **表示モード**：
   - ダークテーマ使用時も文字色が自動調整されます
   - 「夜間モード」と組み合わせて使用可能

### トラブルシューティング（スマホ表示）
- **文字が見えない場合**：Ankiの「表示」設定でテーマを変更してみてください
- **画像が大きすぎる場合**：画像をタップして拡大・縮小可能です
- **レイアウトが崩れる場合**：デッキオプションで「HTML表示」をオンにしてください

## ⚠️ 注意事項

- Vertex AI APIの使用には料金が発生する場合があります
- 大量の画像処理時はAPI利用制限にご注意ください
- 生成される解説文の品質は画像の内容とプロンプト設定に依存します
- 機密性の高い画像の処理にはご注意ください
