# -*- coding: utf-8 -*-
import cyrtranslit
from django.urls import reverse
# from texts.storage import XMLStorage as Storage
from typing import Optional
class AuthorName:

    # author_kitzur = {'taz': 'david_halevi_segal',
    #                  'shah': 'shabbatai_hakohen',
    #                  'tur': 'jacob_ben_asher',
    #                  'hamechaber': 'joseph_karo',
    #                  'maran': 'joseph_karo',
    #                  'smak': 'isaac_ben_joseph_of_corbeil',
    #                  'terumat_hadeshen': 'israel_isserlein_ben_petachia',
    #                  'rif': 'isaac_ben_jacob_alfasi_ha_cohen',
    #                  'talmud': 'talmud',
    #                  'rosh': 'asher_ben_jehiel',
    #                  }

    # author2kitzur = {v: k for k, v in author_kitzur.items()}

    def __init__(self, storage_id, s, language_code='ru'):
        self.__language_code = language_code
        self.storage_id = storage_id
        self.info = s.get_author_info(self)
        self.full_name = self.__get_full_name()
        self.short_name = self.__get_short_name()

    def get_localized_info(self):
        return self.info[self.__language_code]

    def __get_full_name(self):
        i = self.get_localized_info()
        return f"{i['title']['value']} {i['last_name']['value']} {i['first_name']['value']} ({i['short_name']['value']})"



    def __get_short_name(self):
        i = self.get_localized_info()
        if i['short_name']['value']:
            return f"{i['title']['value']} {i['short_name']['value']}"
        else:
            return self.__get_full_name()

    # что комментировал

    def __eq__(self, other):
        if isinstance(other, AuthorName):
            return self.storage_id == other.storage_id
        else:
            return False

    def __repr__(self):
        return str(self.storage_id)

    def __str__(self):
        if self.full_name.strip()!='()':
            return f"{self.full_name}"
        else:
            return f"{self.storage_id}"


class Book:

    """
    У нас отдельно хранится инфа о книге, которая отображается и отедльно - её id в стораже, который используется в реквестах
    """

    # book_kitzur = {'sha1': 'shulchan_aruch_orach_chayim',
    #                'sha2': 'shulchan_aruch_yoreh_deah',
    #                'sha3': 'shulchan_aruch_even_haezer',
    #                'sha4': 'shulchan_aruch_choshen_mishpat',
    #                'smak': 'sefer_mitzvot_katan',
    #                'rif_bejca': 'sefer_ha_halachot_al_bejca',
    #               }
    # book2kitzur = {v: k for k, v in book_kitzur.items()}

    def __init__(self, storage_id: str, author: AuthorName, s, language_code = 'ru'):
        self.__language_code = language_code
        self.author = author
        self.storage_id = storage_id
        self.info = s.get_book_info(self)
        self.full_name = self.__get_full_name()
        self.short_name = self.__get_short_name()

    def get_localized_info(self):
        return self.info[self.__language_code]

    def __get_full_name(self):
        i = self.get_localized_info()
        if i['short_name']['value']:
            return f"{i['full_name']['value']} ({i['short_name']['value']})"
        else:
            return f"{i['full_name']['value']}"

    def __get_short_name(self):
        i = self.get_localized_info()
        if i['short_name']['value']:
            return f"{i['short_name']['value']}"
        else:
            return self.__get_full_name()

    def __eq__(self, other):
        if isinstance(other, Book):
            return self.storage_id == other.storage_id and self.author == other.author
        else:
            return False

    def __repr__(self):
        return str(self.storage_id)

    def __str__(self):
        if self.full_name.strip():
            return f"{self.full_name}"
        else:
            return f"{self.storage_id}"


def get_author(author_name):
    author_color = {
        AuthorName('таз').full_name: 'yellow',
        AuthorName('шах').full_name: 'green',
               }
    a = Author()
    a.author_name = AuthorName(author_name)
    a.css_class_name = author_color.get(a.author_name.full_name,'grey')
    return a

# def get_author_old(author_name):
#     authors = {
#         AuthorName('maran').full_name: __Maran,
#         AuthorName('таз').full_name: __Taz,
#         AuthorName('шах').full_name: __Shah,
#         AuthorName('смак').full_name: __Smak,
#         AuthorName('риф').full_name: __Isaac_ben_jacob_alfasi_ha_cohen,
#         AuthorName('isur_vheyter_harokh').full_name: __Isur_vheyter_harokh,
#         AuthorName('terumat_hadeshen').full_name: __Terumat_hadeshen,
#         AuthorName('rosh').full_name: __Rosh,
#         AuthorName('talmud').full_name: __Talmud,
#                }
#     return authors[AuthorName(author_name).full_name]()


class Author:
    author_name = None  # type: AuthorName
    css_class_name = None  # type: str
    # author_name: AuthorName = None
    # css_class_name: str = None


# class __Taz(Author):
#     author_name = AuthorName('таз')
#     css_class_name = 'yellow'
#
#
# class __Shah(Author):
#     author_name = AuthorName('шах')
#     css_class_name = 'green'
#
#
# class __Smak(Author):
#     author_name = AuthorName('смак')
#     css_class_name = 'grey'
#
#
# class __Maran(Author):
#     author_name = AuthorName('maran')
#     css_class_name = 'grey'
#
#
# class __Isur_vheyter_harokh(Author):
#     author_name = AuthorName('isur_vheyter_harokh')
#     css_class_name = 'grey'
#
#
# class __Terumat_hadeshen(Author):
#     author_name = AuthorName('terumat_hadeshen')
#     css_class_name = 'grey'
#
#
# class __Isaac_ben_jacob_alfasi_ha_cohen(Author):
#     author_name = AuthorName('rif')
#     css_class_name = 'grey'
#
#
# class __Rosh(Author):
#     author_name = AuthorName('rosh')
#     css_class_name = 'grey'
#
#
# class __Talmud(Author):
#     author_name = AuthorName('talmud')
#     css_class_name = 'grey'
