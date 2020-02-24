# -*- coding: utf-8 -*-
# from typing import List, Optional, Callable, ClassVar
from texts.biblio import AuthorName, Book
import texts.biblio
import cyrtranslit
from django.urls import reverse
from typing import *

import os
import re
import xml.etree.ElementTree as ET
from lxml import etree
from texts.biblio import AuthorName, Book

delimiters = '%'
# part = абзац, мысль
_all_fields = ['author', 'book', 'siman', 'chapter', 'klal', 'sub_chapter', 'seif',
               'din', 'page', 'dibur_amathil', 'siman_katan', 'question', 'mishna', 'perek', 'amud', 'mizva', 'part']
_all_fields_ru = ['author', 'book', 'siman', 'chapter', 'klal', 'sub_chapter', 'сеиф',
               'закон', 'стр', 'дибур аматхиль', 'симан катан', 'вопрос', 'мишна', 'perek', 'лист', 'заповедь', 'часть']


class _FileStorage:
    # все поля используются
    book_level = ['author', 'book', ]
    # используется только одно поле!
    chapter_level = ['siman', 'klal', 'page', 'perek','mizva']
    chapter_level_ru = ['симан', 'клаль', 'стр.', 'глава','заповедь']
    # то, что может быть как главой, так и разделом внутри главы. Например, книга иногда может делиться на страницы (как талмуд),
    # а иногда на заповеди (как у Рамбама), и тогда делится делится на страницы внутри заповеди
    can_be_intext = ['mizva', 'page']
    subchapter_level = list(set(_all_fields) - set(book_level) - set(chapter_level)) + can_be_intext


class Linkv1:
    """
    Класс, который хранит информацию на ссылку в структурированной форме
    """

    def __init__(self):

        self.author_name = None  # type: AuthorName
        self.book = None  # type: Book
        self.chapter_name = None  # type: str
        self.errors = []  # type: list
        self.params = None  # type: str

        self.fs_level_param_names = _FileStorage.chapter_level
        self.intext_param_names = _FileStorage.subchapter_level
    def __repr__(self):
        return "{}|{}|{}|{}".format(self.author_name, self.book, self.chapter_name, self.params)
    def set_author_name(self, author_name: AuthorName):
        self.author_name = author_name

    def get_url(self):
        subchapter_params = []
        for param in self.params.split('&'):
            k,v = param.split('=')
            if k in self.fs_level_param_names:
                pass
            else:
                subchapter_params.append(param)
        subchapter_params = "&".join(subchapter_params)
        return reverse('open', args=(self.author_name.full_name, self.book.full_name, self.chapter_name, subchapter_params))

    def set_book(self, book: Book):
        self.book = book

    def set_chapter_name(self, chapter_name: str):
        self.chapter_name = chapter_name

    def set_params(self, params: str):
        self.params = params
        self.correct_params = []
        for k, v in re.findall('([^=]*)=([^&]*)&?', params):
            # print (k,v)
            used_as_chapter_name = False
            # сперва проверяем, что это не глава и лишь если нет - тогда отдаём в параметры

            # if k in self.intext_param_names:
            #     self.__setattr__(k, v)
            if k in self.fs_level_param_names:
                # если ещё не указана глава. Так как может быть, что глава уже указана, так как некоторые подглавы могут называться как главы:
                # мицва и страница например
                if not self.chapter_name:
                    # print('set chapter_name to {}'.format(v))
                    self.chapter_name = v
                    used_as_chapter_name = True
            if k in self.intext_param_names and not used_as_chapter_name:
                self.__setattr__(k, v)
                # print('set {} to {}'.format(k,v))
                self.correct_params.append("{}={}".format(k,v))
        self.correct_params = "&".join(self.correct_params)
    def get_params(self):
        return self.correct_params
    def get_path_to_file(self) -> str:
        """
        Возвращаем путь к файлу, где хранится текст
        :return:
        """
        return os.path.join(*list(map(str, (self.author_name.full_name, self.book.full_name, self.chapter_name))))

    # def get_subchapter(self) -> ClassVar:
    def get_subchapter(self):
        class SubC:
            name = None
            type = None
            def __str__(self):
                return "SubC: {}({})".format(self.name, self.type)
            def __repr__(self):
                return "SubC: {}({})".format(self.name, self.type)

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
                # print(param)
                if param in self.__dict__:
                    # print('in self.__dict__')
                    r += r"\[\[{name}={value}]].*?".format(name = param, value = self.__getattribute__(param))
                    r_end += r"(?:\[\[{name}=.*|\[\[$)".format(name = param)
            # Добавляем содержимое
            r += "(.*?)"

            # до следующего такого же
            r += r_end
            return r
        # если ничего такого нет и надо вернуть текст всего файла
        else:
            # убираем служебные [[ в конце с возможными пробелами/строками
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
class Link:
    """
    Класс, который хранит информацию на ссылку в структурированной форме
    """

    def __init__(self):

        self.author_name = None  # type: AuthorName
        self.book = None  # type: Book
        self.errors = []  # type: list
        self.params = []  # type: list
        self.page = ''  # type: str
        self.daf = ''  # type: str
        self.raw_params = ''  # type: str
    def __repr__(self):
        return "{}|{}|{}".format(self.author_name, self.book, self.params)
    def str_inside_book_position(self):
        params_dict = dict()
        r = ""
        for k,v in self.params:
            params_dict[k] = v
        for idx,chapter_type in enumerate(_FileStorage.chapter_level):
            if chapter_type in params_dict.keys():
                r+= f"{_FileStorage.chapter_level_ru[idx]} {params_dict[chapter_type]}"
                del params_dict[chapter_type]
        for k,v in params_dict.items():
            idx = _all_fields.index(k)
            r+= f", {_all_fields_ru[idx]} {v}"
        return r



    def set_author_name(self, author_name: AuthorName):
        self.author_name = author_name

    def get_url(self):
        return reverse('open_from_xml', args=(self.author_name.storage_id,
                                     self.book.storage_id,
                                     self.get_params()))

    def set_book(self, book: Book):
        self.book = book

    def set_params(self, params: str):
        self.raw_params = params
        for k, v in re.findall('([^=]*)=([^&]*)&?', params):
            if k == 'page':
                self.page = v
            elif k == 'daf':
                self.daf = v
            else:
                self.params.append((k,v))
    def set_param(self, key: str, value: str):
        if self.raw_params:
            self.raw_params += "&"
        self.raw_params += f"{key}={value}"
        if key == 'page':
            self.page = value
        elif key == 'daf':
            self.daf = value
        else:
            self.params.append((key,value))
    def get_params(self):
        r = ''
        for k,v in self.params:
            r += f"{k}={v}&"
        return r
    def get_path_to_file(self) -> str:
        """
        Возвращаем путь к файлу, где хранится текст
        :return:
        """
        return os.path.join(*list(map(str, (self.author_name.full_name, self.book.full_name, self.chapter_name))))

    # def get_subchapter(self) -> ClassVar:
    def get_subchapter(self):
        class SubC:
            name = None
            type = None
            def __str__(self):
                return "SubC: {}({})".format(self.name, self.type)
            def __repr__(self):
                return "SubC: {}({})".format(self.name, self.type)

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
                # print(param)
                if param in self.__dict__:
                    # print('in self.__dict__')
                    r += r"\[\[{name}={value}]].*?".format(name = param, value = self.__getattribute__(param))
                    r_end += r"(?:\[\[{name}=.*|\[\[$)".format(name = param)
            # Добавляем содержимое
            r += "(.*?)"

            # до следующего такого же
            r += r_end
            return r
        # если ничего такого нет и надо вернуть текст всего файла
        else:
            # убираем служебные [[ в конце с возможными пробелами/строками
            return r"(.+)"

    def validate(self):
        if not self.author_name:
            self.errors.append("Не указан автор")
        if not self.book:
            self.errors.append("Не указана книга")
        if self.errors:
            return False
        return True

    def short_str(self):
        # return "{}:{}".format(self.chapter_name, self.get_subchapter().name)
        return self.get_params()

class _Subchapter:
    def __init__(self, subchapter_name: str, subchapter_type: str):
        self.name = subchapter_name  # type: str
        self.type = subchapter_type  # type: str
        self.chapter = None  # type: _Chapter
        # self.name: str = subchapter_name
        # self.type: str = subchapter_type
        # self.chapter: _Chapter = None

    def __repr__(self):
        return "_Subchapter {}:{}".format(self.type, self.name)

    def __str__(self):
        return "_Subchapter {}:{}".format(self.type, self.name)

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

    def get_link_params(self):
        return "{my_type}={my_name}".format(chapter = self.chapter, my_type = self.type, my_name = self.name)

class ContentItem:
    def __init__(self):
        self.level = None
        self.type = None
        self.name = None
        self.parents = ''
        self.verbouse_name = ''
    def populate_from_xml_element(self, element):
        # print(element.attrib)
        if 'level' in element.attrib:
            self.level = int(element.attrib['level'])
        if element.tag in ('page','daf'):
            self.type = element.tag
            self.level = 0
        else:
            self.type = element.attrib['type']
        self.name = element.attrib['name']
        if 'verbouse_name' in element.attrib:
            self.verbouse_name = element.attrib['verbouse_name']
        if element.tag not in ('page','daf'):
            parent = element.getparent()
            # print(parent)
            while parent is not None:
                if 'type' in parent.attrib and 'name' in parent.attrib:
                    self.parents += f"{parent.attrib['type']}={parent.attrib['name']}&"
                parent = parent.getparent()
                # print(parent)
            if self.parents:
                self.parents = self.parents[:-1]
    def html_indentation(self):
        return "&nbsp"*self.level*4
    def get_link_params(self):
        if self.parents:
            return self.parents + f'&{self.type}={self.name}'
        return f'{self.type}={self.name}'
    def __eq__(self, other):
        if self.type == other.type and self.name == other.name and self.parents == other.parents:
            return True
        return False
    def as_url_params(self):
        if self.parents:
            return f"{self.parents}&{self.type}={self.name}"
        else:
            return f"{self.type}={self.name}"
    def __str__(self):
        result = ''
        if not self.parents:
            result =  f"{self.type} <!-- ToC level: {self.level}-->: {self.name}"
        else:
            result = f"{self.parents}|{self.type} ({self.level}): {self.name}"
        if self.verbouse_name:
            result += f" {self.verbouse_name}"
        return result

    def __repr__(self):
        return f"{self.parents}|{self.type} ({self.level}): {self.name}"

class _Chapter:
    def __init__(self, name, type, idx: int = None):
        self.subchapters = []  # type: List[_Subchapter]
        self.name = name  # type: str
        self.type = type  # type: str
        # self.subchapters: List[_Subchapter] = []
        # self.name: str = name
        if not idx:
            self.idx = int(name)
        else:
            self.idx = idx

    def get_link_params(self):
        return f'{self.type}={self.name}'

    def add_subchapter(self, item: _Subchapter):
        item.chapter = self
        self.subchapters.append(item)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.type == 'page':
            return f'стр. {self.name}'
        else:
            return self.name

    def __eq__(self, other):
        if self.name == other.name:
            for idx, subchapter in enumerate(self.subchapters):
                if subchapter != other.subchapters[idx]:
                    return False
            return True
        return False

    def __lt__(self, other):
        return self.idx < other.idx


class Contentv1:

    def __init__(self):
        self.chapters = []
        self.current_place = None  # type: Link
        # self.current_place: Link = None

    def __repr__(self):
        return "Content: {} /{}/".format(self.chapters, self.current_place)
    def add_chapter(self, chapter_name):
        self.chapters.append(chapter_name)
        self.chapters.sort()

    def set_current_place(self, link: Link):
        self.current_place = link

    # def next_chapter_link(self) -> Optional[str]:
    def next_chapter_link(self):
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

    # def prev_chapter_link(self) -> Optional[str]:
    def prev_chapter_link(self):
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

    # def next_subchapter_link(self) -> Optional[str]:
    def next_subchapter_link(self):
        """
        Ссылка на следующий раздел главы, если есть, или на следующую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        subchapters = [c for c in current_chapter.subchapters if c.type==current_subchapter.type]
        # current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)
        current_subchapter_idx = [c.name for c in subchapters].index(current_subchapter.name)
        # print(current_subchapter)
        # print(subchapters)
        # print(current_subchapter_idx)
        # можем ли перейти к следующей подглаве:
        # if current_subchapter_idx + 1 < len(current_chapter.subchapters): # если это не последний раздел
        if current_subchapter_idx + 1 < len(subchapters): # если это не последний раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                # "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].type,
                #                self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].name)
                "{}={}".format(current_subchapter.type,subchapters[current_subchapter_idx + 1].name)
            ])
        else:
            # можем ли перйти к след. главе
            return self.next_chapter_link()

    # def prev_subchapter_link(self) -> Optional[str]:
    def prev_subchapter_link(self):
        """
        Ссылка на предыдущий раздел главы, если есть, или на предыдущую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        subchapters = [c for c in current_chapter.subchapters if c.type == current_subchapter.type]
        # current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)
        current_subchapter_idx = [c.name for c in subchapters].index(current_subchapter.name)
        # можем ли перейти к предыдущему разделу главы:
        if current_subchapter_idx > 0:  # если это не первый раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                # "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].type,
                #                self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].name)
                "{}={}".format(current_subchapter.type, subchapters[current_subchapter_idx - 1].name)
            ])
        else:
            # можем ли перйти к предыдущей главе
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

class Content:

    def __init__(self):
        self.items = []  # type: List[ContentItem]
        self.current_place = None  # type: Link
        self.current_place_idx = None
        # self.current_place: Link = None

    def __repr__(self):
        return "Content: {} /{}/".format(self.current_place_idx, len(self.items))
    def add_item(self, item: ContentItem):
        if item not in self.items:
            self.items.append(item)


    def set_current_place(self, link: Link):
        self.current_place = link
        for idx,item in enumerate(self.items):
            if link.raw_params == item.as_url_params():
                self.current_place_idx = idx
                return True

    # def next_chapter_link(self) -> Optional[str]:
    # def next_chapter_link(self):
    #     """
    #     Ссылка на следующую главу, если есть
    #     """
    #     current_chapter = self.current_place.chapter_name
    #     current_chapter_idx = [c.name for c in self.chapters].index(current_chapter)
    #     if current_chapter_idx + 1 < len(self.chapters): # если это не последняя глава
    #         return reverse('open', args = [
    #             self.current_place.author_name.full_name,
    #             self.current_place.book.full_name,
    #             self.chapters[current_chapter_idx + 1].name,
    #             "{}={}".format(self.chapters[current_chapter_idx + 1].subchapters[0].type,
    #                            self.chapters[current_chapter_idx + 1].subchapters[0].name)
    #         ])

    # def prev_chapter_link(self) -> Optional[str]:
    # def prev_chapter_link(self):
    #     """
    #     Ссылка на предыдущую главу, если есть
    #     """
    #     current_chapter = self.current_place.chapter_name
    #     current_chapter_idx = [c.name for c in self.chapters].index(current_chapter)
    #     if current_chapter_idx > 0: # если это не первая
    #         return reverse('open', args = [
    #             self.current_place.author_name.full_name,
    #             self.current_place.book.full_name,
    #             self.chapters[current_chapter_idx - 1].name,
    #             "{}={}".format(self.chapters[current_chapter_idx - 1].subchapters[0].type,
    #                            self.chapters[current_chapter_idx - 1].subchapters[0].name)
    #         ])

    # def next_subchapter_link(self) -> Optional[str]:
    def next_subchapter_link(self):
        """
        Ссылка на следующий раздел главы, если есть, или на следующую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        subchapters = [c for c in current_chapter.subchapters if c.type==current_subchapter.type]
        # current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)
        current_subchapter_idx = [c.name for c in subchapters].index(current_subchapter.name)
        # print(current_subchapter)
        # print(subchapters)
        # print(current_subchapter_idx)
        # можем ли перейти к следующей подглаве:
        # if current_subchapter_idx + 1 < len(current_chapter.subchapters): # если это не последний раздел
        if current_subchapter_idx + 1 < len(subchapters): # если это не последний раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                # "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].type,
                #                self.chapters[current_chapter_idx].subchapters[current_subchapter_idx + 1].name)
                "{}={}".format(current_subchapter.type,subchapters[current_subchapter_idx + 1].name)
            ])
        else:
            # можем ли перйти к след. главе
            return self.next_chapter_link()

    # def prev_subchapter_link(self) -> Optional[str]:
    def prev_subchapter_link(self):
        """
        Ссылка на предыдущий раздел главы, если есть, или на предыдущую главу
        """
        current_chapter_name = self.current_place.chapter_name
        current_chapter_idx = [c.name for c in self.chapters].index(current_chapter_name)
        current_chapter = self.chapters[current_chapter_idx]

        current_subchapter = self.current_place.get_subchapter()
        subchapters = [c for c in current_chapter.subchapters if c.type == current_subchapter.type]
        # current_subchapter_idx = [c.name for c in current_chapter.subchapters].index(current_subchapter.name)
        current_subchapter_idx = [c.name for c in subchapters].index(current_subchapter.name)
        # можем ли перейти к предыдущему разделу главы:
        if current_subchapter_idx > 0:  # если это не первый раздел
            return reverse('open', args = [
                self.current_place.author_name.full_name,
                self.current_place.book.full_name,
                self.chapters[current_chapter_idx].name,
                # "{}={}".format(self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].type,
                #                self.chapters[current_chapter_idx].subchapters[current_subchapter_idx - 1].name)
                "{}={}".format(current_subchapter.type, subchapters[current_subchapter_idx - 1].name)
            ])
        else:
            # можем ли перйти к предыдущей главе
            # но тут нельзя просто выбрать "пред. главу, так как тогда мы перескачим на её начало - тут обработаем ручками
            if current_chapter_idx > 0:  # если это не первая
                return reverse('open', args = [
                    self.current_place.author_name.full_name,
                    self.current_place.book.full_name,
                    self.chapters[current_chapter_idx - 1].name,
                    "{}={}".format(self.chapters[current_chapter_idx - 1].subchapters[-1].type,
                                   self.chapters[current_chapter_idx - 1].subchapters[-1].name)
                ])

    def next_subchapter_params(self):
        if self.current_place_idx is not None:
            if self.current_place_idx < len(self.items):
                return self.items[self.current_place_idx+1].as_url_params()
        return ''

    def prev_subchapter_params(self):
        if self.current_place_idx is not None:
            if self.current_place_idx > 0:
                return self.items[self.current_place_idx-1].as_url_params()
        return ''

    def __eq__(self, other):
        for idx, chapter in enumerate(self.chapters):
                if chapter != other.chapters[idx]:
                    return False
        return True


# class Storage:
#     """
#     Класс, обслуживающий хранилище текстов. К нему обращаются по человечески, а он уже ищет текст там, где он лежит и возвращает его
#     """
#
#     def __init__(self, texts_path = None):
#         self.fields2chapters = None
#         # если храниение в виде файлов
#         self.texts_path = texts_path
#
#         if self.texts_path:
#             self.fields2chapters = _FilseStorage()
#
#     # def __getattr__(self, item: str) -> Callable:
#     def __getattr__(self, item: str):
#         if self.texts_path:
#             return {
#                 'get_authors': self.__file_get_authors,
#                 'get_author_info': self.__file_get_author_info,
#                 'get_book_info': self.__file_get_book_info,
#                 'get_books_for_author': self.__file_get_books_for_author,
#                 'get_book_TOC': self.__file_get_book_TOC,
#                 'get_text_by_link': self.__file_get_text_by_link,
#                 'get_term': self.__file_get_term,
#             }[item]
#
#     # def __file_get_authors(self) -> List[AuthorName]:
#     def __file_get_authors(self):
#         """
#         Возвращает список авторов, чьи книги доступны
#         """
#         return [AuthorName(full_name) for full_name in os.listdir(self.texts_path) if not full_name.startswith('.')]
#
#     # def __file_get_books_for_author(self, author: AuthorName) -> List[Book]:
#     def __file_get_books_for_author(self, author: AuthorName):
#         """
#         Возвращает список книг для автора
#         """
#         return [Book(name, author) for name in os.listdir(os.path.join(self.texts_path, author.full_name)) if not name.startswith('.')]
#
#     def __file_get_author_info(self, author: AuthorName):
#         """
#         Возвращает список книг для автора
#         """
#         r = ''
#         try:
#             with open(os.path.join(self.texts_path, author.full_name,'.info')) as f:
#                 r = f.read()
#         except:
#             pass
#         return r
#
#     def __file_get_book_info(self, book: Book):
#         """
#         Возвращает список книг для автора
#         """
#         r = ''
#         try:
#             with open(os.path.join(self.texts_path, book.author.full_name, book.full_name, '.info')) as f:
#                 r = f.read()
#         except:
#             pass
#         return r
#
#     # noinspection PyPep8Naming
#     def __file_get_book_TOC(self, book: Book) -> Content:
#         """
#         Возвращает содержание книги
#         """
#         # попробуем чтобы подглава могла иметь название, не только цифры
#         regexp = r"\[\[({})=([^]]+)]]".format('|'.join(self.fields2chapters.subchapter_level))
#         # regexp = r"\[\[({})=(\d+)]]".format('|'.join(self.fields2chapters.subchapter_level))
#         content = Content()
#         for chapter_name in [_ for _ in os.listdir(os.path.join(self.texts_path,
#                                                                 book.author.full_name,
#                                                                 book.full_name)) if not _.startswith('.')]:
#             chapter = _Chapter(chapter_name[:-4])  # отбрасываем .txt
#             with open(os.path.join(self.texts_path,
#                                    book.author.full_name,
#                                    book.full_name, chapter_name), 'r', encoding='utf8') as f:
#                 c = f.read()
#                 for subchapter_type, subchapter_name in re.findall(regexp, c):
#                     subchapter = _Subchapter(subchapter_name, subchapter_type)
#                     chapter.add_subchapter(subchapter)
#             content.add_chapter(chapter)
#         return content
#
#     def __file_get_text_by_link(self, link: Link) -> str:
#         """
#         Возвращает текст по ссылке
#         """
#         path = link.get_path_to_file()
#         fullpath = os.path.join(self.texts_path, path)
#         try:
#             with open("{}.txt".format(fullpath), 'r', encoding = 'utf8') as f:
#                 fulltext = f.read()
#         except FileNotFoundError:
#             return "??ЕЩЁ НЕ ПЕРЕВЕДЕНО??"
#         pattern = link.get_regexp()
#         print(pattern)
#         if pattern == r"(.+)":
#             # если нам нужен весь текст, проще отрезать служебные [[ в конце текста, чем делать это регекспом
#             fulltext = fulltext.rstrip()
#             if fulltext.endswith('[['):
#                 fulltext = fulltext[:-2].rstrip()
#         result = re.findall(pattern, fulltext, re.DOTALL)
#         if result:
#             return result[0]
#         else:
#             # вроде как при успешном поиске не должно такого быть
#             return "TEXT NOT FOUND"
#
#     def __file_get_term(self, term):
#         term = cyrtranslit.to_latin(term, 'ru')
#         fullpath = os.path.join(self.texts_path, 'TERM_DEFINITIONS', "{}.txt".format(term) )
#         # print(fullpath)
#         try:
#             with open(fullpath, 'r', encoding = 'utf8') as f:
#                 fulltext = f.read()
#             # fulltext = fulltext.replace('\n','<p>')
#             return fulltext
#         except FileNotFoundError:
#             return "DEFINITION NOT FOUND"
#
#     def get_quote_by_ref(self, link: Link) -> str:
#         """
#         Возвращает цитату по ссылке и refferer'y
#         :param link:
#         :return:
#         """
#         pass
#
#     # def get_term(self, term: str) -> str:
#     #     """
#     #     Возвращает подсказку для определения
#     #     """
#     #     pass


class FileStorage:
    def __init__(self, db_path):
        # print(db_path)
        self.texts_path = db_path
        # print(self.texts_path)
        # FIXME должно быть объявлено в классе обработчика инфы - надо поудмать, как это правильно указать
        self.info_filename = 'info'

    def get_xslt_path(self, book: Book, output_type='html') -> str:
        p = os.path.join(self.texts_path, book.author.storage_id, book.storage_id, '.meta', f'{output_type}.xslt')
        # Если для книги нет xslt файла для такго формата - используем файл общий для всего хранилища
        if os.path.exists(p):
            return p
        else:
            return os.path.join(self.texts_path, '.meta', f'{output_type}.xslt')

    def get_libraty_meta_filepath(self, full_filename):
        if full_filename:
            return full_filename
        filename = full_filename.split(os.path.sep)[-1]
        return os.path.join(self.texts_path, '.meta', filename)
    def get_book_text(self, book: Book) -> List[str]:
        result = []
        # на случай если надо искать что-то внутри других элементов, короче по параметрам
        # типа шестая глава в нескольких файлах, сперва собираем её, затем ищем там мишну

        # print(self.texts_path, book.author.full_name, book.full_name)
        # print(self.info_filename)
        files = [_ for _ in os.listdir(os.path.join(self.texts_path,
                                                    book.author.storage_id,
                                                    book.storage_id)) if _.endswith('.xml') and _ != self.info_filename]
        # print(files)
        # files.sort()
        for filename in files:
            filename = os.path.join(self.texts_path,
                                    book.author.storage_id,
                                    book.storage_id, filename)
            try:
                with open(filename,'r',encoding = 'utf8') as f:
                    result.append(f.read())
            except:
                pass
        return result


    def get_authors(self, language_code):
        """
        Возвращает список авторов, чьи книги доступны
        """
        return [AuthorName(full_name, self, language_code) for full_name in os.listdir(self.texts_path) if
                    not full_name.startswith('.')
                    and os.path.isdir(os.path.join(self.texts_path,full_name))]


    def get_books_for_author(self, author: AuthorName):
        """
        Возвращает список книг для автора
        """
        return [Book(name, author, self) for name in os.listdir(os.path.join(self.texts_path, author.storage_id)) if
                not name.startswith('.')
                and os.path.isdir(os.path.join(self.texts_path, author.storage_id, name))]

    def load_author_info(self, author: AuthorName):
        # print('parent', self.info_filename)
        # print(os.path.join(self.texts_path, author.full_name, self.info_filename))
        r = ''
        try:
            with open(os.path.join(self.texts_path, author.storage_id, self.info_filename), 'r', encoding = 'utf8') as f:
                r = f.read()
        except:
            with open(os.path.join(self.texts_path, author.storage_id, self.info_filename), 'w', encoding = 'utf8') as f:
                r = f"""<?xml version="1.0" standalone="yes"?>
<info>
    <ru>
        <title></title>
        <first_name>{author.storage_id}</first_name>
        <last_name></last_name>
        <short_name>{author.storage_id}</short_name>
    </ru>
	<display>
		<css_class_name>default</css_class_name>
	</display>
</info>

"""
                f.write(r)
        return r

    def load_book_info(self, book: Book):
        r = ''
        try:
            with open(os.path.join(self.texts_path,
                                   book.author.storage_id,
                                   book.storage_id,
                                   self.info_filename), 'r', encoding = 'utf8') as f:
                r = f.read()
        except:
            with open(os.path.join(self.texts_path,
                                   book.author.storage_id,
                                   book.storage_id,
                                   self.info_filename), 'w', encoding = 'utf8') as f:
                r = f"""<?xml version="1.0" standalone="yes"?>
<info>
    <ru>
        <full_name>{book.storage_id}</full_name>
        <short_name>{book.storage_id}</short_name>
    </ru>
</info>
"""
                f.write(r)
        return r


class XMLFormat:
    """
    Класс, обслуживающий хранилище текстов. К нему обращаются по человечески, а он уже ищет текст там, где он лежит и возвращает его
    """
    info_filename = 'info.xml'
    def __init__(self, texts_path = None):
        self.fields2chapters = None
        # если храниение в виде файлов
        self.texts_path = texts_path
        self.info_filename_ext = 'xml'


        if self.texts_path:
            self.fields2chapters = _FileStorage()

    def extract_toc_elements_form_xml(self, root):
        result = []
        children = root.getchildren()
        for child in children:
            if child.tag in ('header','page','daf'):
                result.append(child)
            r = self.extract_toc_elements_form_xml(child)
            result += r
        # for r in result:
        #     print(r)
        return result

    def build_book_TOC(self, text_tuple: List[str]) -> Content:
        """
        Возвращает содержание книги
        """
        content = Content()
        for text in text_tuple:
            root = etree.fromstring(text)
            # root = ET.fromstring(text)
            # toc_elements = root.findall('.//header')
            # Так как может быть только либо страница, либо лист - оставим их вручную
            # pages_elements = root.findall('.//page')
            # daf_elements = root.findall('.//daf')
            # toc_elements.sort(key= lambda x: int(x.attrib['level']))
            toc_elements = self.extract_toc_elements_form_xml(root)
            for element in toc_elements:
                item = ContentItem()
                item.populate_from_xml_element(element)
                content.add_item(item)
        return content


    def select_text(self,text_tuple: List[str], link: Link) -> str:
        """
        Возвращает текст по ссылке
        """
        # print(text_tuple)
        # print(link.page, link.daf,link.params)
        if not text_tuple:
            return "??ЕЩЁ НЕ ПЕРЕВЕДЕНО??"
        result = ""
        # на случай если надо искать что-то внутри других элементов, короче по параметрам
        # типа шестая глава в нескольких файлах, сперва собираем её, затем ищем там мишну
        elements = []
        params = []
        temp_root = etree.Element('content')
        for text in text_tuple:
            b_text = text
            root = etree.fromstring(b_text)

            # root = ET.fromstring(text)
            if link.page:
                # TODO когда отображается страница - было бы хорошо показывать заголовки которые в ней. например, если заканчивается один маймор и
                #  начинается другой - вставить заголовок с сылкой

                for element in root.findall(f".//page[@name='{link.page}']"):
                    temp_root.append(element)
                # print('*')
                # print(temp_root.getchildren())
                # result = etree.tostring(temp_root, pretty_print = True, encoding = 'utf8').decode('utf8')
                # for t in element.itertext():
                #     t = t.strip()
                #     result += f"\n{t}"
            elif link.daf:
                temp_root = etree.Element('content')
                for element in root.findall(f".//daf[@name='{link.daf}']"):
                    temp_root.append(element)
                # result = etree.tostring(temp_root, pretty_print = True, encoding = 'utf8').decode('utf8')
                # for t in element.itertext():
                #     t = t.strip()
                #     result += f"\n{t}"
            # else:
            # print(link.params)
            # Так как адресация может быть и после указания страницы
            if link.params:
                if len(temp_root):
                    # print('making new root')
                    root = temp_root
                    # print([_ for _ in root.getchildren()])
                    # print(link.params)
                    # print(root.findall(f".//header[@type='amud']"))
                import copy
                params = copy.deepcopy(link.params)
                main_param,main_param_value = params.pop(0)

                for element in root.findall(f".//header[@type='{main_param}']"):
                    if element.attrib['name'] == main_param_value:
                        elements.append(element)

                # return "??ЕЩЁ НЕ ПЕРЕВЕДЕНО??"
                # root.findall(".//header[@type='letter']")
        if len(temp_root)>0 and not link.params:
            from texts.xml_utils import remove_girsaot
            remove_girsaot(temp_root)
            result = etree.tostring(temp_root, pretty_print = True, encoding = 'utf8').decode('utf8')
        # print('deep search? ',elements)
        if elements:
            while params:
                new_elements = []
                main_param, main_param_value = params.pop(0)
                # print(main_param, main_param_value)
                for element in elements:
                    for c in element.findall(f".//header[@type='{main_param}']"):
                        if c.attrib['name'] == main_param_value:
                            new_elements.append(c)
                elements = new_elements
                # print(elements)
            result = ""
            # TODO надо объединять одинаковые элементы. Проще всего заменить страницы и листы детскими элементами, а затем пройтись по списку и
            #  сшить одинаоквые элементы
            root = etree.Element('content')
            for element in elements:
                # print('append ',element)
                root.append(element)
            import html


            from texts.xml_utils import copy_wihtout_pages, remove_girsaot
            new_root = copy_wihtout_pages(root)
            # print(link.params)
            # Если мы не ищем гирсу - убираем не основные версии
            if 'girsa' not in [_[0] for _ in link.params]:
                remove_girsaot(new_root)

            # if '5682' in link.book.full_name:
            #     with open(r'F:\TEMP\0004.xml', 'w', encoding = 'utf8') as f:
            #         f.write(html.unescape(etree.tostring(new_root, pretty_print = True).decode('utf8')))
            # for element in elements:
            #     result += etree.tostring(element, pretty_print = True, encoding = 'utf8').decode('utf8')
            result = etree.tostring(new_root, pretty_print = True, encoding = 'utf8').decode('utf8')
            # print(new_root)
            # with open(r'F:\TEMP\0004.xml', 'w', encoding = 'utf8') as f:
            #     f.write(html.unescape(etree.tostring(new_root, pretty_print = True).decode('utf8')))
        if result:
            return result.strip()
        else:
            # вроде как при успешном поиске не должно такого быть
            return "TEXT NOT FOUND"


    def get_quotes(self, text: str) -> List[Tuple[Link,str]]:
        root = etree.fromstring(text)
        result = []
        for element in root.findall(r".//quote"):
            link = Link()
            link.set_author_name(AuthorName(element.attrib['author'], self))
            link.set_book(Book(element.attrib['book'], link.author_name, self))
            params = element.keys()
            params.pop(params.index('author'))
            params.pop(params.index('book'))
            for key in params:
                link.set_param(key, element.attrib[key])
            result.append((link, etree.tostring(element, with_tail=False).decode('utf8')))
        return result
    def get_links(self, text: str) -> List[Tuple[Link,str,str]]:
        import html
        root = etree.fromstring(text)
        result = []
        for element in root.findall(r".//link"):
            link = Link()
            link.set_author_name(AuthorName(element.attrib['author'], self))
            link.set_book(Book(element.attrib['book'], link.author_name, self))
            params = element.keys()
            link.upper = False
            if 'upper' in params:
                link.upper = True
                params.pop(params.index('upper'))
            params.pop(params.index('author'))
            params.pop(params.index('book'))
            for key in params:
                link.set_param(key, element.attrib[key])
            result.append((link,
                           element.text,
                           html.unescape(etree.tostring(element, with_tail=False).decode('utf8'))))
        return result

    def htmlizer(self, text: str, xslt_path: str) -> str:
        """
        Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
        раши на брейшис или шмойс
        """
        # import lxml.etree as ET

        root = etree.fromstring(text)
        xslt = etree.parse(xslt_path)
        transform = etree.XSLT(xslt)
        newdom = transform(root)
        text = etree.tostring(newdom, encoding = 'utf8', pretty_print = True).decode('utf8')
        return text

    # def simple_htmlizer(self, text: str, xslt_path: str) -> str:
    #     """
    #     Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
    #     раши на брейшис или шмойс
    #     """
    #     # import lxml.etree as ET
    #
    #     root = etree.fromstring(text)
    #     xslt = etree.parse(xslt_path)
    #     transform = etree.XSLT(xslt)
    #     newdom = transform(root)
    #     text = etree.tostring(newdom, encoding = 'utf8', pretty_print = True).decode('utf8')
    #     return text

    # def parse_author_info(self, info):
    #     root = etree.fromstring(info)
    #     r = dict()
    #     def element_to_dict(e):
    #         tmp = dict()
    #         for a in e.attrib.keys():
    #             tmp[a] = e.attrib[a]
    #         tmp['value'] = e.text
    #         for c in e.getchildren():
    #             tmp[c.tag] = element_to_dict(c)
    #         return tmp
    #     r = element_to_dict(root)
    #     return r

    def parse_info(self, info):
        root = etree.fromstring(info)
        r = AllwaysDictDict()
        def element_to_dict(e):
            tmp = AllwaysDictDict()
            for a in e.attrib.keys():
                tmp[a] = e.attrib[a]
            tmp['value'] = e.text
            for c in e.getchildren():
                tmp[c.tag] = element_to_dict(c)
            return tmp
        r = element_to_dict(root)
        return r



    # def get_term(self, term: str) -> str:
    #     """
    #     Возвращает подсказку для определения
    #     """
    #     pass


class AllwaysDictDict:
    def __init__ (self):
        self.dict = dict()

    def __setitem__ (self, key, value):
        self.dict[key] = value

    def __getitem__ (self, key):
        if key not in self.dict.keys():
            if key=='value':
                return ''
            else:
                self.dict[key] = AllwaysDictDict()
        return self.dict[key]
        # return ""

    # def __str__ (self):
    #     return ""

class Storage(FileStorage, XMLFormat):


    def __init__(self, db_path):
        # TODO разобраться почему так

        class ConfigurationError(Exception):
            pass
        storage_class_name = None
        format_class_name = None
        for c in self.__class__.__bases__:
            if c.__name__.endswith('Format'):
                format_class_name = c.__name__
            elif c.__name__.endswith("Storage"):
                storage_class_name = c.__name__
        if not format_class_name and not storage_class_name:
            raise ConfigurationError("Не указаны классы хранилища и/или формата")
        # FileStorage.__init__(self, db_path)
        # XMLFormat.__init__(self)
        globals()[storage_class_name].__init__(self, db_path)
        globals()[format_class_name].__init__(self)
        # print(self.texts_path)
        self.texts_path = db_path
        # print(self.texts_path)
        # FIXME надо подумать, можно ли автоматом понимать, какой клас подмешен

        self.info_filename = XMLFormat.info_filename

    def get_text_by_link(self, link: Link) -> str:
        full_book_text = self.get_book_text(link.book)

        text = self.select_text(full_book_text, link)
        # print("*"*20)
        # print(full_book_text)
        # print("*"*20)
        return text

    def get_book_TOC(self, book: Book) -> Content:
        """
        Возвращает содержание книги
        """
        full_book_text = self.get_book_text(book)
        content = self.build_book_TOC(full_book_text)
        return content

    def get_author_info(self, author: AuthorName):
        raw_info = self.load_author_info(author)
        # Если информации о книги нет - возвращаем словарь, который возвращает себя на любом уровне вложенности
        if not raw_info:
            return AllwaysDictDict()
        info = self.parse_info(raw_info)
        return info

    def get_book_info(self, book: Book):
        raw_info = self.load_book_info(book)
        # Если информации о книги нет - возвращаем словарь, который возвращает себя на любом уровне вложенности
        if not raw_info:
            return AllwaysDictDict()
        info = self.parse_info(raw_info)
        return info
