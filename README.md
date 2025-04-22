# youtube-data-collector

指定したYouTubeチャンネルの動画データを収集し、再生回数、コメント数などを含むExcelファイルを生成するPythonスクリプト。

## 概要

このプロジェクトは、YouTube Data APIを使用して指定したYouTubeチャンネルから動画情報を収集し、再生回数、イイネ数、コメント数などを含むExcelファイルとして出力するPythonスクリプトです。特定の期間にアップロードされた動画データを抽出し、指定した条件に基づいてデータをフィルタリングします。

## 機能

- YouTube APIを利用して、指定したチャンネルの動画情報を取得。
- 動画の再生回数、イイネ数、コメント数を収集。
- ショート動画と長編動画の分類（最大180秒：ショート、それ以上：長編）。
- 特定の日付範囲（`PUBLISHED_AFTER`, `PUBLISHED_BEFORE`）でフィルタリング。
- 結果をExcelファイル（`.xlsx`）として保存。

## 必要なもの

- Python 3.6以上
- 必要なPythonパッケージ：
  - `pandas`
  - `google-api-python-client`
  - `isodate`
  - `configparser`
  - `openpyxl` (Excel出力用)

## インストール方法

### 1. Pythonのインストール

まず、Python 3.6以上がインストールされていることを確認してください。以下のリンクからインストールできます。

- [Python 公式サイト](https://www.python.org/downloads/)

### 2. 必要なパッケージのインストール

次に、プロジェクトに必要なパッケージをインストールします。以下のコマンドを実行してください。

```bash
pip install pandas google-api-python-client isodate openpyxl
```

### 3. Google APIの設定

このスクリプトを使用するためには、YouTube Data API v3のAPIキーが必要です。以下の手順でAPIキーを取得してください。

1. [Google Cloud Console](https://console.developers.google.com/)にアクセスします。
2. 新しいプロジェクトを作成します。
3. 「YouTube Data API v3」を有効にします。
4. 「認証情報」セクションでAPIキーを生成します。

生成したAPIキーを`settings.ini`ファイルに設定してください。

### 4. `settings.ini`の設定

プロジェクトディレクトリに`settings.ini`ファイルを作成し、以下の設定を追加します。

```ini
[entity]
# 動画の公開期間の開始日 (例: 2024-01-01)
PUBLISHED_AFTER = 2024-01-01

# 動画の公開期間の終了日 (例: 2024-12-31)
PUBLISHED_BEFORE = 2024-12-31

# 収集する動画の種類 (ショート動画は最大3分、長編はそれ以上)
# "ショート" または "長編" を選択
VIDEO_TYPE = 長編

# YouTube APIキー (Google Cloud Platformから取得)
GCP_APIKEY = your-google-api-key-here

# YouTubeチャンネルID (対象のチャンネルIDを入力)
CHANNEL_ID = your-channel-id-here
```

- `PUBLISHED_AFTER`: 収集する動画の最小公開日
- `PUBLISHED_BEFORE`: 収集する動画の最大公開日
- `VIDEO_TYPE`: `ショート` または `長編` を指定
- `GCP_APIKEY`: 取得したYouTube APIのAPIキー
- `CHANNEL_ID`: 収集対象のYouTubeチャンネルID

## 使い方

1. `youtube_video_data_extractor.py` を実行して、指定されたチャンネルの動画データを収集します。
   
   ```bash
   python youtube_video_data_extractor.py
   ```

2. 実行後、指定された日付範囲内の動画情報が収集され、`youtube_videos_<timestamp>.xlsx`という名前のExcelファイルが生成されます。

## エラーハンドリング

- APIキーやチャンネルIDの設定が不足している場合や、YouTube APIからデータを取得できなかった場合は、エラーメッセージが表示され、詳細がログファイルに記録されます。
- すべてのエラーは`youtube_data_collector.log`に記録されますので、問題が発生した際はログを確認してください。

## ログ

ログファイルはプロジェクトディレクトリに保存されます。

- `youtube_data_collector.log`

ログには以下の情報が含まれます：
- 設定ファイルの読み込み
- YouTube APIの呼び出し
- 動画情報の収集状況
- エラー発生時の詳細な情報

## ライセンス

このプロジェクトは、MITライセンスの下で公開されています。
