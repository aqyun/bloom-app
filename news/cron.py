# myapp/cron.py
from .clustering_model import cluster_news, extract_rss_feed_details


def my_scheduled_job():
    # Tulis logika tugas Anda di sini
    extract_rss_feed_details()
    cluster_news()
    print("News update job ran successfully.")
