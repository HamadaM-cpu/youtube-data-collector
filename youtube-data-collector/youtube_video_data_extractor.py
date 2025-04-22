import os
import pandas as pd
from googleapiclient.discovery import build
import isodate
from datetime import datetime, timezone
from configparser import ConfigParser
import os.path as osp
import logging

# ログ設定
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='youtube_data_collector.log',  # ログをファイルに保存
                    filemode='w')  # ファイルモード（'w'で上書き）

# 設定ファイルの読み込み
FILE = osp.join(osp.dirname(__file__), "settings.ini")
settings = ConfigParser()

try:
    with open(FILE, 'r', encoding='utf-8') as f:
        settings.read_file(f)
    logging.info("設定ファイルが正常に読み込まれました。")
except FileNotFoundError as e:
    logging.error(f"設定ファイルが見つかりません: {e}")
    print("Error: settings.iniファイルが見つかりません。")
    exit(1)
except Exception as e:
    logging.critical(f"設定ファイルの読み込み中に予期しないエラーが発生しました: {e}")
    print(f"予期しないエラーが発生しました: {e}")
    exit(1)

# 現在の日付を取得
current_date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# settings.iniファイルから設定を取得
published_after_str = settings['entity'].get('PUBLISHED_AFTER', '').strip() or current_date_str
published_before_str = settings['entity'].get('PUBLISHED_BEFORE', '').strip() or current_date_str
video_type = settings['entity'].get('VIDEO_TYPE', '').strip()

# APIキーとチャンネルIDを設定ファイルから取得
API_KEY = settings["entity"].get("GCP_APIKEY")
CHANNEL_ID = settings["entity"].get("CHANNEL_ID")

if not API_KEY or not CHANNEL_ID:
    logging.error("APIキーまたはチャンネルIDが設定ファイルに含まれていません。")
    print("Error: APIキーまたはチャンネルIDが設定ファイルに含まれていません。")
    exit(1)

# YouTube APIクライアントの初期化
try:
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    logging.info("YouTube APIクライアントを初期化しました。")
except Exception as e:
    logging.critical(f"YouTube APIの初期化に失敗しました: {e}")
    print(f"Error: YouTube APIの初期化に失敗しました。詳細はログファイルを確認してください。")
    exit(1)

# チャンネル情報の取得
try:
    channel_response = youtube.channels().list(
        part='contentDetails',
        id=CHANNEL_ID
    ).execute()
    uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    logging.info(f"チャンネル情報を正常に取得しました。Uploads Playlist ID: {uploads_playlist_id}")
except Exception as e:
    logging.error(f"チャンネル情報の取得に失敗しました: {e}")
    print(f"Error: チャンネル情報の取得に失敗しました。詳細はログファイルを確認してください。")
    exit(1)

# 動画情報を取得する関数
def get_videos_in_date_range(playlist_id, published_after_str, published_before_str):
    videos = []
    next_page_token = None
    logging.info("動画情報の取得を開始します...")

    while True:
        try:
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            logging.info(f"次のページの動画情報を取得しました。")
        except Exception as e:
            logging.error(f"動画リストの取得中にエラーが発生しました: {e}")
            break

        for item in playlist_response.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']
            published_at_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

            if published_after_str <= published_at_date.strftime('%Y-%m-%d') <= published_before_str:
                try:
                    video_response = youtube.videos().list(
                        part='contentDetails,statistics',
                        id=video_id
                    ).execute()
                    video_details = video_response['items'][0]
                    duration = video_details['contentDetails'].get('duration')

                    if duration:
                        duration_seconds = isodate.parse_duration(duration).total_seconds()

                        if (video_type == 'ショート' and duration_seconds <= 180) or \
                            (video_type == '長編' and 180 < duration_seconds <= 3600):
                            view_count = video_details['statistics'].get('viewCount', '0')
                            like_count = video_details['statistics'].get('likeCount', '0')
                            comment_count = video_details['statistics'].get('commentCount', '0')

                            videos.append({
                                'タイトル': title,
                                'URL': f'https://www.youtube.com/watch?v={video_id}',
                                '投稿日時': published_at,
                                '再生回数': int(view_count),
                                'イイネ数': int(like_count),
                                'コメント数': int(comment_count),
                            })
                except Exception as e:
                    logging.error(f"動画詳細情報の取得中にエラーが発生しました: {e}")

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

    return videos

# 動画データを取得
data = get_videos_in_date_range(uploads_playlist_id, published_after_str, published_before_str)

# DataFrameに変換してExcelファイルとして保存
df = pd.DataFrame(data)
current_time = datetime.now().strftime('%Y%m%d_%H%M')
output_file = f'C:\\Users\\username\\Documents\\youtube_videos_{current_time}.xlsx'

try:
    df.to_excel(output_file, index=False)
    logging.info(f"Excelファイルが正常に保存されました: {output_file}")
    print(f"Excelファイルが保存されました: {output_file}")
except Exception as e:
    logging.error(f"Excelファイルの保存中にエラーが発生しました: {e}")
    print(f"Error: Excelファイルの保存に失敗しました。詳細はログファイルを確認してください。")
