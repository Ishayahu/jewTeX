# -*- coding: utf-8 -*-
# from unittest import TestCase
from django.test import TestCase
from texts.storage import *
from texts.storage import _Chapter, _Subchapter
import os


class TestContent(TestCase):
    def setUp(self):
        self.storage = Storage(os.path.join(os.getcwd(), 'TEST_TEXTS_DB'))


    def test_next_link_inside_siman (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('92')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.next_subchapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/92/seif=2/')

    def test_next_link_to_next_siman (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('92')
        link.set_params('seif=6')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.next_subchapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/106/seif=1/')

    def test_prev_link_inside_siman (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('92')
        link.set_params('seif=2')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.prev_subchapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/92/seif=1/')

    def test_prev_link_to_next_siman (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('106')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.prev_subchapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/92/seif=6/')

    # def test_next_chapter_link_taz (self):
    #     self.link = Link()
    #     author_name = AuthorName('taz')
    #     book = Book(Book('taz_al_shulchan_aruch_yoreh_deah'),author_name)
    #     self.link.set_author_name(author_name)
    #     self.link.set_book(book)
    #     self.link.set_params(params)

    def test_next_chapter_link_sha2 (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('92')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.next_chapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/106/seif=1/')

    def test_next_chapter_link_sha2_for_last_chapter (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2',author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('106')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertIsNone(book_TOC.next_chapter_link())

    def test_prev_chapter_link (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2', author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('106')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertEqual(book_TOC.prev_chapter_link(), '/open/joseph_karo/shulchan_aruch_yoreh_deah/92/seif=1/')

    def test_prev_chapter_link_for_first_chapter (self):
        link = Link()
        author_name = AuthorName('maran')
        book = Book('sha2', author_name)
        link.set_author_name(author_name)
        link.set_book(book)
        link.set_chapter_name('92')
        link.set_params('seif=1')
        book_TOC: Content = self.storage.get_book_TOC(book)
        book_TOC.set_current_place(link)
        self.assertIsNone(book_TOC.prev_chapter_link())
