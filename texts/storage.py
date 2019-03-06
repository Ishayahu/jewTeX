# -*- coding: utf-8 -*-
from typing import List, Optional, Callable, ClassVar
from texts.biblio import AuthorName, Book
import texts.biblio
import cyrtranslit
from django.urls import reverse


import os
import re

_all_fields = ['author', 'book', 'siman', 'chapter', 'klal', 'sub_chapter', 'seif',
               'din', 'page', 'dibur_amathil', 'siman_katan']


class _FilseStorage:
    # все поля используются
    book_level = ['author', 'book', ]
    # используется только одно поле!
    chapter_level = ['siman']
    subchapter_level = list(set(_all_fields) - set(book_level) - set(chapter_level))


class Link:
    """
    Класс, который хранит информацию на ссылку в структурированной форме
    """

    def __init__(self):

        self.author_name: AuthorName = None
        self.book: Book = None
        self.chapter_name: str = None
        self.errors: list = []
        self.params: str = None
        # self.siman = None
        # self.klal = None
        # self.seif = None
        # self.din = None
        # self.page = None
        # self.dibur_amathil = None
        # self.siman_katan = None
        # self.referrerer = None

        self.accepted_param_names = ['siman', 'klal', 'seif', 'din', 'page', 'dibur_amathil', 'siman_katan', 'referrerer']
        self.fs_level_param_names = ['siman', 'klal', 'page', ]
        self.intext_param_names = list(set(self.accepted_param_names) - set(self.fs_level_param_names))

    def set_author_name(self, author_name: AuthorName):
        self.author_name = author_name

    def set_book(self, book: Book):
        self.book = book

    def set_chapter_name(self, chapter_name: str):
        self.chapter_name = chapter_name

    def set_params(self, params: str):
        self.params = params
        for k, v in re.findall('([^=]*)=([^&]*)&?', params):
            if k in self.intext_param_names:
                self.__setattr__(k, v)
            if k in self.fs_level_param_names:
                self.chapter_name = v

    def get_path_to_file(self) -> str:
        """
        Возвращаем путь к файлу, где хранится текст
        :return:
        """
        return os.path.join(*list(map(str, (self.author_name.full_name, self.book.full_name, self.chapter_name))))

    def get_subchapter(self) -> ClassVar:
        class SubC:
            name = None
            type = None

        result = SubC()
        if any([_ in self.__dict__ for _ in self.intext_param_names]):
            for param in self.intext_param_names:
                if param in self.__dict__:
                    result.type = param
                    result.name = self.__getattribute__(param)
        return result

    def get_regexp(self) -> str:
        """
        Возвращает регулярку, чтобы искать нужный отрывок в тексте
        :return:
        """
        # если есть что-то, что ищем в файле
        if any([_ in self.__dict__ for _ in self.intext_param_names]):
            r = '.*'
            r_end = ''
            # TODO надо подумать над ним, но пока оставлю так, потому что ещё не ясно, какие варианты могут быть
            for param in self.intext_param_names:
                if param in self.__dict__:
                    r += r"\[\[{name}={value}]].*?".format(name = param, value = self.__getattribute__(param))
                    r_end += r"(?:\[\[{name}=.*|\[\[$)".format(name = param)
            # Добавляем содержимое
            r += "(.*?)"

            # до следующего такого же
            r += r_end
            return r
        # если ничего такого нет и надо вернуть текст всего файла
        else:
            return r"(.+)"

    def validate(self):
        if not self.author_name:
            self.errors.append("Не указан автор")
        if not self.book:
            self.errors.append("Не указана книга")
        if not self.chapter_name:
            self.errors.append("Не указана глава ")
        if self.errors:
            return False
        return True

    def short_str(self):
        return "{}:{}".format(self.chapter_name, self.get_subchapter().name)

class _Subchapter:
    def __init__(self, subchapter_name: str, subchapter_type: str):
        self.name: str = subchapter_name
        self.type: str = subchapter_type
        self.chapter: _Chapter = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}:{}".format(self.type, self.name)

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

    def get_link_params(self):
        return "{my_type}={my_name}".format(chapter = self.chapter, my_type = self.type, my_name = self.name)


class _Chapter:
    def __init__(self, name: str, idx: int = None):
        self.subchapters: List[_Subchapter] = []
        self.name: str = name
        if not idx:
            self.idx = int(name)
        else:
            self.idx = idx

    def add_subchapter(self, item: _Subchapter):
        item.chapter = self
        self.subchapters.append(item)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}:{}".format(self.name, str(self.subchapters))

    def __eq__(self, other):
        if self.name == other.name:
            for idx, subchapter in enumerate(self.subchapters):
                if subchapter != other.subchapters[idx]:
                    return False
            return True
        return False

    def __lt__(self, other):
        return self.idx < other.idx


class Content:

    def __init__(self):
        self.chapters = []
        self.current_place: Link = None

    def add_chapter(self, chapter_name):
        self.chapters.append(chapter_name)
        self.chapters.sort()

    def set_current_place(self, link: Link):
        self.current_place = link

    def next_chapter_link(self) -> Optional[str]:
        """
        Ссылка на следующую главу, если есть
        """
        current_chapter = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter)
        if current_chapter_idx + 1 < len(self.chapters): # если это не последняя глава
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx + 1].name,
                "{}={}".format(self.chapters[current_chapter_idx + 1].subchapters[0].type,
                               self.chapters[current_chapter_idx + 1].subchapters[0].name)
            ])

    def prev_chapter_link(self) -> Optional[str]:
        """
        Ссылка на предыдущую главу, если есть
        """
        current_chapter = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter)
        if current_chapter_idx > 0: # если это не первая
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx - 1].name,
                "{}={}".format(self.chapters[current_chapter_idx - 1].subchapters[0].type,
                               self.chapters[current_chapter_idx - 1].subchapters[0].name)
            ])

    def next_subchapter_link(self) -> Optional[str]:
        """
        Ссылка на следующий раздел главы, если есть, или на следующую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)

        # можем ли перейти к следующей подглаве:
        if current_subchapter_idx + 1 < len(current_chapter.subchapters): # если это не последний раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].type,
                               self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].name)
            ])
        else:
            # можем ли перйти к след. главе
            return self.next_chapter_link()

    def prev_subchapter_link(self) -> Optional[str]:
        """
        Ссылка на предыдущий раздел главы, если есть, или на предыдущую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)

        # можем ли перейти к предыдущему разделу главы:
        if current_subchapter_idx > 0:  # если это не первый раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].type,
                               self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].name)
            ])
        else:
            # можем ли перйти к след. главе
            # но тут нельзя просто выбрать "пред. главу, так как тогда мы перескачим на её начало - тут обработаем ручками
            if current_chapter_idx > 0:  # если это не первая
                return reverse('open', args = [
                    self.current_place.author_name.full_name,
                    self.current_place.book.full_name,
                    self.chapters[current_chapter_idx - 1].name,
                    "{}={}".format(self.chapters[current_chapter_idx - 1].subchapters[-1].type,
                                   self.chapters[current_chapter_idx - 1].subchapters[-1].name)
                ])

    def __eq__(self, other):
        for idx, chapter in enumerate(self.chapters):
                if chapter != other.chapters[idx]:
                    return False
        return True


class Storage:
    """
    Класс, обслуживающий хранилище текстов. К нему обращаются по человечески, а он уже ищет текст там, где он лежит и возвращает его
    """

    def __init__(self, texts_path = None):
        self.fields2chapters = None
        # если храниение в виде файлов
        self.texts_path = texts_path

        if self.texts_path:
            self.fields2chapters = _FilseStorage()

    def __getattr__(self, item: str) -> Callable:
        if self.texts_path:
            return {
                'get_authors': self.__file_get_authors,
                'get_books_for_author': self.__file_get_books_for_author,
                'get_book_TOC': self.__file_get_book_TOC,
                'get_text_by_link': self.__file_get_text_by_link,
                'get_term': self.__file_get_term,
            }[item]

    def __file_get_authors(self) -> List[AuthorName]:
        """
        Возвращает список авторов, чьи книги доступны
        """
        return [AuthorName(full_name) for full_name in os.listdir(self.texts_path) if not full_name.startswith('.')]

    def __file_get_books_for_author(self, author: AuthorName) -> List[Book]:
        """
        Возвращает список книг для автора
        """
        return [Book(name, author) for name in os.listdir(os.path.join(self.texts_path, author.full_name)) if not name.startswith('.')]

    # noinspection PyPep8Naming
    def __file_get_book_TOC(self, book: Book) -> Content:
        """
        Возвращает содержание книги
        """
        regexp = r"\[\[({})=(\d+)]]".format('|'.join(self.fields2chapters.subchapter_level))
        content = Content()
        for chapter_name in [_ for _ in os.listdir(os.path.join(self.texts_path,
                                                                book.author.full_name,
                                                                book.full_name)) if not _.startswith('.')]:
            chapter = _Chapter(chapter_name[:-4])  # отбрасываем .txt
            with open(os.path.join(self.texts_path,
                                   book.author.full_name,
                                   book.full_name, chapter_name), 'r', encoding='utf8') as f:
                c = f.read()
                for subchapter_type, subchapter_name in re.findall(regexp, c):
                    subchapter = _Subchapter(subchapter_name, subchapter_type)
                    chapter.add_subchapter(subchapter)
            content.add_chapter(chapter)
        return content

    def __file_get_text_by_link(self, link: Link) -> str:
        """
        Возвращает текст по ссылке
        """
        path = link.get_path_to_file()
        fullpath = os.path.join(self.texts_path, path)
        try:
            with open("{}.txt".format(fullpath), 'r', encoding = 'utf8') as f:
                fulltext = f.read()
        except FileNotFoundError:
            return "??ЕЩЁ НЕ ПЕРЕВЕДЕНО??"
        pattern = link.get_regexp()
        print(pattern)
        result = re.findall(pattern, fulltext, re.DOTALL)
        if result:
            return result[0]
        else:
            # вроде как при успешном поиске не должно такого быть
            return "TEXT NOT FOUND"

    def __file_get_term(self, term):
        term = cyrtranslit.to_latin(term, 'ru')
        fullpath = os.path.join(self.texts_path, 'TERM_DEFINITIONS', term)
        try:
            with open("{}.txt".format(fullpath), 'r', encoding = 'utf8') as f:
                fulltext = f.read()
            # fulltext = fulltext.replace('\n','<p>')
            return fulltext
        except FileNotFoundError:
            return "DEFINITION NOT FOUND"

    def get_quote_by_ref(self, link: Link) -> str:
        """
        Возвращает цитату по ссылке и refferer'y
        :param link:
        :return:
        """
        pass

    def get_term(self, term: str) -> str:
        """
        Возвращает подсказку для определения
        """
        pass

