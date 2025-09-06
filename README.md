# Civic Sentiment

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Civic Sentiment is a sentiment analysis project focused on public comments responding to official government and parliamentary statements, especially around demonstrations, civic demands, and major political issues.

## Features

- **YouTube Comment Scraping:** Scrape comments from a list of YouTube videos using the YouTube Data API.
- **Environment Detection:** Seamlessly switch between local and Google Colab environments.
- **Modular Design:** The scraping functionality is available as a command-line tool and can be imported into Jupyter notebooks.

## Getting Started

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rnov24/civic_sentiment.git
    cd civic_sentiment
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

3.  **Set up your environment variables:**
    - Create a `.env` file in the project root.
    - Add your YouTube Data API key to the `.env` file:
      ```
      YOUTUBE_API_KEY=your_api_key
      ```

### Google Colab Setup

1.  Open the `notebooks/01-data-collection.ipynb` notebook in Google Colab.
2.  Run the first cell to clone the repository and install the dependencies.

## Usage

### Command-Line Interface

You can use the `scraping.py` script to scrape comments from a list of YouTube videos and save them to a CSV file.

```bash
python -m civic_sentiment.scraping VIDEO_ID_1 VIDEO_ID_2
```

### Jupyter Notebook

The `notebooks/01-data-collection.ipynb` notebook provides an interactive environment for data collection. You can import the scraping functions and use them to collect data from YouTube.

```python
from civic_sentiment.scraping import get_video_comments, main
import os

# Get the API key from the environment variable
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Example: Get comments from a single video
video_id = "dQw4w9WgXcQ"
if API_KEY:
    comments = get_video_comments(API_KEY, video_id)
    print(f"Found {len(comments)} comments for video {video_id}")
else:
    print("YOUTUBE_API_KEY environment variable not set.")
```

## Configuration

This project uses a `.env` file to manage environment variables. You need to create a `.env` file in the project root and add the following variables:

- `YOUTUBE_API_KEY`: Your YouTube Data API key.