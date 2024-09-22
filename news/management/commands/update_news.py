import os

import joblib
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from django.core.management.base import BaseCommand

from news.clustering_model import cluster_news, extract_rss_feed_details
from news.models import NewsArticle


class Command(BaseCommand):
    help = 'Fetch news data, perform clustering, and save the trained model'

    def handle(self, *args, **kwargs):
        rss_feeds = [
            'https://news.detik.com/berita/rss',
            'https://www.antaranews.com/rss/terkini.xml',
            'https://www.cnbcindonesia.com/news/rss',
            'https://rss.tempo.co/nasional',
            'https://www.republika.co.id/rss',
            'https://sindikasi.okezone.com/index.php/rss/0/RSS2.0'
        ]

        all_titles = []
        all_links = []
        all_pub_dates = []
        all_preprocessed_texts = []
        all_keywords = []

        for rss_feed in rss_feeds:
            preprocessed_texts, keywords, titles, links, pub_dates = extract_rss_feed_details(rss_feed)
            all_titles.extend(titles)
            all_links.extend(links)
            all_pub_dates.extend(pub_dates)
            all_preprocessed_texts.extend(preprocessed_texts)
            all_keywords.extend(keywords)

        clusters = cluster_news(all_preprocessed_texts, all_keywords)

        # Save the trained model
        model_path = os.path.join('news', 'trained_model.joblib')
        joblib.dump(clusters, model_path)

        NewsArticle.objects.all().delete()
        for i, (title, link, pub_date, preprocessed_text) in enumerate(zip(all_titles, all_links, all_pub_dates, all_preprocessed_texts)):
            pub_date = parser.parse(pub_date).strftime('%Y-%m-%d %H:%M:%S')
            NewsArticle.objects.create(
                title=title,
                link=link,
                content=preprocessed_text,
                pub_date=pub_date,
                cluster=i
            )

        self.stdout.write(self.style.SUCCESS('Successfully updated news data and trained model'))
