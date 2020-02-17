# -*- coding: utf-8 -*-
from unittest import TestCase
from texts.storage import *
from texts.storage import _Chapter, _Subchapter
import os


class TestStorage(TestCase):
    def setUp(self):
        self.storage = Storage(os.path.join(os.getcwd(), 'TEST_TEXTS_DB'))

    def test_get_authors(self):
        a = self.storage.get_authors()
        result = [AuthorName('david_halevi_segal'),
                  AuthorName('isaac_ben_joseph_of_corbeil'),
                  AuthorName('isur_vheyter_harokh'),
                  AuthorName('jacob_ben_asher'),
                  AuthorName('joseph_karo'),
                  AuthorName('shabbatai_hakohen'),
                  AuthorName('TERM_DEFINITIONS'),
                  ]
        self.assertListEqual(a, result)

    # def test_get_books_for_author_short_name(self):
    #     a = self.storage.get_books_for_author(AuthorName('taz'))
    #     result = [Book('taz_al_yoreh_deah', AuthorName('taz')),
    #               ]
    #     self.assertListEqual(a, result)
    #
    # def test_get_books_for_author_full_name(self):
    #     a = self.storage.get_books_for_author(AuthorName('joseph_karo'))
    #     result = [Book('shulchan_aruch_choshen_mishpat', AuthorName('joseph_karo')),
    #               Book('shulchan_aruch_yoreh_deah', AuthorName('joseph_karo')),
    #               ]
    #     self.assertListEqual(a, result)
    #
    # def test_book_short_names(self):
    #     b1 = Book('shulchan_aruch_yoreh_deah', AuthorName('joseph_karo'))
    #     self.assertEqual(b1.short_name, 'sha2')
    #
    # def test_book_full_and_short_names(self):
    #     b1 = Book('shulchan_aruch_yoreh_deah', AuthorName('joseph_karo'))
    #     b2 = Book('sha2', AuthorName('maran'))
    #     self.assertEqual(b1, b2)
    #
    # def test_get_book_content_for_taz(self):
    #     a = self.storage.get_book_TOC(Book('taz_al_yoreh_deah', AuthorName('taz')))
    #     result = Content()
    #     c = _Chapter('92')
    #     s1 = _Subchapter('1','siman_katan')
    #     s2 = _Subchapter('17','siman_katan')
    #     c.add_subchapter(s1)
    #     c.add_subchapter(s2)
    #     result.add_chapter(c)
    #     self.assertEqual(a, result)
    #
    # def test_get_book_content_for_sha_yoreh_deah(self):
    #     a = self.storage.get_book_TOC(Book('sha2', AuthorName('maran')))
    #     a.chapters.sort()
    #     result = Content()
    #     c = _Chapter('92')
    #     c.add_subchapter(_Subchapter('1','seif'))
    #     c.add_subchapter(_Subchapter('2','seif'))
    #     c.add_subchapter(_Subchapter('3','seif'))
    #     c.add_subchapter(_Subchapter('4','seif'))
    #     c.add_subchapter(_Subchapter('5','seif'))
    #     c.add_subchapter(_Subchapter('6','seif'))
    #     result.add_chapter(c)
    #     c = _Chapter('106')
    #     c.add_subchapter(_Subchapter('1','seif'))
    #     result.add_chapter(c)
    #     result.chapters.sort()
    #     self.assertEqual(a, result)

