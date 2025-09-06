"""
This script scrapes comments from a list of YouTube videos, combines them into a
single DataFrame, and saves them to a CSV file in the data/raw directory.

The script uses the YouTube Data API to retrieve comments. It requires an API
key, which is loaded from a .env file. The video IDs are imported from the
config.py file.

The script uses the tqdm library to display progress bars for videos and pages
of comments.
"""

import os

from typing import List

import pandas as pd
import typer
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

from civic_sentiment.config import RAW_DATA_DIR, logger

# Get the API key from the environment variable
API_KEY = os.getenv("YOUTUBE_API_KEY")

app = typer.Typer()


def get_video_comments(api_key, video_id):
    """
    Retrieves all comments from a YouTube video.

    Args:
        api_key: Your YouTube Data API key.
        video_id: The ID of the YouTube video.

    Returns:
        A list of comments.
    """
    comments = []
    try:
        # Create a YouTube API client
        youtube = build("youtube", "v3", developerKey=api_key)

        # Get video comments
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,  # Max results per page
            textFormat="plainText",
        )

        with tqdm(
            desc=f"Pages for {video_id}", unit="page", leave=False
        ) as pbar:
            while request:
                response = request.execute()

                for item in response["items"]:
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append(
                        {
                            "author": comment["authorDisplayName"],
                            "published_at": comment["publishedAt"],
                            "text": comment["textOriginal"],
                        }
                    )

                request = youtube.commentThreads().list_next(
                    request, response
                )
                pbar.update(1)

    except HttpError as e:
        logger.error(f"An HTTP error {e.resp.status} occurred: {e.content}")

    return comments


@app.command()
def main(video_ids: List[str] = typer.Argument(..., help="List of video IDs to scrape")):
    """
    Main function to scrape comments, combine them, and save a single CSV to
    data/raw.
    """
    all_comments_frames = []
    video_id_to_title = {}

    for video_id in video_ids:
        if video_id.startswith("YOUR_"):
            continue

        # Fetch and cache the title for final reporting only
        try:
            youtube = build("youtube", "v3", developerKey=API_KEY)
            resp = (
                youtube.videos()
                .list(part="snippet", id=video_id, maxResults=1)
                .execute()
            )
            items = resp.get("items", [])
            title = (
                items[0]["snippet"].get("title", video_id)
                if items
                else video_id
            )
            video_id_to_title[video_id] = title
        except HttpError:
            video_id_to_title[video_id] = video_id

        comments = get_video_comments(API_KEY, video_id)
        df = pd.DataFrame(comments)
        if not df.empty:
            df["video_id"] = video_id
            all_comments_frames.append(df)

    if not all_comments_frames:
        logger.info("No comments found.")
        return

    combined_df = pd.concat(all_comments_frames, ignore_index=True)
    total_comments = len(combined_df)

    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / "comments.csv"
    combined_df.to_csv(file_path, index=False)

    # Decorated final report
    group_counts = (
        combined_df.groupby(["video_id"], as_index=False)["text"].count()
    )
    header = "=" * 60
    logger.info(header)
    logger.info("Final Report: YouTube Comments Scraping")
    logger.info(header)
    logger.info(f"Saved to: {file_path}")
    logger.info(f"Total comments: {total_comments}")
    logger.info("-" * 60)
    for _, row in group_counts.iterrows():
        title = video_id_to_title.get(row["video_id"], row["video_id"])
        logger.info(f"{title} ({row['video_id']}): {row['text']} comments")
    logger.info(header)


if __name__ == "__main__":
    app()