# -*- coding: utf-8 -*-
import cyrtranslit
from django.urls import reverse


class AuthorName:

    author_kitzur = {'taz': 'david_halevi_segal',
                     'shah': 'shabbatai_hakohen',
                     'tur': 'jacob_ben_asher',
                     'hamechaber': 'joseph_karo',
                     'maran': 'joseph_karo',
                     'smak': 'isaac_ben_joseph_of_corbeil',
                     }

    author2kitzur = {v: k for k, v in author_kitzur.items()}

    def __init__(self, name):
        self.full_name = self.__get_full_name(name)
        self.short_name = self.__get_short_name(name)

    @staticmethod
    def __get_full_name(name):
        name = name.lower()
        name = cyrtranslit.to_latin(name, 'ru')
        return AuthorName.author_kitzur.get(name, name)

    @staticmethod
    def __get_short_name(name):
        name = name.lower()
        name = cyrtranslit.to_latin(name, 'ru')
        return AuthorName.author2kitzur.get(name, name)

    # что комментировал

    def __eq__(self, other):
        if isinstance(other, AuthorName):
            return self.full_name == other.full_name
        else:
            return False

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<AuthorName:{} ({})>".format(self.full_name, self.short_name)


class Book:

    book_kitzur = {'sha1': 'shulchan_aruch_orach_chayim',
                   'sha2': 'shulchan_aruch_yoreh_deah',
                   'sha3': 'shulchan_aruch_even_haezer',
                   'sha4': 'shulchan_aruch_choshen_mishpat',
                   'smak': 'sefer_mitzvot_katan',
                  }
    book2kitzur = {v: k for k, v in book_kitzur.items()}

    def __init__(self, name: str, author: AuthorName):
        self.full_name = Book.__get_full_name(name)
        self.short_name = Book.__get_short_name(name)
        self.author = author

    @staticmethod
    def __get_full_name(name):
        name = name.lower()
        name = cyrtranslit.to_latin(name, 'ru')
        return Book.book_kitzur.get(name, name)

    @staticmethod
    def __get_short_name(name):
        name = name.lower()
        name = cyrtranslit.to_latin(name, 'ru')
        return Book.book2kitzur.get(name, name)

    def __eq__(self, other):
        if isinstance(other, Book):
            return self.full_name == other.full_name and self.author == other.author
        else:
            return False

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<Book:{}@{}>".format(self.full_name, self.author)


def get_author(author_name):
    authors = {
        AuthorName('maran').full_name: __Maran,
        AuthorName('таз').full_name: __Taz,
        AuthorName('шах').full_name: __Shah,
        AuthorName('смак').full_name: __Smak,
        AuthorName('isur_vheyter_harokh').full_name: __Isur_vheyter_harokh,
               }
    return authors[AuthorName(author_name).full_name]()


class Author:
    author_name = None  # type: AuthorName
    css_class_name = None  # type: str
    # author_name: AuthorName = None
    # css_class_name: str = None


class __Taz(Author):
    author_name = AuthorName('таз')
    css_class_name = 'yellow'


class __Shah(Author):
    author_name = AuthorName('шах')
    css_class_name = 'green'


class __Smak(Author):
    author_name = AuthorName('смак')
    css_class_name = 'grey'


class __Maran(Author):
    author_name = AuthorName('maran')
    css_class_name = 'grey'


class __Isur_vheyter_harokh(Author):
    author_name = AuthorName('isur_vheyter_harokh')
    css_class_name = 'grey'
