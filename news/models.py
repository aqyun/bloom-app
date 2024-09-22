from django.db import models


# class NewsArticle(models.Model):
#     title = models.CharField(max_length=255)
#     link = models.URLField()
#     content = models.TextField()
#     pub_date = models.DateTimeField()
#     cluster = models.IntegerField()



class NewsArticle(models.Model):
    judul = models.CharField(max_length=255)
    tautan = models.URLField(max_length=255)
    isi_berita = models.TextField()
    tanggal = models.DateField()
    preprocessed = models.TextField()
    cluster_2024_06_14 = models.CharField(max_length=255)
    keywords_2024_06_14 = models.CharField(max_length=255)
    cluster_2024_06_15 = models.CharField(max_length=255)
    keywords_2024_06_15 = models.CharField(max_length=255)
    cluster_2024_06_16 = models.CharField(max_length=255)
    keywords_2024_06_16 = models.CharField(max_length=255)
    cluster_2024_06_17 = models.CharField(max_length=255)
    keywords_2024_06_17 = models.CharField(max_length=255)
    cluster_2024_06_18 = models.CharField(max_length=255)
    keywords_2024_06_18 = models.CharField(max_length=255)
    
    def __str__(self):
        return self.judul