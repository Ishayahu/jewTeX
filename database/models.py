from django.db import models
import requests
from bs4 import BeautifulSoup

PREFIX = 'https://jewtex.ru/open'

class Tag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Summary(models.Model):
    events = models.ManyToManyField('Event')
    tags = models.ManyToManyField('Tag', blank=True)
    link = models.TextField()

    def name(self):
        a = requests.get(f'{PREFIX}{self.link}')
        self.b = BeautifulSoup(a.text, 'html.parser')
        return self.b.title.text

    def __str__(self):
        return self.link

    def summary(self):
        if not self.b:
            self.name()
        return self.b.body.body.text

