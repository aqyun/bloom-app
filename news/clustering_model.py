import re
from collections import defaultdict

import numpy as np
import requests
from bs4 import BeautifulSoup
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score as sklearn_silhouette_score

prepositions = ["yang", "am", "tetapi", "oleh", "bisa", "mampu", "antara", "tidak", "setiap", "untuk", "tentang", "dan", "sayang", "dari", "punya", "di", "ada", "lakukan", "telah", "memiliki", "setelah", "seperti", "memang", "dia", "jika", "semua", "jadi", "baik", "bagaimana", "ke", "hampir", "karena", "lain", "itu", "dalam", "juga", "sudah", "pernah", "sama", "saling", "ini", "karena", "tapi", "selalu", "cnbc", "serta", "pun", "kata", "saat", "maupun", "dengan", "walau", "akan", "bagai", "jadi", "atau", "sehingga", "pada", "republika"]

def preprocess_text(text):
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    tokens = [token for token in tokens if token not in prepositions and len(token) > 2]
    stemmer = StemmerFactory().create_stemmer()
    tokens = [stemmer.stem(token) for token in tokens]
    term_frequency = {}
    for token in tokens:
        term_frequency[token] = term_frequency.get(token, 0) + 1
    max_frequency = max(term_frequency.values(), default=0)
    threshold = max_frequency / 2
    keywords = {word: freq for word, freq in term_frequency.items() if freq >= threshold and freq >= 2}
    if (len(keywords) < 3) and term_frequency:
        sorted_keywords = sorted(term_frequency.items(), key=lambda item: item[1], reverse=True)
        keywords = {word: freq for word, freq in sorted_keywords[:3]}
    return keywords, tokens

def extract_rss_feed_details(rss_url):
    response = requests.get(rss_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')
        preprocessed_texts = []
        all_title = []
        all_pubdate = []
        all_link = []
        all_keywords = []
        all_images = []
        for item in items:
            title = item.find('title').text
            print("Judul:", title)
            link = item.find('link').text
            print("Tautan:", link)
            image_url = None
            
            enclosure = item.find('enclosure')
            if enclosure and enclosure.get('type') and enclosure.get('type').startswith('image/'):
                image_url = enclosure.get('url')
            else:
                media_content = item.find('media:content')
                if media_content and media_content.get('url'):
                    image_url = media_content.get('url')
                elif 'rss.tempo.co' in rss_url:
                    img_tag = item.find('img')
                    if img_tag and img_tag.text:
                        image_url = img_tag.text.strip()
            
            news_response = requests.get(link)
            if news_response.status_code == 200:
                news_soup = BeautifulSoup(news_response.text, 'html.parser')
                if 'antaranews.com' in rss_url:
                    content = news_soup.find('div', class_='post-content')
                elif 'republika.co.id' in rss_url:
                    content = news_soup.find('div', class_='article-content')
                elif 'rss.tempo.co' in rss_url:
                    content = news_soup.find('div', class_='detail-konten')
                else:
                    content = None
                if content:
                    content_text = content.text.strip()
                    
                    if not image_url:
                        if 'rss.tempo.co' in rss_url:
                            img_tag = content.find('img', itemprop='image')
                        elif 'republika.co.id' in rss_url:
                            img_tag = content.find('img', class_='img-fluid')
                        else:
                            img_tag = content.find('img')
                        if img_tag and img_tag.get('src'):
                            image_url = img_tag.get('src')
                    
                    print("Isi Berita sebelum pra-pemrosesan:", content_text)
                    keyword_frequency, processed_tokens = preprocess_text(content_text)
                    print("\nIsi Berita setelah pra-pemrosesan:", " ".join(processed_tokens))
                    print("\nKata Kunci:")
                    for keyword, frequency in keyword_frequency.items():
                        print(f"{keyword}: {frequency}")
                    preprocessed_texts.append(" ".join(processed_tokens))
                    all_keywords.append(keyword_frequency)
                    all_title.append(title)
                    all_link.append(link)
                    all_pubdate.append(item.find('pubDate').text)
                    all_images.append(image_url)
                else:
                    print("Konten berita tidak ditemukan.")
            else:
                print("Gagal mengambil halaman berita:", news_response.status_code)
            print("-" * 50)
        return preprocessed_texts, all_keywords, all_title, all_link, all_pubdate, all_images
    else:
        print("Gagal mengambil RSS feed:", response.status_code)
        return [], [], [], [], [], []

def cluster_news(preprocessed_texts, all_keywords, all_title, all_link, all_pubdate):
    filtered_keywords = [keywords for keywords in all_keywords if isinstance(keywords, dict) and keywords]
    max_df = min(0.8, len(preprocessed_texts) / len(filtered_keywords))
    vectorizer = TfidfVectorizer(max_df=max_df, min_df=2, max_features=1000, stop_words='english')
    X = vectorizer.fit_transform([" ".join(keywords.keys()) for keywords in filtered_keywords])
    
    silhouette_scores = []
    max_clusters = len(preprocessed_texts) // 2
    
    for n_clusters in range(2, max_clusters + 1):
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        cluster_labels = clusterer.fit_predict(X.toarray())
        
        # Check if any cluster has only one member
        cluster_sizes = np.bincount(cluster_labels)
        if np.any(cluster_sizes < 2):
            continue  # Skip this number of clusters if any cluster is too small
        
        silhouette_avg = sklearn_silhouette_score(X, cluster_labels)
        silhouette_scores.append((silhouette_avg, n_clusters))
    
    # Choose the number of clusters with the highest silhouette score
    if silhouette_scores:
        optimal_silhouette_score, optimal_num_clusters = max(silhouette_scores)
    else:
        optimal_silhouette_score, optimal_num_clusters = 0, 2
    
    clusterer = AgglomerativeClustering(n_clusters=optimal_num_clusters)
    cluster_labels = clusterer.fit_predict(X.toarray())
    
    cluster_data = defaultdict(list)
    for label, text, keywords, title, pub_date, link in zip(cluster_labels, preprocessed_texts, all_keywords, all_title, all_pubdate, all_link):
        cluster_data[label].append((title, link, pub_date, text, keywords))
    
    # Merge small clusters into larger clusters
    merged_cluster_data = []
    for cluster, data in cluster_data.items():
        if len(data) < 2:
            # Find the closest larger cluster to merge with
            closest_cluster = max(cluster_data.items(), key=lambda x: len(x[1]) if len(x[1]) >= 2 else 0)[0]
            cluster_data[closest_cluster].extend(data)
        else:
            merged_cluster_data.append(data)
    
    print("Hasil Klasterisasi Berita:")
    for i, cluster in enumerate(merged_cluster_data, start=1):
        print(f"\nKlaster {i}:")
        for title, link, pub_date, text, keywords in cluster:
            print("Judul:", title)
            print("Tautan:", link)
            print("Tanggal Publikasi:", pub_date)
            print("Teks Berita:")
            print(text)
            print("\nKata kunci:")
            print(keywords)
            print("-" * 50)
    
    print("\nSilhouette Score:", optimal_silhouette_score)
    
    print("DATA INGIN")
    print(merged_cluster_data)
    print("DATA TAK INGIN")
    
    return merged_cluster_data

all_preprocessed_texts = []
all_keywords = []
all_titles = []
all_links = []
all_pubdates = []
all_images = [] 

rss_urls = [
    "https://www.antaranews.com/rss/terkini.xml",
    "https://www.republika.co.id/rss",
    "https://rss.tempo.co/nasional",
]

for rss_url in rss_urls:
    preprocessed_texts, keywords, titles, links, pubdates, images = extract_rss_feed_details(rss_url)
    all_preprocessed_texts.extend(preprocessed_texts)
    all_keywords.extend(keywords)
    all_titles.extend(titles)
    all_links.extend(links)
    all_pubdates.extend(pubdates)
    all_images.extend(images)

if all_preprocessed_texts and all_keywords:
    silhouette_avg_score = cluster_news(all_preprocessed_texts, all_keywords, all_titles, all_links, all_pubdates)
    print("\nSilhouette Score:", silhouette_avg_score)
else:
    print("Tidak ada teks yang berhasil diproses dari RSS feed.")
