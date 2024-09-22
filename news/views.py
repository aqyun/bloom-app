import codecs
import csv
import re

import pandas as pd
from django.shortcuts import render
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


def extract_dates(columns):
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    dates = set()
    for col in columns:
        match = date_pattern.search(col)
        if match:
            dates.add(match.group(0))
    return sorted(dates)

def cluster_view(request):
    df = pd.read_csv('news/static/news/database/clustered_documents_harian_test_rep.csv')
    dataframe = pd.DataFrame(df)

    dates = extract_dates(dataframe.columns)
    all_clustered_data_by_date = {}

    for date in dates:
        cluster_col = f'Cluster_{date}'
        keywords_col = f'Keywords_{date}'

        if cluster_col in dataframe.columns and keywords_col in dataframe.columns:
            cleaned = dataframe[dataframe[cluster_col].notna()]
            num_clusters = int(cleaned[cluster_col].max())

            clustered_data = [{"kluster": i+1, "berita": [], "count": 0} for i in range(num_clusters)]

            for index in cleaned.index:
                cluster_index = int(cleaned.loc[index, cluster_col]) - 1
                clustered_data[cluster_index]['berita'].append({
                    "judulBerita": cleaned.loc[index, 'Judul'],
                    "linkBerita": cleaned.loc[index, 'Tautan'],
                    "pubDateBerita": cleaned.loc[index, 'Tanggal Publikasi'],
                    "content": cleaned.loc[index, 'Isi Berita'],
                    "keywords": str(cleaned.loc[index, keywords_col]).replace(' ', ', '),
                    "image": cleaned.loc[index, 'Gambar']
                })

                clustered_data[cluster_index]['count'] += 1

            all_clustered_data_by_date[date] = clustered_data

    nonClusteredData = []
    for index in dataframe.index:
        nonClusteredData.append({
            "judulBerita": dataframe.loc[index, 'Judul'],
            "linkBerita": dataframe.loc[index, 'Tautan'],
            "pubDateBerita": dataframe.loc[index, 'Tanggal Publikasi'],
            "content": dataframe.loc[index, 'Isi Berita'],
            "keywords": str(dataframe.loc[index, 'Keywords_2024-06-23']).replace(' ', ', '),
            "image": dataframe.loc[index, 'Gambar']
        })

    dfAll = pd.read_csv('news/static/news/database/clustered_documents_all.csv')
    dataframeAll = pd.DataFrame(dfAll)
    allnum_clusters = int(dataframeAll['Cluster'].max())

    allClusteredData = [{"kluster": i+1, "berita": [], "count": 0} for i in range(allnum_clusters)]

    for index in dataframeAll.index:
        cluster_index = int(dataframeAll.loc[index, 'Cluster']) - 1
        allClusteredData[cluster_index]['berita'].append({
            "judulBerita": dataframeAll.loc[index, 'Judul'],
            "linkBerita": dataframeAll.loc[index, 'Tautan'],
            "pubDateBerita": dataframeAll.loc[index, 'Tanggal Publikasi'],
            "content": dataframeAll.loc[index, 'Isi Berita'],
            "keywords": str(dataframeAll.loc[index, 'Keywords']).replace(' ', ', '),
            "image": dataframeAll.loc[index, 'Gambar']
        })

        allClusteredData[cluster_index]['count'] += 1

    return render(request, 'news/clusters.html', {
        "clustered_data_by_date": all_clustered_data_by_date,
        "nonClustered": nonClusteredData,
        "allCluster": allClusteredData
    })

def cluster_view_all(request, cluster_id):
    df = pd.read_csv('news/static/news/database/clustered_documents_all.csv')
    dataframe = pd.DataFrame(df)
    
    filtered_data = dataframe[dataframe['Cluster'] == cluster_id]
    
    cluster_articles = []
    
    for index in filtered_data.index:
        cluster_articles.append({
            "judulBerita": filtered_data.loc[index, 'Judul'],
            "linkBerita": filtered_data.loc[index, 'Tautan'],
            "pubDateBerita": filtered_data.loc[index, 'Tanggal Publikasi'],
            "content": filtered_data.loc[index, 'Isi Berita'],
            "keywords": str(filtered_data.loc[index, 'Keywords']).replace(' ', ', '),
            "image": filtered_data.loc[index, 'Gambar']
        })
    
    return render(request, 'news/filtered_cluster.html', {
        "cluster_id": cluster_id,
        "articles": cluster_articles
    })

def filtered_cluster_view(request, date, cluster_id):
    df = pd.read_csv('news/static/news/database/clustered_documents_harian_test_rep.csv')
    dataframe = pd.DataFrame(df)
    
    cluster_col = f'Cluster_{date}'
    keywords_col = f'Keywords_{date}'

    if cluster_col not in dataframe.columns or keywords_col not in dataframe.columns:
        return render(request, 'news/error.html', {"message": f"Column {cluster_col} or {keywords_col} not found in dataset."})

    filtered_data = dataframe[(dataframe[cluster_col] == int(cluster_id)) & (dataframe[cluster_col].notna())]
    
    cluster_articles = []
    
    for index in filtered_data.index:
        cluster_articles.append({
            "judulBerita": filtered_data.loc[index, 'Judul'],
            "linkBerita": filtered_data.loc[index, 'Tautan'],
            "pubDateBerita": filtered_data.loc[index, 'Tanggal Publikasi'],
            "content": filtered_data.loc[index, 'Isi Berita'],
            "keywords": str(filtered_data.loc[index, keywords_col]).replace(' ', ', '),
            "image": filtered_data.loc[index, 'Gambar']
        })
    
    return render(request, 'news/filtered_cluster.html', {
        "cluster_id": cluster_id,
        "date": date,
        "articles": cluster_articles
    })

factory = StemmerFactory()
stemmer = factory.create_stemmer()
stopwords_indonesia = stopwords.words('indonesian')

def search_results(request):
    query = request.GET.get('query')
    words = query.split()
    words = [word for word in words if word.lower() not in stopwords_indonesia]

    stemmed_words = [stemmer.stem(word) for word in words]

    df = pd.read_csv('news/static/news/database/clustered_documents_harian_test_rep.csv')
    dataframe = pd.DataFrame(df)
    
    dates = extract_dates(dataframe.columns)
    all_clustered_data_by_date = {}

    for date in dates:
        cluster_col = f'Cluster_{date}'
        keywords_col = f'Keywords_{date}'

        if cluster_col in dataframe.columns and keywords_col in dataframe.columns:
            cleaned = dataframe[dataframe[cluster_col].notna()]
            num_clusters = int(cleaned[cluster_col].max())

            clustered_data = [{"kluster": i+1, "berita": [], "count": 0} for i in range(num_clusters)]

            for index, row in cleaned.iterrows():
                found = False
                for keyword in stemmed_words:
                    if keyword in str(row[keywords_col]).lower():
                        cluster_index = int(row[cluster_col]) - 1
                        clustered_data[cluster_index]['berita'].append({
                            "judulBerita": row['Judul'],
                            "linkBerita": row['Tautan'],
                            "pubDateBerita": row['Tanggal Publikasi'],
                            "content": row['Isi Berita'],
                            "keywords": str(row[keywords_col]).replace(' ', ', '),
                            "image": row['Gambar']
                        })
                        found = True
                        break
                if found:
                    clustered_data[cluster_index]['count'] += 1

            updated_clustered = [element for element in clustered_data if element['count'] != 0]

            all_clustered_data_by_date[date] = updated_clustered

    return render(request, 'news/search_results.html', {
        'keyword': query,
        'clustered_data_by_date': all_clustered_data_by_date
    })