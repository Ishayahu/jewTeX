# -*- coding: utf-8 -*-
# from typing import List, Optional, Callable, ClassVar
import lxml.etree

from texts.biblio import AuthorName, Book
import texts.biblio
# import cyrtranslit
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
               'din', 'page', 'dibur_amathil', 'siman_katan', 'question', 'mishna', 'perek', 'amud', 'mizva', 'part',
               'letter', 'gate','posuk', 'daf']
_all_fields_ru = ['author', 'book', 'siman', 'chapter', 'klal', 'sub_chapter', 'сеиф',
               'закон', 'стр', 'дибур аматхиль', 'симан катан', 'вопрос', 'мишна', 'perek', 'лист', 'заповедь', 'часть',
                  'буква', 'врата','стих','лист']

def getStartYear(i) -> int:
    # print(i.info['ru']['first_name']['value'], i.info['ru']['start_year']['value'])
    # return 3
    try:
        # print(i.info['ru']['first_name']['value'], i.info['ru']['start_year']['value'])
        return int(i.info['ru']['start_year']['value'])
    except ValueError:
        # print(i.info['ru']['first_name']['value'], 6001)
        return 6001

def params_sort_key(x):
    if(type(x)==type('')):
        key = x
    else:
        key = x[0]
    try:
        return {
                'dibur_amathil': 1,
                'j_chapter': 1,
                'chapter': 3,
                'posuk': 5,
                'mishna': 5,
                'daf': 3,
                'siman': 5,
                'seif': 7,
                'klal': 7,
                'letter': 10,
                'siman_katan': 10,
                'ref': 99,
                'girsa': 999
                }[key]
    except KeyError:
        print('key->', key)
        return 999

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



class Link:
    """
    Класс, который хранит информацию на ссылку в структурированной форме
    """

    def __init__(self, raw=''):

        self.author_name = None  # type: AuthorName
        self.book = None  # type: Book
        self.errors = []  # type: list
        self.params = []  # type: list
        self.page = ''  # type: str
        self.daf = ''  # type: str
        self.raw_params = ''  # type: str
        self.raw_string = raw

    def __repr__(self):
        return "{}|{}|{}".format(self.author_name, self.book, self.params)

    def str_inside_book_position(self):
        params_dict = dict()
        r = ""
        for k,v in self.params:
            if k!='xmlns':
                params_dict[k] = v

        # print(params_dict)
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
                if k!='xmlns':
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
            if key!='xmlns':
                self.params.append((key,value))
    def get_params(self):
        r = ''
        for k,v in self.params:
            r += f"{k}={v}&"
        if self.daf:
            r += f"daf={self.daf}"
        r = r.strip('&')
        return r

    def get_param(self, key):
        for k, v in self.params:
            if k == key:
                return v
        return ''

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
        self.children = []
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
        if 'number' in element.attrib:
            self.number = element.attrib['number']
        if 'verbouse_name' in element.attrib:
            self.verbouse_name = element.attrib['verbouse_name']
        if element.tag not in ('page','daf'):
            parent = element.getparent()
            # print(parent)
            while parent is not None:
                if 'type' in parent.attrib and 'name' in parent.attrib:
                    self.parents = f"{parent.attrib['type']}={parent.attrib['name']}&"+self.parents
                    # self.parents += f"{parent.attrib['type']}={parent.attrib['name']}&"
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
            # item.parent = self
            self.items.append(item)
        # self.items = sorted(self.items,key = lambda x: x.name)


    def set_current_place(self, link: Link):
        self.current_place = link
        self.prev_subchapter_params = False
        self.next_subchapter_params = False
        # self.current_found = False
        self.toc = []
        # print(link.get_params())
        def prepare_prev_and_next(item):
            for i in item.children:
                self.toc.append(i.get_link_params())
                prepare_prev_and_next(i)
            return

        for i in self.items:
            self.toc.append(i.get_link_params())
            if i.children:
                prepare_prev_and_next(i)
        print(self.toc)
        print(link.get_params())
        curr_idx = self.toc.index(link.get_params())
        print(curr_idx)
        while curr_idx > 0:
            if not link.get_params().startswith(self.toc[curr_idx-1]):
                self.prev_subchapter_params = self.toc[curr_idx-1]
                break
            curr_idx -= 1
        curr_idx = self.toc.index(link.get_params())
        while curr_idx+1 < len(self.toc):
            # print(self.toc[curr_idx+1])

            if not self.toc[curr_idx+1].startswith(link.get_params()):
                self.next_subchapter_params = self.toc[curr_idx+1]
                break
            curr_idx += 1


    def __eq__(self, other):
        for idx, chapter in enumerate(self.chapters):
                if chapter != other.chapters[idx]:
                    return False
        return True


class FileStorage:
    def __init__(self, db_path):
        # print(db_path)
        self.texts_path: str = db_path
        # print(self.texts_path)
        # self.info_filename = 'info'

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
        """
        Получаем полный текст всех файлов в каталоге книги,
        так как на уровне хранилища мы не знаем, что именно нам надо, ведь это зависит от формата

        Возвращаем имеенно всю книгу
        на случай если надо искать что-то внутри других элементов, короче по параметрам
        типа шестая глава в нескольких файлах, сперва собираем её, затем ищем там мишну

        :param book: Книга
        :return: кортедж строк, по строке на каждый файл
        """
        result = []

        files = [_ for _ in os.listdir(os.path.join(self.texts_path,
                                                    book.author.storage_id,
                                                    book.storage_id))]
        for filename in files:
            filename = os.path.join(self.texts_path,
                                    book.author.storage_id,
                                    book.storage_id, filename)
            try:
                with open(filename, 'r', encoding='utf8') as f:
                    result.append(f.read())
            except:
                pass
        return result


    def get_authors(self, s, language_code):
        """
        Возвращает список авторов, чьи книги доступны
        """
        result = [AuthorName(full_name, s, language_code) for full_name in os.listdir(self.texts_path) if
                  not full_name.startswith('.')
                  and os.path.isdir(os.path.join(self.texts_path, full_name))]
        # return sorted(result, key=lambda x: x.info['ru']['first_name']['value'])


        return sorted(result, key=getStartYear)

    def get_books_for_author(self, author: AuthorName, s):
        """
        Возвращает список книг для автора
        """
        return [Book(name, author, s) for name in os.listdir(os.path.join(self.texts_path, author.storage_id)) if
                not name.startswith('.')
                and os.path.isdir(os.path.join(self.texts_path, author.storage_id, name))]

    def load_author_info(self, author: AuthorName, info_filename: str):
        # print('parent', self.info_filename)
        # print(os.path.join(self.texts_path, author.full_name, self.info_filename))
        r = ''
        try:
            with open(os.path.join(self.texts_path, author.storage_id, info_filename), 'r', encoding='utf8') as f:
                r = f.read()
        except:
            with open(os.path.join(self.texts_path, author.storage_id, info_filename), 'w', encoding='utf8') as f:
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

    def load_book_info(self, book: Book, info_filename: str):
        r = ''
        try:
            with open(os.path.join(self.texts_path,
                                   book.author.storage_id,
                                   book.storage_id,
                                   info_filename), 'r', encoding='utf8') as f:
                r = f.read()
        except:
            with open(os.path.join(self.texts_path,
                                   book.author.storage_id,
                                   book.storage_id,
                                   info_filename), 'w', encoding='utf8') as f:
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

    def load_book_metainfo(self, book: Book, info_filename: str):
        return os.path.getmtime(os.path.join(self.texts_path,
                             book.author.storage_id,
                             book.storage_id,
                             info_filename))



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
            if child.tag in ('header',):
                # Для хидеров мы пропускам все хидеры, которые обозначают место для ссылки
                try:
                    if child.attrib['type'] in ('ref', 'girsa'):
                        pass
                    else:
                        result.append(child)
                except KeyError:
                    pass
            elif child.tag in ('page', 'daf'):
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
        toc_elements = []
        for text in text_tuple:
            root = etree.fromstring(text)
            # выбираем все элементы, которые должны быть в содержании
            t_toc_elements = self.extract_toc_elements_form_xml(root)
            toc_elements += t_toc_elements
        print(toc_elements)

        def get_sort_key(x):
            try:
                return int(x.number)
            except AttributeError:
                try:
                    return int(x.name)
                except ValueError:
                    return x.name



        # для каждого уровня:
        def make_TOC_structure (sorted_toc_elements, toc_elements, level):
            def make_parent_code(p):
                """код родителя, чтобы понять, его ли это сын"""
                c = ''
                c += f"{p.type}={p.name}"
                if p.parents:
                    c = p.parents +'&'+ c
                return c
            def collect_all_parents(parents):
                r = []
                for p in parents:
                    r.append(p)
                    r += collect_all_parents(p.children)
                return r

            current_level_elements = [e for e in toc_elements if int(e.level) == level]
            # оговорка на случай если верхний уровень - первый, то есть нулевого уровня не было
            if level==0 or (level==1 and not sorted_toc_elements):
                current_level_elements.sort(key=get_sort_key)
                for e in current_level_elements:
                    sorted_toc_elements.append(e)

            else:
                # если элементов не осталось - всё
                if not current_level_elements:
                    return
                # уже добавленные элементы - чтобы избежать повторного добавления элемента, разбитого страницей
                already_added = set()
                all_parents = collect_all_parents(sorted_toc_elements)

                # если это не 0 уровень, значит уже есть родители - надо им добавить детей
                for e in current_level_elements:
                    if f'{e.type}={e.name}' not in already_added:
                        # находим родителя:
                        for p in all_parents:
                            if e.parents == make_parent_code(p):
                                p.children.append(e)
                                # мы добавили такой элемент для этого родителя, а для других - нет
                                pid = id(p)
                                already_added.add(f'{pid}.{e.type}={e.name}')
            make_TOC_structure(sorted_toc_elements, toc_elements, level+1)

        toc_elements_with_info = []
        pages = []
        for element in toc_elements:
            item = ContentItem()
            item.populate_from_xml_element(element)
            if item.type=='page':
                pages.append(item)
            else:
                toc_elements_with_info.append(item)

        sorted_content = []

        make_TOC_structure(sorted_content, toc_elements_with_info, 0)


        pages.sort(key=lambda x:x.name)
        for item in pages:
            content.add_item(item)
        for item in sorted_content:
            content.add_item(item)

        return content

    @staticmethod
    def select_text(text_tuple: List[str], link: Link) -> lxml.etree.Element:
        """
        Возвращает текст по ссылке
        """
        if not text_tuple:
            return "??ЕЩЁ НЕ ПЕРЕВЕДЕНО??"
        # на случай если надо искать что-то внутри других элементов, короче по параметрам
        # типа шестая глава в нескольких файлах, сперва собираем её, затем ищем там мишну
        elements = []
        for text in text_tuple:
            root = etree.fromstring(text)
            # Указана страница
            if link.page:
                for element in root.findall(f".//page[@name='{link.page}']"):
                    elements.append(element)
            # Указан лист
            elif link.daf:
                for element in root.findall(f".//daf[@name='{link.daf}']"):
                    elements.append(element)
            # Указано что-то другое - пока просто добавляем, потом будем фильтровтаь
            else:
                elements.append(root)
        import copy
        params = copy.deepcopy(link.params)
        # тут нужно сортировать, чтобы параметры шли в правильном порядке,
        # так как сперва выбираем куски покрупнее, а затем уже поконкретнее
        params.sort(key=params_sort_key)
        while params:
            new_elements = []
            main_param, main_param_value = params.pop(0)
            for element in elements:
                xpath = f".//header[@type='{main_param}'][@name='{main_param_value}']"
                for c in element.findall(xpath):
                    new_elements.append(c)
            elements = new_elements

        root = etree.Element('content')
        for element in elements:
            for child in element.getchildren():
                root.append(child)

        from texts.xml_utils import copy_wihtout_pages, remove_girsaot
        # Если мы не ищем гирсу - убираем не основные версии
        if 'girsa' not in [_[0] for _ in link.params]:
            remove_girsaot(root)


        return root




    def parse_info(self, info):
        root = etree.fromstring(info)
        r = AllwaysDictDict()
        def element_to_dict(e):
            tmp = AllwaysDictDict()
            for a in e.attrib.keys():
                tmp[a] = e.attrib[a]
            tmp['value'] = ''
            if e.text:
                tmp['value'] = e.text

            for c in e.getchildren():
                tmp[c.tag] = element_to_dict(c)
            return tmp
        r = element_to_dict(root)
        return r


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


class Storagev2:
    """
    Класс хранилища, который отвечает за поиск/выборку текста
    """
    def __init__(self, storageType, storageFormat):
        """

        :param storageType: Тип хранилища (файловый, в памяти и тп)
        :param dataFormat: Формат данных в хранилищие
        """
        self.__storageType = storageType
        self.__storageFormat = storageFormat

    def get_text_by_link(self, link: Link) -> str:
        # TODO в иделае это надо разделить на формат/хранилище. ну или забить на эту идею
        def getText(link: Link):
            text = self.__storageType.get_book_text(link.book)
            root: etree.Element = self.__storageFormat.select_text(text, link)
            # сперва работаем над деревом и там меняем узлы (ссылки/вставки)
            # а лишь потом htmlizer
            # print(etree.tostring(root, pretty_print=True, encoding='utf8').decode('utf8'))
            # 1) сперва вставляем все цитаты
            for quote in root.findall(".//quote"):

                link = Link()
                author = AuthorName(quote.attrib['author'], self, 'ru')
                link.set_author_name(author)
                link.set_book(Book(quote.attrib['book'], author, self, 'ru'))
                for a in quote.attrib.keys():
                    if a not in ('author', 'book'):
                        link.set_param(a, quote.attrib[a])
                # для каждой цитаты получаем полный текст, с заменой в нём всех цитат
                quoteRoot = getText(link)
                quoteRoot.tag = 'quote'
                quote.getparent().replace(quote, quoteRoot)
            return root
        # 0) получаем полный текст, с подменой всех цитат
        root = getText(link)
        # 2) Когда всё готово - модифицируем ссылки для замены
        for alink in root.findall(".//link"):
            localLink = Link()
            localAuthor = AuthorName(alink.attrib['author'], self, 'ru')
            localBook = Book(alink.attrib['book'], localAuthor, self, 'ru')
            localLink.set_author_name(localAuthor)
            localLink.set_book(localBook)
            for k, v in alink.attrib.items():
                if k not in ('author', 'book', 'upper'):
                    localLink.set_param(k, v)
            span = etree.Element('span')
            span.attrib['class'] = "ajax-block"
            a = etree.Element('a')
            a.attrib['href'] = "#!"
            a.attrib['class'] = "js-ajax-link"
            a.attrib['data-ajax-url'] = f"/api/text/{localAuthor.storage_id}/{localBook.storage_id}/{localLink.get_params()}/"
            a.text = alink.text
            a.tail = alink.tail
            span.append(a)
            if 'upper' in alink.attrib:
                sup = etree.Element('sup')
                sup.append(span)
                alink.getparent().replace(alink, sup)
            else:
                alink.getparent().replace(alink, span)

        # 3) применяем XSLT это
        xslt_path = self.__storageType.get_xslt_path(link.book)
        xslt = etree.parse(xslt_path)
        transform = etree.XSLT(xslt)
        newdom = transform(root)
        text = etree.tostring(newdom, encoding='utf8', pretty_print=True).decode('utf8')

        return text.replace('xmlns="" ', '')


    def get_book_TOC(self, book: Book) -> Content:
        """
        Возвращает содержание книги
        """
        full_book_text: List[str] = self.__storageType.get_book_text(book)
        content = self.__storageFormat.build_book_TOC(full_book_text)
        return content

    def get_author_info(self, author: AuthorName):
        """
        Заргузить и распарсить информацию об авторе
        :param book:
        :return:
        """
        raw_info = self.__storageType.load_author_info(author, self.__storageFormat.info_filename)
        # Если информации о книги нет - возвращаем словарь, который возвращает себя на любом уровне вложенности
        if not raw_info:
            return AllwaysDictDict()
        info = self.__storageFormat.parse_info(raw_info)
        return info

    def get_book_info(self, book: Book):
        """
        Заргузить и распарсить информацию о книге
        :param book:
        :return:
        """
        raw_info = self.__storageType.load_book_info(book, self.__storageFormat.info_filename)
        # Если информации о книги нет - возвращаем словарь, который возвращает себя на любом уровне вложенности
        if not raw_info:
            return AllwaysDictDict()
        info = self.__storageFormat.parse_info(raw_info)
        return info

    def get_book_metainfo(self, book: Book):
        """
        Заргузить и распарсить мета-информацию о книге (дата создания каталога например)
        :param book:
        :return:
        """

        raw_info = self.__storageType.load_book_metainfo(book, self.__storageFormat.info_filename)
        # Если информации о книги нет - возвращаем словарь, который возвращает себя на любом уровне вложенности
        if not raw_info:
            return AllwaysDictDict()

        return raw_info

    def get_authors(self, lang):
        return self.__storageType.get_authors(self, lang)

    def get_books_for_author(self, author: AuthorName):
        return self.__storageType.get_books_for_author(author, self)
