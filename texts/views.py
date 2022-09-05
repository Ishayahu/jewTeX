from django.http import HttpResponse, HttpResponseRedirect
import os
import re
from django.shortcuts import render
from django.urls import reverse
from texts.storage import Link, Content
from texts.storage import Storagev2, FileStorage, XMLFormat, getStartYear
from texts.biblio import AuthorName, Book
from django.utils.translation import get_language_from_request
from django.http import JsonResponse


def error400(request, exception):
    """
    При ошибке поиска - возвращаем на главную страницу
    :type request: object
    :type exception: object
    """
    return HttpResponseRedirect('/')


def error500(request):
    return HttpResponseRedirect('/')


TEXTS_DB_PATH = os.path.join(os.getcwd(), 'TEXTS_DB')

s = Storagev2(
    storageType=FileStorage(TEXTS_DB_PATH),
    storageFormat=XMLFormat()
)

# TEXTS_PATH = os.path.join(os.getcwd(), 'TEXTS_DB')


def open_text(request, author_name, book_name, params, api):
    import time
    lang = get_language_from_request(request)
    # print(get_language_from_request(request))
    author_name = AuthorName(author_name, s, lang)
    book_name = Book(book_name, author_name, s, lang)
    # book_TOC: Content = s.get_book_TOC(book)

    link = Link()
    link.set_author_name(author_name)
    link.set_book(book_name)
    # link.set_chapter_name(chapter_name)
    link.set_params(params)
    # parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author_name, book_name, params, link, link.errors))

    text = s.get_text_by_link(link)

    if not api:
        book_toc = s.get_book_TOC(book_name)  # type:  Content
        print(book_toc)
        context = dict()
        context['text'] = text

        context['title'] = f'{author_name.full_name}: {book_name.full_name}: {link.str_inside_book_position()}'
        context['header'] = f'{author_name.full_name}: {book_name.full_name}: {link.str_inside_book_position()}'
        # for openGraph
        try:
            context['description'] = "{}...".format(text[:147])
            # context['description'] = "{}...".format(demarking(text,s.get_xslt_path(link.book,'quote_html'))[:200])
        except AttributeError:
            print('views.397')
            print(text)
            context['description'] = ''
        context['pulished_time'] = "%s" % time.ctime(s.get_book_metainfo(book_name))
        context['url'] = "{}".format(request.build_absolute_uri())
        context['link'] = link

        book_toc.set_current_place(link)
        context['up'] = reverse('book', kwargs={'author_name': link.author_name.storage_id,
                                                'book_name': link.book.storage_id})
        if book_toc.prev_subchapter_params:

            context['prev'] = reverse('open_from_xml', args=(link.author_name.storage_id,
                                                             link.book.storage_id,
                                                             book_toc.prev_subchapter_params))
        if book_toc.next_subchapter_params:
            context['next'] = reverse('open_from_xml', args=(link.author_name.storage_id,
                                                             link.book.storage_id,
                                                             book_toc.next_subchapter_params))
        return render(request, 'texts/open.html', context)
    else:
        title = '{} {}. {}: {}'.format(
            author_name.info[lang]['first_name']['value'],
            author_name.info[lang]['last_name']['value'],
            book_name.info[lang]['full_name']['value'],
            link.str_inside_book_position())
        text += f"<a target='_blank' href='{link.get_url()}'>К книге</a>"
        return JsonResponse({'title': title, 'content': text, 'cardColor':
                             author_name.info['display']['css_class_name']['value']})


# TODO генерировать odt документы. разобраться, почему они как с ошибкой и требуют восстановления


def index(request):
    language_code = get_language_from_request(request)
    authors = s.get_authors(language_code)

    class GroupedAuthors:
        @staticmethod
        class Group:
            def __init__(self, name):
                self.list = []
                self.name = name

            def append(self, author_instance):
                # print(self.list, len(self.list))
                self.list.append(author_instance)
                if len(self.list) == 1:
                    self.list[-1].first = True

            def __iter__(self):
                return self.list.__iter__()

        def __init__(self):
            self.__itercount = -1
            self.started = GroupedAuthors.Group('Ранние')
            self.zugot = GroupedAuthors.Group("Зугот")
            self.tanoim = GroupedAuthors.Group("Таноим")
            self.amaroim = GroupedAuthors.Group("Амароим")
            self.saburaim = GroupedAuthors.Group("Сабуроим")
            self.gaonim = GroupedAuthors.Group("Гаоним")
            self.rishonim = GroupedAuthors.Group("Ришоним")
            self.aharonim = GroupedAuthors.Group("Ахароним")
            self.others = GroupedAuthors.Group("Не указано")
            self.__groups = [
                self.started, self.zugot, self.tanoim, self.amaroim, self.saburaim,
                self.gaonim, self.rishonim, self.aharonim, self.others
            ]

        def __iter__(self):
            return self

        def __next__(self):
            self.__itercount += 1
            if self.__itercount < len(self.__groups):
                return self.__groups[self.__itercount]
            raise StopIteration

        def add(self, author_instance):
            # https://he.wikipedia.org/wiki/תקופת_הזוגות
            if getStartYear(author_instance) < 3570:
                self.started.append(author_instance)
            elif getStartYear(author_instance) < 3770:
                self.zugot.append(author_instance)
            # https://he.wikipedia.org/wiki/תנאים
            elif getStartYear(author_instance) < 4000:
                self.tanoim.append(author_instance)
            # https://he.wikipedia.org/wiki/אמוראים
            elif getStartYear(author_instance) < 4260:
                self.amaroim.append(author_instance)
            # https://he.wikipedia.org/wiki/סבוראים
            elif getStartYear(author_instance) < 4350:
                self.saburaim.append(author_instance)
            # https://he.wikipedia.org/wiki/גאונים
            elif getStartYear(author_instance) < 4800:
                self.gaonim.append(author_instance)
            # https://he.wikipedia.org/wiki/ראשונים
            elif getStartYear(author_instance) < 5250:
                self.rishonim.append(author_instance)
            # https://he.wikipedia.org/wiki/אחרונים
            elif getStartYear(author_instance) < 6000:
                self.aharonim.append(author_instance)
            else:
                self.others.append(author_instance)

    result = GroupedAuthors()
    for a in authors:
        result.add(a)
    return render(request, 'texts/index.html', {
        'authors': result, 'title': "Список авторов"
    })


def author(request, author_name):
    language_code = get_language_from_request(request)
    author_name = AuthorName(author_name, s, language_code)
    books = s.get_books_for_author(author_name)
    info = s.get_author_info(author_name)
    return render(request, 'texts/author.html', {
        'books': books, 'author': author_name,
        'title': "Список книг для {}".format(author_name),
        'info': info,
    })


def book(request, author_name, book_name):
    from django.template.loader import render_to_string
    import uuid
    language_code = get_language_from_request(request)
    author_name = AuthorName(author_name, s, language_code)
    book_name = Book(book_name, author_name, s, language_code)
    info = book_name.info['about']['value']
    content = s.get_book_TOC(book_name)

    def make_html_toc(elements):
        def makeuuid(element):
            result = uuid.uuid4()
            return result.hex

        if elements:
            rendered = ''
            for element in elements:
                rendered += render_to_string('texts/html_toc.html',
                                             {'element': element, 'element_id': makeuuid(element), 'author': author_name,
                                              'book': book_name})
                rendered += make_html_toc(element.children)
                if element.children:
                    rendered += '</ol>'
            return rendered
        else:
            return ''

    html_toc = make_html_toc(content.items)

    # print(content.items)
    lang = get_language_from_request(request)
    title = "Содержание книги {} от {} {}".format(book_name.info[lang]['full_name']['value'],
                                                  author_name.info[lang]['first_name']['value'],
                                                  author_name.info[lang]['last_name']['value'])
    return render(request, 'texts/book.html', {
        'content': content, 'html_toc': html_toc, 'author': author_name,
        'book': book_name,
        'title': title, 'info': info,
    })


def terms_to_define(request):
    result = []
    for root, directory, files in os.walk(TEXTS_DB_PATH):
        # print(root)
        if not '.git' in root:
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding='utf8') as f:
                    text = f.read()
                    for term in re.findall('<term>([а-яА-Я ]+)</term>', text):
                        term_definition = get_term_definition(term)
                        if not term_definition:
                            filepath = filepath.replace(TEXTS_DB_PATH, '')
                            result.append([term, filepath])
                        else:
                            pass
                            # print(term_definition)

    # for k in result:
    # print(k)

    terms = dict()
    for r in result:

        if r[0] not in terms:
            terms[r[0]] = set()
        terms[r[0]].add(r[1])
    print(terms)
    return render(request, 'texts/terms_to_define.html', {
        'terms': terms, 'title': "Термины без определения"
    })


def need_to_be_done(request):
    result = []
    for root, dir, files in os.walk(TEXTS_DB_PATH):
        print(root, dir)
        if not '.git' in root:
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding='utf8') as f:
                    for text in f.readlines():
                        term = re.findall('<work_needed>(.*?)</work_needed>', text)

                        if term:
                            # print(term)
                            for t in term:
                                import html
                                text = html.escape(text)
                                pattern = re.escape(f'&lt;work_needed&gt;{html.escape(t)}&lt;/work_needed&gt;')
                                text = re.sub(pattern, f'<span style="background-color:red">{t}</span>', text)
                            filepath = filepath.replace(TEXTS_DB_PATH, '')
                            result.append([text, filepath])
    # print(result)
    return render(request, 'texts/need_to_be_done.html', {
        'result': result, 'title': "Требуется доработка"
    })


def need_to_translate(request):
    result = []
    count = 0
    for root, dir, files in os.walk(TEXTS_DB_PATH):
        print(root, dir)
        if not '.git' in root:
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding='utf8') as f:
                    for text in f.readlines():
                        term = re.findall('<link_needed>(.*?)</link_needed>', text)

                        if term:
                            # print(term)
                            for t in term:
                                import html
                                text = html.escape(text)
                                pattern = re.escape(f'&lt;link_needed&gt;{html.escape(t)}&lt;/link_needed&gt;')
                                text = re.sub(pattern, f'<span style="background-color:red">{t}</span>', text)
                            filepath = filepath.replace(TEXTS_DB_PATH, '')
                            result.append([text, filepath])
                            count += 1
                            if count > 20:
                                return render(request, 'texts/need_to_be_done.html', {
                                    'result': result, 'title': "Требуется перевести"
                                })

    # print(result)
    return render(request, 'texts/need_to_be_done.html', {
        'result': result, 'title': "Требуется перевести"
    })


def search(request):
    if request.method != 'POST':
        raise ImportError()
    a = request.POST
    search_string = request.POST.get('search_string', '')
    if not search_string:
        raise ImportError()
    from pathlib import Path
    from lxml import etree
    # find = etree.XPath(f"//p[re:test(.,'{search_string}','i')]",
    #                    namespaces={'re': "http://exslt.org/regular-expressions"})
    find = etree.XPath(f"//p[re:test(.,'{search_string}','i')] | //p[re:test(.,'{search_string}','i')]",
                       namespaces={'re': "http://exslt.org/regular-expressions"})
    # db_path = r'D:\YandexDisk\Sites\jewTeX\TEXTS_DB'
    found = []

    def check_out_path(target_path, level=0):
        """"
        This function recursively prints all contents of a pathlib.Path object
        """
        for file in target_path.iterdir():
            if file.is_dir():
                check_out_path(file, level + 1)
            else:
                if file.name.endswith('.xml'):
                    content = None
                    with open(file, 'r', encoding='utf8') as f:
                        content = f.read()
                    if content:
                        root = etree.XML(content)
                        for e in find(root):
                            found.append((file, e))

    my_path = Path(s.texts_path)
    check_out_path(my_path)
    result = []

    class Link:
        def __init__(self):
            self.author = None
            self.book = None
            self.link = None
            self.text = None

    for file, e in found:
        author = file.parts[-3]
        book = file.parts[-2]
        l = Link()
        l.author = author
        l.book = book
        l.text = e.text

        tmp = []
        while e.tag != 'content':
            if e.tag == 'header':
                tmp.append((e.attrib['type'], e.attrib['name']))
            e = e.getparent()
        tmp.reverse()
        ll = ''
        for k, v in tmp:
            ll += f"{k}={v}&"
        ll = ll[:-1]
        l.link = ll
        result.append(l)

    return render(request, 'texts/found.html', {
        'found': result, 'title': "Найдено"
    })


def get_term_definition(term):
    term_path = os.path.join(os.getcwd(), 'TEXTS_DB', 'TERM_DEFINITIONS', f"{term}.txt")
    if os.path.isfile(term_path):
        with open(term_path, 'r', encoding='utf8') as f:
            return f.read()
    else:
        return False


def api_term(request, term):
    result = {
        'name': term,
        'definition': get_term_definition(term)
    }
    return JsonResponse(result)
