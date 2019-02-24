from django.shortcuts import render
from django.http import HttpResponse
import os
import re
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
import texts.authors
from texts.authors import normalize_author, normalize_book
import cyrtranslit

from django.http import JsonResponse

TEXTS_PATH = os.path.join(os.getcwd(),'TEXTS_DB')


def get_author(author):
    author = normalize_author(author)
    return authors.get(author, texts.authors.DEFAULT_AUTHOR)()


authors = {normalize_author('таз'): texts.authors.Taz,
           normalize_author('шах'): texts.authors.Shah,
           normalize_author('смак'): texts.authors.Smak,
           }


def parser(link, author, book, params):
    """
    Из автора (в полном или сокрыщённом виде), книги и параметров получаем запрос, по которому будем искать текст. params что-то вроде глава=4&пункт=8
    :param link: Link
    :param author: str
    :param book: str
    :param params: str
    """
    # if author in author_kitzur:
    #     author = author_kitzur[author]
    # author = normalize_author(author)
    link.set_author(author)
    link.set_book(book)
    for k, v in re.findall('([^=]*)=([^&]*)&?',params):
        link.add_by_key_value(k, v)


class Link:
    """
    Доступные для заполнения поля:
    автор
    книга
    глава/симан
    параграф/сеиф
    """
    def __init__(self):
        self.author = None
        self.book = None
        self.siman = None
        self.chapter = None
        self.sub_chapter = None
        self.seif = None
        self.page = None
        self.dibur_amathil = None
        self.siman_katan = None
        #TODO надо сделать API для получения id referrer'a
        self.referrerer = None
        self.errors = []

        self.in_file = ['siman_katan','page','seif','dibur_amathil']

    def add_by_key_value(self,k,v):
        if k=='chapter':
            self.set_chapter(v)
        elif k=='siman':
            self.set_siman(v)
        elif k=='seif':
            self.set_seif(v)
        elif k=='page':
            self.set_page(v)
        elif k=='dibur_amathil':
            self.set_dibur_amathil(v)
        elif k=='siman_katan':
            self.set_siman_katan(v)
        elif k=='referrerer':
            self.set_referrerer(v)

    def set_author(self, v):
        self.author = v

    def set_book(self, v):
        self.book = v

    def set_siman(self, v):
        self.siman = v
        self.chapter = v

    def set_chapter(self, v):
        self.chapter = v

    def set_seif(self, v):
        self.seif = v
        self.sub_chapter = v

    def set_page(self, v):
        self.page = v
        self.chapter = v

    def set_dibur_amathil(self, v):
        self.dibur_amathil = v
        self.sub_chapter = v

    def set_siman_katan(self, v):
        self.siman_katan = v
        self.sub_chapter = v

    def set_referrerer(self, v):
        self.referrerer = v

    def short_str(self):
        return "{}:{}".format(self.chapter, self.sub_chapter)

    def __str__(self):
        return """{}:{} глава {} симан {}<p>
        сеиф {} страница {} дибур аматхиль {} симан катан {}<p>
        кто ссылался {}""".format(
            self.author, self.book, self.chapter, self.siman, self.seif, self.page, self.dibur_amathil,
            self.siman_katan, self.referrerer)

    def __repr__(self):
        return self.__str__()

    def validate(self):
        if not self.author:
            self.errors.append("Не указан автор")
        if not self.book:
            self.errors.append("Не указана книга")
        if not self.chapter and not self.siman:
            self.errors.append("Не указана глава или симан")
        if self.errors:
            return False
        return True

    def get_path(self):
        filename = self.chapter if self.chapter else self.siman
        return os.path.join(*list(map(str,(self.author, self.book, filename))))

    def get_regexp(self):
        # если есть что-то, что ищем в файле
        if any([self.__getattribute__(_) for _ in self.in_file]):
            r = '.*'
            # TODO надо подумать над ним, но пока оставлю так, потому что ещё не ясно, какие варианты могут быть
            if self.siman_katan:
                r += r"\[\[siman_katan={}]].*?".format(self.siman_katan)
            if self.seif:
                r += r"\[\[seif={}]].*?".format(self.seif)
            if self.page:
                r += r"\[\[page={}]].*?".format(self.page)
            if self.dibur_amathil:
                r += r"\[\[dibur_amathil={}]].*?".format(self.dibur_amathil)
            # Добавляем содержимое
            r += "(.*?)"
            # if self.referrerer:
            #     r += r"\[\[/{}]]".format(self.referrerer)
            # else:
            #     r += r"\[\["

            # до следующего такого же
            if self.siman_katan:
                r += r"(?:\[\[siman_katan=.*|\[\[$)"
            if self.seif:
                r += r"(?:\[\[seif=|\[\[$)"
            if self.page:
                r += r"(?:\[\[page=|\[\[$)"
            if self.dibur_amathil:
                r += r"(?:\[\[dibur_amathil=|\[\[$)"



            # r += ".*"
            return r
        # если ничего такого нет и надо вернуть текст всего файла
        else:
            return r"(.+)"


def get_link():
    """
    Возвращает класс ссылки для заполнения её парсером и использования потом в получении текста
    :return: Link
    """
    return Link()


def get_text(link):
    """
    По запросу получаем из хранилища текст и возвращаем его
    :param request:
    :return: str
    """
    path = link.get_path()
    fullpath = os.path.join(TEXTS_PATH,path)
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



def htmlizer(text, link):
    """
    Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
    раши на брейшис или шмойс
    :param text: str
    :param link: Link
    :return: str
    """
    delimiters = '%'
    text = text.replace('\n','<p>')
    # заменяем <ramo> на <div class='ramo'>
    for to_replace, closing_tag, tag in re.findall(r'(<(/?)([^/>]+)>)',text):
        text = text.replace(to_replace,"<div class='{}'>".format(tag) if not closing_tag else "</div>")

    # обрабатываем "короткие" ссылки {{taz/1}} на ссылки /api/text/taz/taz_al_yore_dea/siman=92&siman_katan=1/
    for to_replace, author_kitzur_name, siman_katan in re.findall('({0}{0}([^/]+)/([^{0}]+){0}{0})'.format(delimiters),text):
        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
        # author_full_name = author_kitzur[author_kitzur_name]
        author_full_name = normalize_author(author_kitzur_name)
        # [('{{taz/1}}', 'taz', '1')]
        author = authors[author_full_name]()
        author.set_link_to_parent(link)
        author.siman_katan = siman_katan
        text = text.replace(to_replace,
                            '<sup><span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{name}</a></span></sup>'.format(
                                **author.get_link()))

    # в случае если delimiters = '%'
    # автор/книга могут содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
    # название параметра может содержать только английские буквы в нижнем регистре и нижнее подчёркивание
    # значение параметра может быть любым, но без % и &
    # название ссылки может содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
    # (%%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%([a-z_0-9]+)%%)
    # длинные ссылки
    # в качестве текста может быть всё, кроме ||
    # всё дальше - как выше для цитаты
    # (%%([^%]+)%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%%)

    # для теста можно использовать этот текст:
    # пишет, что %%maran:sha2:siman=106&seif=1%sha2_shah_92_11%%. А РАМО
    # дальше %%в начале главы 109%maran:sha2:siman=109&seif=1%%" [Другими словами

    # убираем разметку, которая нам тут не нужна
    for markdown in re.findall(r'\[\[[^]]+]]',text,re.M):
        text = text.replace(markdown, '')
    # убираем [[refferer=sha2_shah_92_11]] и [[/refferer=sha2_shah_92_11]]
    # for to_replace in re.findall('\[\[/?refferer=[a-z_0-9]+]]',text):
    #     text = text.replace(to_replace, '')

    # вставляем отрывки из других текстов
    # %%maran:sha2:siman=106&seif=1%refferer%%
    for to_replace, author_kitzur_name, book, params, refferer in re.findall(
            '({0}{0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}([a-z_0-9]+){0}{0})'.format(
            delimiters),text):
        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
        quote = get_quote(author_kitzur_name, book, params, refferer)
        text = text.replace(to_replace, '"{}"'.format(quote))

    # обрабатываем "длинные" ссылки (как в url)
    # %%в начале главы 106%maran:sha2:siman=106&seif=1%%
    for to_replace, link_text, author_kitzur_name, book, params in re.findall(
            '({0}{0}([^{0}]+){0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}{0})'.format(
            delimiters),text):
        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
        url = reverse('text_api_request', args = (author_kitzur_name, book, params))
        text = text.replace(to_replace,
                            '<span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{name}</a></span>'.format(
                                **{'url': url, 'name': link_text}))
    # **текст** как термины
    for term in re.findall('\*\*(.+?)\*\*',text):
        term_definition = get_term(term)
        text = text.replace("**{}**".format(term), '<span title="{1}" class="term">{0}</span>'.format(term, term_definition))
    # ??текст?? как то, что надо доработать
    for subtext in re.findall('\?\?(.+?)\?\?',text):
        text = text.replace("??{}??".format(subtext), '<span title="Требуется вставить ссылку/доработать" class="need_work">{}</span>'.format(
            subtext))
    return text



def get_term(term):
    term = cyrtranslit.to_latin(term,'ru')
    fullpath = os.path.join(TEXTS_PATH,'TERM_DEFINITIONS',term)
    try:
        with open("{}.txt".format(fullpath), 'r', encoding = 'utf8') as f:
            fulltext = f.read()
        # fulltext = fulltext.replace('\n','<p>')
        return fulltext
    except FileNotFoundError:
        return "DEFINITION NOT FOUND"



def get_response_by_link(request, link, template, context, add_navigation = True):
    # TODO пока работает только с числами
    text = get_text(link)
    # for openGraph
    context['description'] = "{}...".format(text[:50])
    context['title'] = "{}: {}".format(link.author,context.get('header',''))
    # TODO
    context['pulished_time'] = "{}".format("pulished_time")
    context['url'] = "{}".format("GET URL")


    html = htmlizer(text, link)
    context['text'] = html



    if add_navigation:
        context['up'] = reverse('book', kwargs={'author': link.author, 'book': link.book})
        content = get_book_content(link.author, link.book)
        context['prev'] = None
        context['next'] = None
        cur_chapter_idx = content.chapter_idx(link.siman)
        cur_seif_idx = content.chapters[cur_chapter_idx].seifim.index(str(link.seif))
        seif_count = len( content.chapters[cur_chapter_idx].seifim)
        if cur_seif_idx+1 < seif_count:
            context['next'] = reverse('open_by_siman_seif', kwargs={'author': link.author,
                                                                    'book': link.book,
                                                                    'siman':  int(content.chapters[cur_chapter_idx].name),
                                                                    'seif':  int(content.chapters[cur_chapter_idx].seifim[cur_seif_idx+1])})
        else:
            if int(cur_chapter_idx)+1 in content.chapters:
                context['next'] = reverse('open_by_siman_seif', kwargs = {'author': link.author,
                                                                          'book': link.book,
                                                                          'siman': int(content.chapters[cur_chapter_idx+1].name),
                                                                          'seif': int(content.chapters[int(cur_chapter_idx)+1].seifim[0])})
        if cur_seif_idx-1 >= 0:
            context['prev'] = reverse('open_by_siman_seif', kwargs={'author': link.author,
                                                                    'book': link.book,
                                                                    'siman': int(content.chapters[cur_chapter_idx].name),
                                                                    'seif':  int(content.chapters[cur_chapter_idx].seifim[cur_seif_idx-1]) })
        else:
            if int(cur_chapter_idx)-1 in content.chapters:
                context['prev'] = reverse('open_by_siman_seif', kwargs = {'author': link.author,
                                                                          'book': link.book,
                                                                          'siman':  int(content.chapters[cur_chapter_idx-1].name),
                                                                          'seif': int(content.chapters[int(cur_chapter_idx)-1].seifim[-1])})


    return render(request, template, context)




def open_text(request, author, book, params):
    print(params)
    author = normalize_author(author)
    book = normalize_book(book)

    link = get_link()

    parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    # text = get_text(link)
    # html = htmlizer(text, link)
    # return render(request, 'texts/open.html', {
    #     'title': '{}:{}'.format(author,book),
    #     'text':html
    # })

    return get_response_by_link(request, link, 'texts/open.html', {'title': '{}:{}'.format(author,book),
                                                                   'header': "{}:{}".format(link.siman, link.seif)}
                                )


def get_quote(author, book, params, refferer):
    print(params)
    author = normalize_author(author)
    book = normalize_book(book)

    link = get_link()

    parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = get_text(link)
    quote = re.findall('\[\[refferer={0}]](.*)\[\[/refferer={0}]]'.format(refferer),text, re.M)
    if quote:
        html = htmlizer(quote[0], link)
        return html
    return "NOT FOUND"


def api_request(request, author, book, params):
    print('api')
    print(params)

    author = normalize_author(author)
    book = normalize_book(book)
    link = get_link()
    parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = get_text(link)
    html = htmlizer(text, link)
    author = get_author(author)
    return  JsonResponse({'title': '{}:{}'.format(author.short_name,link.short_str()), 'content': html, 'cardColor': author.card_color})
    # return render(request, 'texts/clean_text.html', {
    #     'text':html
    # })
    # return get_response_by_link(request, link, 'texts/clean_text.html', {}, False)


def open_by_siman_and_seif(request, author, book, siman, seif):
    print('openby')

    author = normalize_author(author)
    book = normalize_book(book)

    link = get_link()
    link.set_author(author)
    link.set_book(book)
    link.set_siman(siman)
    link.set_seif(seif)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, link, link.errors))
    # text = get_text(link)
    # html = htmlizer(text, link)
    #
    # return render(request, 'texts/open.html', {
    #     'title': '{}:{}'.format(author,book),
    #     'text':html
    # })
    return get_response_by_link(request, link, 'texts/open.html', {'title': '{}:{}'.format(author,book),
                                                                   'header': "{}:{}".format(link.siman, link.seif)})




def get_authors():
    """
    По запросу получаем из хранилища текст и возвращаем его
    :param request:
    :return: str
    """

    return [_ for _ in os.listdir(TEXTS_PATH) if not _.startswith('.')]

def get_books(author):
    """
    По запросу получаем из хранилища текст и возвращаем его
    :param request:
    :return: str
    """

    return [_ for _ in os.listdir(os.path.join(TEXTS_PATH,author)) if not _.startswith('.')]

def index(request):
    authors = get_authors()
    return render(request, 'texts/index.html', {
        'authors':authors, 'title': "Список авторов"
    })

def author(request, author):
    books = get_books(author)
    return render(request, 'texts/author.html', {
        'books':books, 'author': author, 'title': "Список книг для {}".format(author)
    })

def get_book_content(author, book):
    """
    По запросу получаем из хранилища текст и возвращаем его
    :param request:
    :return: str
    """
    class Chapter:
        def __init__(self, name):
            self.seifim = []
            self.name = name
        def append(self, item):
            self.seifim.append(item)
        def __repr__(self):
            return self.__str__()
        def __str__(self):
            return "{}:{}".format(self.name, str(self.seifim))
        # def __iter__(self):
        #     return iter(self.seifim)

    class Content:
        def __init__(self):
            self.chapters = []
        def chapter_idx(self, chapter):
            return [_.name for _ in self.chapters].index(str(chapter))
        def __repr__(self):
            return self.__str__()
        def __str__(self):
            return str(self.chapters)

    content = Content()
    for chapter in [_ for _ in os.listdir(os.path.join(TEXTS_PATH,author, book)) if not _.startswith('.')]:
        content.chapters.append(Chapter(chapter[:-4])) # отбрасываем .txt
        with open(os.path.join(TEXTS_PATH,author, book,chapter),'r', encoding = 'utf8') as f:
            c = f.read()
            for seif in re.findall(r"\[\[seif=(\d+)]]",c):
                content.chapters[-1].append(seif)
    return content




def book(request, author, book):
    content = get_book_content(author, book)
    # raise ImportError
    return render(request, 'texts/book.html', {
        'content':content, 'author': author, 'book': book, 'title': "Содержание книги {} от {}".format(book, author)
    })
