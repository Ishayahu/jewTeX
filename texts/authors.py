# -*- coding: utf-8 -*-
from django.urls import reverse
import cyrtranslit

author_kitzur = {'taz': 'david_halevi_segal',
                 'shah': 'shabbatai_hakohen',
                 'tur': 'jacob_ben_asher',
                 'hamechaber': 'joseph_karo',
                 'maran': 'joseph_karo',
                 'smak': 'isaac_ben_joseph_of_corbeil',
                 }

author2kitzur = {v: k for k, v in author_kitzur.items()}


def normalize_author(author):
    author = author.lower()
    author = cyrtranslit.to_latin(author,'ru')
    return author_kitzur.get(author, author)


def get_short_author_name(author):
    author = author.lower()
    author = cyrtranslit.to_latin(author,'ru')
    return author2kitzur.get(author, author)


def normalize_book(book):
    book = book.lower()
    book = cyrtranslit.to_latin(book,'ru')
    book_kitzur = {'sha1': 'shulchan_aruch_orach_chayim',
                   'sha2': 'shulchan_aruch_yoreh_deah',
                   'sha3': 'shulchan_aruch_even_haezer',
                   'sha4': 'shulchan_aruch_choshen_mishpat',
                   'smak': 'sefer_mitzvot_katan',
                 }
    return book_kitzur.get(book, book)


def SHACommentatorsFactory(author, book_template, russian_link_template, card_color):
    """
    Для ТАЗ: author='david_halevi_segal', book_template='taz_al_{}', russian_link_template='ТАЗ-{}'
    :param author:
    :param book_template:
    :param russian_link:
    :return:
    """
    class Commentator:
        def __init__ (self):
            """

            :param link_to_parent: Link
            :param siman_katan: str
            """
            self.helek = None
            self.siman = None
            self.siman_katan = None
            self.card_color = card_color
            self.name = author
            self.short_name = get_short_author_name(author)

        def set_link_to_parent(self, link_to_parent):
            self.helek = "_".join(link_to_parent.book.split("_")[-2:])
            self.siman = link_to_parent.siman
        def __str__(self):
            return "{}: {}/{}/{}/{}".format(self.name, self.helek, self.siman, self.siman_katan, self.card_color)
        def __repr__(self):
            return str(self)
        def get_link (self):
            return {'url': reverse('text_api_request', args = [author,
                                                               book_template.format(self.helek),
                                                               'siman={}&siman_katan={}'.format(self.siman, self.siman_katan)]),
                    'name': russian_link_template.format(self.siman_katan)}

    return Commentator

def AuthorsFactory(author, card_color):
    class Author:
        def __init__ (self):
            """

            :param link_to_parent: Link
            :param siman_katan: str
            """
            self.name = author
            self.short_name = get_short_author_name(author)
            self.books = []
            self.card_color = card_color

        # нужно только для коротких ссылок
        # def set_link_to_parent(self, link_to_parent):
        #     self.helek = "_".join(link_to_parent.book.split("_")[-2:])
        #     self.siman = link_to_parent.siman

        def __str__(self):
            return "{}({})".format(self.name, self.card_color)
        def __repr__(self):
            return str(self)
        def get_link (self):
            return {'url': reverse('author', kwargs = {'author': self.name})}

    return Author



# пока доступные варианты классов карточек red, blue, green, yellow, purple, gray
Taz = SHACommentatorsFactory('david_halevi_segal', 'taz_al_{}', 'ТАЗ-{}', 'red')
Shah = SHACommentatorsFactory('shabbatai_hakohen', 'shah_al_{}', 'ШАХ-{}', 'blue')

Smak = AuthorsFactory('isaac_ben_joseph_of_corbeil', 'yellow')
DEFAULT_AUTHOR = AuthorsFactory('noname', 'gray')

# class Taz:
#     def __init__(self, link_to_parent, siman_katan):
#         """
#
#         :param link_to_parent: Link
#         :param siman_katan: str
#         """
#         self.helek = "_".join(link_to_parent.book.split("_")[-2:])
#         self.siman = link_to_parent.siman
#         self.siman_katan = siman_katan
#     def get_link(self):
#         return {'url': reverse('text_api_request', args=['david_halevi_segal',
#                                                  'taz_al_{}'.format(self.helek),
#                                                  'siman={}&siman_katan={}'.format(self.siman, self.siman_katan)]),
#                 'name': 'ТАЗ-{}'.format(self.siman_katan)}
