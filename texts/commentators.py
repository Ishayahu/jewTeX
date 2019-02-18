# -*- coding: utf-8 -*-
from django.urls import reverse


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

Taz = SHACommentatorsFactory('david_halevi_segal', 'taz_al_{}', 'ТАЗ-{}', '#f2dbcc')
Shah = SHACommentatorsFactory('shabbatai_hakohen', 'shah_al_{}', 'ШАХ-{}', '#f0f8ff')
DEFAULT_AUTHOR = SHACommentatorsFactory('noname', 'noname_{}', 'noname-{}', '#f7786b')

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
