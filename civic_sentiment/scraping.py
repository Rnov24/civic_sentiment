"""
This script scrapes comments from a list of YouTube videos, combines them into a
single DataFrame, and saves them to a CSV file in the data/raw directory.

The script uses the YouTube Data API to retrieve comments. It requires an API
key and video IDs to be provided as parameters.

The script uses the tqdm library to display progress bars for videos and pages
of comments, showing video titles for better user experience.
"""

import os
from typing import List

import pandas as pd
import typer
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

from civic_sentiment.config import RAW_DATA_DIR, logger

app = typer.Typer()


def get_video_title(api_key: str, video_id: str) -> str:
    """
    Retrieves the title of a YouTube video.

    Args:
        api_key: Your YouTube Data API key.
        video_id: The ID of the YouTube video.

    Returns:
        The video title or video_id if title cannot be retrieved.
    """
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        
        if response["items"]:
            return response["items"][0]["snippet"]["title"]
        else:
            return video_id
    except HttpError as e:
        logger.warning(f"Could not fetch title for {video_id}: {e}")
        return video_id


def scrape_videos(api_key: str, video_ids: List[str]) -> pd.DataFrame:
    """
    Scrapes comments from a list of YouTube videos and returns a pandas DataFrame.

    Args:
        api_key: Your YouTube Data API key.
        video_ids: A list of YouTube video IDs.

    Returns:
        A pandas DataFrame containing the scraped comments.
    """
    all_comments_frames = []
    
    # Create YouTube API client once
    youtube = build("youtube", "v3", developerKey=api_key)

    for video_id in video_ids:
        if video_id.startswith("YOUR_"):
            continue

        # Get video title for better progress display
        video_title = get_video_title(api_key, video_id)
        logger.info(f"Scraping comments from: {video_title}")
        
        comments = []
        try:
            # Get video comments
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,  # Max results per page
                textFormat="plainText",
            )

            with tqdm(
                desc=f"Comments from: {video_title[:50]}{'...' if len(video_title) > 50 else ''}", 
                unit="page", 
                leave=False
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
                                "video_id": video_id,
                                "video_title": video_title,
                            }
                        )

                    request = youtube.commentThreads().list_next(
                        request, response
                    )
                    pbar.update(1)

        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred for {video_title}: {e.content}")
            continue

        if comments:
            df = pd.DataFrame(comments)
            all_comments_frames.append(df)
            logger.info(f"Collected {len(comments)} comments from {video_title}")

    if not all_comments_frames:
        logger.info("No comments found.")
        return pd.DataFrame()

    combined_df = pd.concat(all_comments_frames, ignore_index=True)
    return combined_df


@app.command()
def main(
    video_ids: List[str] = typer.Argument(..., help="List of video IDs to scrape"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="YouTube Data API key (or set YOUTUBE_API_KEY env var)")
):
    """
    Main function to scrape comments, combine them, and save a single CSV to
    data/raw.
    
    Examples:
        python -m civic_sentiment.scraping dQw4w9WgXcQ abc123def456 --api-key YOUR_API_KEY
        python -m civic_sentiment.scraping dQw4w9WgXcQ abc123def456  # Uses YOUTUBE_API_KEY env var
    """
    # Get API key from parameter or environment variable
    if api_key is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if api_key is None:
            typer.echo("Error: YouTube API key is required. Provide it via --api-key option or set YOUTUBE_API_KEY environment variable.")
            raise typer.Exit(1)
    
    logger.info(f"Starting to scrape comments from {len(video_ids)} video(s)")
    combined_df = scrape_videos(api_key, video_ids)

    if combined_df.empty:
        logger.warning("No comments were collected from any videos.")
        return

    total_comments = len(combined_df)

    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / "comments.csv"
    combined_df.to_csv(file_path, index=False)

    # Enhanced final report with video titles
    group_counts = (
        combined_df.groupby(["video_id", "video_title"], as_index=False)["text"].count()
    )
    header = "=" * 80
    logger.info(header)
    logger.info("Final Report: YouTube Comments Scraping")
    logger.info(header)
    logger.info(f"Saved to: {file_path}")
    logger.info(f"Total comments: {total_comments}")
    logger.info("-" * 80)
    for _, row in group_counts.iterrows():
        title_preview = row['video_title'][:60] + "..." if len(row['video_title']) > 60 else row['video_title']
        logger.info(f"{row['video_id']}: {row['text']} comments")
        logger.info(f"  Title: {title_preview}")
    logger.info(header)


if __name__ == "__main__":
    app()