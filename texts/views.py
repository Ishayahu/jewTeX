from django.shortcuts import render
from django.http import HttpResponse
import os
import re
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
# import texts.authors
# from texts.authors import normalize_author, normalize_book
import cyrtranslit
from texts.storage import Storage, Link, Content
from texts.biblio import AuthorName, Book, get_author

s = Storage(os.path.join(os.getcwd(), 'TEXTS_DB'))

from django.http import JsonResponse

TEXTS_PATH = os.path.join(os.getcwd(),'TEXTS_DB')
delimiters = '%'

def close_unclosed_tags(text):
    temp_text = text
    opened_tags = []
    closed_tags = []
    r = re.search(r'(</?([^>]+)>)', temp_text)
    while r:
        print(r.groups())
        tag, tag_name = r.groups()
        if tag[1] == '/':
            # ищем последнее вхождение этого тега и убираем его
            try:
                last_index = len(opened_tags) - 1 - opened_tags[::-1].index(tag_name)
                opened_tags.pop(last_index)
            except ValueError:  # значит, начинается с закрывающего тега - надо добавить открывающий в начале
                closed_tags.append(tag_name)
        else:
            opened_tags.append(tag_name)
        temp_text = temp_text.replace(tag, '', 1)
        r = re.search(r'(</?([^>]+)>)', temp_text)
    print(opened_tags)
    # добавляем в текст незакрытые теги в конце
    for t in opened_tags[::-1]:
        text += "</{}>".format(t)
    for t in closed_tags[::-1]:
        text = "<{}>".format(t) + text

    return text


def htmlizer(text, link: Link):
    """
    Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
    раши на брейшис или шмойс
    :param text: str
    :param link: Link
    :return: str
    """



    # заменяем <ramo> на <div class='ramo'>
    for to_replace, closing_tag, tag in re.findall(r'(<(/?)([^/>]+)>)',text):
        text = text.replace(to_replace,"<div class='{}'>".format(tag) if not closing_tag else "</div>")

    text = text.replace('\n', '<p>')
    # обрабатываем "короткие" ссылки {{taz/1}} на ссылки /api/text/taz/taz_al_yore_dea/siman=92&siman_katan=1/
    for to_replace, author_kitzur_name, siman_katan in re.findall('({0}{0}([^/]+)/([^{0}]+){0}{0})'.format(delimiters),text):
        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
        # author_full_name = author_kitzur[author_kitzur_name]
        author_name = AuthorName(author_kitzur_name)
        # [('{{taz/1}}', 'taz', '1')]
        author = get_author(author_name.full_name)


        # author.set_link_to_parent(link)
        # author.siman_katan = siman_katan

        text = text.replace(to_replace,
                            """
<sup>
<span class="ajax-block">
    <a href="#!" class="js-ajax-link" data-ajax-url="{url}">
        {name}-{siman_katan}
    </a>
</span>
</sup>
                        """.format(url = reverse('text_api_request', args = [author_name.full_name,
                                                                             "{}_al_{}".format(author_name.short_name,link.book.full_name),
                                                                             link.chapter_name,
                                                                             "siman_katan={}".format(siman_katan)]),
                                                  name = author_name.short_name, siman_katan= siman_katan))

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
        link = Link()
        link.set_author_name(AuthorName(author_kitzur_name))
        link.set_book(Book(book, AuthorName(author_kitzur_name)))
        link.set_params(params)
        url = reverse('text_api_request', args = (author_kitzur_name, book, link.chapter_name, params))
        text = text.replace(to_replace,
                            '<span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{name}</a></span>'.format(
                                **{'url': url, 'name': link_text}))
    # **текст** как термины
    for term in re.findall('\*\*(.+?)\*\*',text):
        term_definition = s.get_term(term)
        text = text.replace("**{}**".format(term), '<span title="{1}" class="term">{0}</span>'.format(term, term_definition))
    # ??текст?? как то, что надо доработать
    for subtext in re.findall('\?\?(.+?)\?\?',text):
        text = text.replace("??{}??".format(subtext), '<span title="Требуется вставить ссылку/доработать" class="need_work">{}</span>'.format(
            subtext))
    print(text)
    return text

def demarking(text, link):
    """
    Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
    раши на брейшис или шмойс
    :param text: str
    :param link: Link
    :return: str
    """
    delimiters = '%'
    text = text.replace('\n','<p>')
    # убираем все <ramo>
    for to_replace in re.findall(r'(</?[^/>]+>)',text):
        text = text.replace(to_replace,"")

    # удаляем "короткие" ссылки {{taz/1}}
    for to_replace in re.findall('({0}{0}[^/]+/[^{0}]+{0}{0})'.format(delimiters),text):
        text = text.replace(to_replace,'')

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
        # url = reverse('text_api_request', args = (author_kitzur_name, book, params))
        text = text.replace(to_replace, link_text)
    # **текст** как термины
    for term in re.findall('\*\*(.+?)\*\*',text):
        text = text.replace("**{}**".format(term), '{0}'.format(term))
    # ??текст?? как то, что надо доработать
    for subtext in re.findall('\?\?(.+?)\?\?',text):
        text = text.replace("??{}??".format(subtext), '{}'.format(
            subtext))
    return text





def open_text(request, author, book, chapter_name, params):
    print(params)
    author_name = AuthorName(author)
    book = Book(book, author_name)
    # book_TOC: Content = s.get_book_TOC(book)
    book_TOC = s.get_book_TOC(book) # type:  Content

    link = Link()
    link.set_author_name(author_name)
    link.set_book(book)
    link.set_chapter_name(chapter_name)
    link.set_params(params)
    # parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = s.get_text_by_link(link)
    context = dict()
    context['title'] = '{}:{}'.format(author,book)
    context['header'] = "{}:{}".format(link.chapter_name, link.get_subchapter().name)
    # for openGraph
    context['description'] = "{}...".format(demarking(text,link)[:200])
    context['title'] = "{}: {}".format(link.author_name.full_name, context.get('header',''))
    # TODO время публикации и урл для опенграф
    context['pulished_time'] = "{}".format("GET pulished_time")
    context['url'] = "{}".format("GET URL")

    html = htmlizer(text, link)
    context['text'] = html
    book_TOC.set_current_place(link)
    context['up'] = reverse('book', kwargs={'author': link.author_name.full_name,
                                            'book': link.book.full_name})
    context['prev'] = book_TOC.prev_subchapter_link()
    context['next'] = book_TOC.next_subchapter_link()
    return render(request, 'texts/open.html', context)


def get_quote(author, book, params, refferer):
    print(params)
    author_name = AuthorName(author)
    book = Book(book, author_name)

    link = Link()
    link.set_author_name(author_name)
    link.set_book(book)
    link.set_params(params)

    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = s.get_text_by_link(link)
    quote = re.findall('\[\[refferer={0}]](.*)\[\[/refferer={0}]]'.format(refferer),text, re.M+re.DOTALL)
    if quote:
        quote = close_unclosed_tags(quote[0])
        html = htmlizer(quote, link)
        return html
    return "NOT FOUND"


def api_request(request, author, book, chapter_name, params):
    print('api')
    print(params)

    author_name = AuthorName(author)
    book = Book(book, author_name)
    link = Link()
    link.set_author_name(author_name)
    link.set_book(book)
    link.set_chapter_name(chapter_name)
    link.set_params(params)

    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = s.get_text_by_link(link)
    html = htmlizer(text, link)
    author = get_author(author)
    return JsonResponse({'title': '{}:{}:{}'.format(author_name.short_name, book.short_name, link.short_str()), 'content': html, 'cardColor':
        author.css_class_name})


def index(request):
    authors = s.get_authors()
    # authors = get_authors()
    return render(request, 'texts/index.html', {
        'authors':authors, 'title': "Список авторов"
    })


def author(request, author):
    author = AuthorName(author)
    books = s.get_books_for_author(author)
    info = s.get_author_info(author)
    return render(request, 'texts/author.html', {
        'books':books, 'author': author, 'title': "Список книг для {}".format(author), 'info':info,
    })


def book(request, author, book):
    author = AuthorName(author)
    book = Book(book, author)
    info = s.get_book_info(book)
    content = s.get_book_TOC(book)
    return render(request, 'texts/book.html', {
        'content':content, 'author': author, 'book': book, 'title': "Содержание книги {} от {}".format(book, author), 'info':info,
    })

def terms_to_define(request):
    result = []
    for root, dir, files in os.walk(r"F:\Yandex\Sites\jewTeX\TEXTS_DB"):
        # print(root)
        if not '.git' in root:
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding = 'utf8') as fin:
                    text = fin.read()
                    for term in re.findall('\*\*(.+?)\*\*', text):
                        term_definition = s.get_term(term)
                        if term_definition == 'DEFINITION NOT FOUND':
                            result.append([filepath, term, term_definition])
                        else:
                            print(term_definition)

    for k in result:
        print(k)

    terms = {i[1] for i in result}

    return render(request, 'texts/terms_to_define.html', {
        'terms':terms, 'title': "Термины без определения"
    })

def need_to_be_done(request):
    result = []
    for root, dir, files in os.walk(r"F:\Yandex\Sites\jewTeX\TEXTS_DB"):
        # print(root)
        if not '.git' in root:
            # for items in fnmatch.filter(files, "*"):
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding = 'utf8') as fin:
                    text = fin.read()
                    for subtext in re.findall('\?\?(.+?)\?\?', text):
                        result.append([filepath, subtext])
                        # result.append([filepath.replace(s.texts_path,'').split(os.path.sep)[1:], subtext])

    # for k in result:
    #     print(k)
    return render(request, 'texts/need_to_be_done.html', {
        'result':result, 'title': "Надо доделать"
    })

def not_translated(request):
    from urllib.request import urlopen
    result = []
    for root, dir, files in os.walk(r"F:\Yandex\Sites\jewTeX\TEXTS_DB"):
        # print(root)
        if not '.git' in root:
            # for items in fnmatch.filter(files, "*"):
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath, 'r', encoding = 'utf8') as fin:
                    text = fin.read()
                    # вставляем отрывки из других текстов
                    # %%maran:sha2:siman=106&seif=1%refferer%%
                    for to_replace, author_kitzur_name, book, params, refferer in re.findall(
                            '({0}{0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}([a-z_0-9]+){0}{0})'.format(
                                delimiters), text):
                        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
                        quote = get_quote(author_kitzur_name, book, params, refferer)
                        if quote == "NOT FOUND":
                            result.append([filepath, (author_kitzur_name, book, params, refferer)])

                    # обрабатываем "длинные" ссылки (как в url)
                    # %%в начале главы 106%maran:sha2:siman=106&seif=1%%
                    for to_replace, link_text, author_kitzur_name, book, params in re.findall(
                            '({0}{0}([^{0}]+){0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}{0})'.format(
                                delimiters), text):
                        # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
                        link = Link()
                        link.set_author_name(AuthorName(author_kitzur_name))
                        link.set_book(Book(book, AuthorName(author_kitzur_name)))
                        link.set_params(params)
                        url = reverse('text_api_request', args = (author_kitzur_name, book, link.chapter_name, params))
                        a = urlopen("http://127.0.0.1:8000{}".format(url))
                        if "TEXT NOT FOUND" in a.read().decode('utf8'):
                            result.append([filepath, url])

    # for k in result:
    #     print(k)
    return render(request, 'texts/need_to_be_done.html', {
        'result':result, 'title': "Надо перевести"
    })
