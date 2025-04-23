import os
import pandas as pd
from googleapiclient.discovery import build
import isodate
from datetime import datetime, timezone
from configparser import ConfigParser
import os.path as osp
import logging

def setup_logging(log_file):
    """ログの設定を行う関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_settings(file_path):
    """設定ファイルを読み込む関数"""
    settings = ConfigParser()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            settings.read_file(f)
        logging.info("設定ファイルの読み込みに成功しました。")
    except FileNotFoundError:
        logging.error("settings.iniファイルが見つかりません。")
        exit(1)
    return settings

def get_api_client(api_key):
    """YouTube APIクライアントの構築"""
    try:
        client = build('youtube', 'v3', developerKey=api_key)
        logging.info("YouTube APIクライアントの構築に成功しました。")
        return client
    except Exception as e:
        logging.error(f"YouTube APIクライアントの構築に失敗しました: {e}")
        exit(1)

def get_uploads_playlist_id(youtube, channel_id):
    """チャンネルのアップロード再生リストIDを取得"""
    try:
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        logging.info("チャンネル情報の取得に成功しました。")
        return channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        logging.error(f"チャンネル情報の取得に失敗しました: {e}")
        exit(1)

def get_videos_in_date_range(youtube, playlist_id, published_after_str, published_before_str, video_type):
    """指定された日付範囲内の動画情報を取得する関数"""
    videos = []
    next_page_token = None

    logging.info("データの集計を開始します...")

    while True:
        try:
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            logging.info("動画リストの取得に成功しました。")
        except Exception as e:
            logging.error(f"動画リストの取得に失敗しました: {e}")
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
                            logging.info(f"動画情報を収集しました: {title}")
                except Exception as e:
                    logging.error(f"動画の詳細情報の取得に失敗しました: {e}")

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

    return videos

def save_to_excel(data, output_file):
    """データをExcelファイルに保存する関数"""
    try:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        logging.info(f"Excelファイルが保存されました: {output_file}")
    except Exception as e:
        logging.error(f"Excelファイルの保存に失敗しました: {e}")

def main():
    # settings.iniファイルのパスを取得
    FILE = osp.join(osp.dirname(__file__), "settings.ini")
    
    # ログファイルの設定
    LOG_FILE = osp.join(osp.dirname(__file__), "youtube_data_collector.log")
    setup_logging(LOG_FILE)

    # 設定を読み込む
    settings = load_settings(FILE)

    # 現在の日付を取得
    current_date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # settings.iniから日付を取得し、空の場合はデフォルトの日付を設定
    published_after_str = settings['entity'].get('PUBLISHED_AFTER', '').strip() or current_date_str
    published_before_str = settings['entity'].get('PUBLISHED_BEFORE', '').strip() or current_date_str
    video_type = settings['entity'].get('VIDEO_TYPE', '').strip()

    # 環境変数からAPIキーとチャンネルIDを取得
    API_KEY = settings["entity"].get("GCP_APIKEY")
    CHANNEL_ID = settings["entity"].get("CHANNEL_ID")

    if not API_KEY or not CHANNEL_ID:
        logging.error("APIキーまたはチャンネルIDが取得できませんでした。'.ini'ファイルを確認してください。")
        exit(1)

    # YouTube APIクライアントの構築
    youtube = get_api_client(API_KEY)

    # チャンネルの情報を取得してアップロード再生リストIDを取得
    uploads_playlist_id = get_uploads_playlist_id(youtube, CHANNEL_ID)

    # 動画を取得
    data = get_videos_in_date_range(youtube, uploads_playlist_id, published_after_str, published_before_str, video_type)

    # settings.iniから出力ディレクトリを取得し、デフォルトディレクトリを設定
    default_output_dir = osp.join(osp.dirname(__file__), 'output')
    output_dir = settings['entity'].get('OUTPUT_DIR', default_output_dir)

    # 出力ディレクトリが存在しない場合は作成
    if not osp.exists(output_dir):
        os.makedirs(output_dir)

    # 現在の日時を取得してファイル名に組み込む
    current_time = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = osp.join(output_dir, f'youtube_videos_{current_time}.xlsx')

    # Excelファイルとして出力
    save_to_excel(data, output_file)

if __name__ == "__main__":
    main()
