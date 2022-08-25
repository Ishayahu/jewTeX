from django.shortcuts import render
from django.http import HttpResponse
import os
import re
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
# import texts.authors
# from texts.authors import normalize_author, normalize_book
# import cyrtranslit
from texts.storage import Link, Content
from texts.storage import Storage
from texts.biblio import AuthorName, Book
from django.utils.translation import get_language_from_request

# TODO почистить старый код

s = Storage(os.path.join(os.getcwd(), 'TEXTS_DB'))

def process_text(text, xslt_path):
    # преобразуем xml в нужный формат
    # print(text)
    from lxml.etree import XMLSyntaxError
    try:
        text = s.htmlizer(text, xslt_path)
    except XMLSyntaxError as e:
        print(e)
        return text
    # print(text)

    # вставляем цитаты
    quote_xslt_path = xslt_path.split(os.path.sep)
    # print(os.path.sep)
    # print(quote_xslt_path)
    if not quote_xslt_path[-1].startswith('quote'):
        quote_xslt_path[-1] = f'quote_{quote_xslt_path[-1]}'
    quote_xslt_path = os.path.sep.join(quote_xslt_path)
    quote_xslt_path = s.get_libraty_meta_filepath(quote_xslt_path)


    # print(quote_xslt_path)
    for quote_link, quote_tag in s.get_quotes(text):
        quote_text = s.get_text_by_link(quote_link)
        # print(quote_tag, quote_text)
        # print(s.htmlizer(quote_text, quote_xslt_path))
        try:
            quote_text = process_text(quote_text, quote_xslt_path)
            # quote_text = s.htmlizer(quote_text, quote_xslt_path)
        except XMLSyntaxError as e:
            print(e)
        text = text.replace(quote_tag, f'"{quote_text}"')
    # вставляем ссылки
    for link, link_text, link_tag in s.get_links(text):
        import re
        # print("*"*50)
        # print(link_tag, link_text)
        # print(link_tag)
        url = reverse('text_api_request', args = (link.author_name.storage_id,
                                                  link.book.storage_id,
                                                  link.get_params()))
        # print(url)
        replace_link_to = f'<span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{link_text}</a></span>'
        if link.upper:
            replace_link_to = '<sup>'+replace_link_to+'</sup>'
        # print('->', replace_link_to)
        # text = text.replace(link_tag, replace_link_to)
        text = re.sub(rf"<link[^<]*>{link_text}</link>", replace_link_to, text)


    # print(text[-300:])
    return text


from django.http import JsonResponse

TEXTS_PATH = os.path.join(os.getcwd(),'TEXTS_DB')


def close_unclosed_tags(text):
    temp_text = text
    opened_tags = []
    closed_tags = []
    r = re.search(r'(</?([^>]+)>)', temp_text)
    while r:
        # print(r.groups())
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
    # print(opened_tags)
    # добавляем в текст незакрытые теги в конце
    for t in opened_tags[::-1]:
        text += "</{}>".format(t)
    for t in closed_tags[::-1]:
        text = "<{}>".format(t) + text

    return text


# def htmlizer_old(text, link: Link):
#     """
#     Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
#     раши на брейшис или шмойс
#     :param text: str
#     :param link: Link
#     :return: str
#     """
#
#
#
#     # заменяем <ramo> на <div class='ramo'>
#     for to_replace, closing_tag, tag in re.findall(r'(<(/?)([^/>]+)>)',text):
#         text = text.replace(to_replace,"<div class='{}'>".format(tag) if not closing_tag else "</div>")
#
#     text = text.replace('\n', '<p>')
#     # обрабатываем "короткие" ссылки {{taz/1}} на ссылки /api/text/taz/taz_al_yore_dea/siman=92&siman_katan=1/
#     for to_replace, author_kitzur_name, siman_katan in re.findall('({0}{0}([^/]+)/([^{0}]+){0}{0})'.format(delimiters),text):
#         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#         # author_full_name = author_kitzur[author_kitzur_name]
#         author_name = AuthorName(author_kitzur_name)
#         # [('{{taz/1}}', 'taz', '1')]
#         author = get_author(author_name.full_name)
#
#
#         # author.set_link_to_parent(link)
#         # author.siman_katan = siman_katan
#
#         text = text.replace(to_replace,
#                             """
# <sup>
# <span class="ajax-block">
#     <a href="#!" class="js-ajax-link" data-ajax-url="{url}">
#         {name}-{siman_katan}
#     </a>
# </span>
# </sup>
#                         """.format(url = reverse('text_api_request', args = [author_name.full_name,
#                                                                              "{}_al_{}".format(author_name.short_name,link.book.full_name),
#                                                                              link.chapter_name,
#                                                                              "siman_katan={}".format(siman_katan)]),
#                                                   name = author_name.short_name, siman_katan= siman_katan))
#
#     # в случае если delimiters = '%'
#     # автор/книга могут содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
#     # название параметра может содержать только английские буквы в нижнем регистре и нижнее подчёркивание
#     # значение параметра может быть любым, но без % и &
#     # название ссылки может содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
#     # (%%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%([a-z_0-9]+)%%)
#     # длинные ссылки
#     # в качестве текста может быть всё, кроме ||
#     # всё дальше - как выше для цитаты
#     # (%%([^%]+)%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%%)
#
#     # для теста можно использовать этот текст:
#     # пишет, что %%maran:sha2:siman=106&seif=1%sha2_shah_92_11%%. А РАМО
#     # дальше %%в начале главы 109%maran:sha2:siman=109&seif=1%%" [Другими словами
#
#     # убираем разметку, которая нам тут не нужна
#     for markdown in re.findall(r'\[\[[^]]+]]',text,re.M):
#         text = text.replace(markdown, '')
#     # убираем [[refferer=sha2_shah_92_11]] и [[/refferer=sha2_shah_92_11]]
#     # for to_replace in re.findall('\[\[/?refferer=[a-z_0-9]+]]',text):
#     #     text = text.replace(to_replace, '')
#
#     # вставляем отрывки из других текстов
#     # %%maran:sha2:siman=106&seif=1%refferer%%
#     for to_replace, author_kitzur_name, book, params, refferer in re.findall(
#             '({0}{0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}([a-z_0-9]+){0}{0})'.format(
#                 delimiters),text):
#         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#         quote = get_quote(author_kitzur_name, book, params, refferer)
#         text = text.replace(to_replace, '"{}"'.format(quote))
#
#     # обрабатываем "длинные" ссылки (как в url)
#     # %%в начале главы 106%maran:sha2:siman=106&seif=1%%
#     for to_replace, link_text, author_kitzur_name, book, params in re.findall(
#             '({0}{0}([^{0}]+){0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}{0})'.format(
#                 delimiters),text):
#         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#         link = Link()
#         link.set_author_name(AuthorName(author_kitzur_name))
#         link.set_book(Book(book, AuthorName(author_kitzur_name)))
#         link.set_params(params)
#         url = reverse('text_api_request', args = (author_kitzur_name, book, link.chapter_name, link.get_params()))
#         # url = reverse('text_api_request', args = (author_kitzur_name, book, link.chapter_name, params))
#         text = text.replace(to_replace,
#                             '<span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{name}</a></span>'.format(
#                                 **{'url': url, 'name': link_text}))
#     # **текст** как термины
#     for term in re.findall('\*\*(.+?)\*\*',text):
#         term_definition = s.get_term(term)
#         text = text.replace("**{}**".format(term), '<span title="{1}" class="term">{0}</span>'.format(term, term_definition))
#     # ??текст?? как то, что надо доработать
#     for subtext in re.findall('\?\?(.+?)\?\?',text):
#         text = text.replace("??{}??".format(subtext), '<span title="Требуется вставить ссылку/доработать" class="need_work">{}</span>'.format(
#             subtext))
#     # print(text)
#     return text

# def demarking(text, link):
#     """
#     Делаем из текста html. link - ссылка на запрос основной страницы, чтобы из контекста понять, какой комментарий нам нужен, например,
#     раши на брейшис или шмойс
#     :param text: str
#     :param link: Link
#     :return: str
#     """
#     delimiters = '%'
#     text = text.replace('\n','<p>')
#     # убираем все <ramo>
#     for to_replace in re.findall(r'(</?[^/>]+>)',text):
#         text = text.replace(to_replace,"")
#
#     # удаляем "короткие" ссылки {{taz/1}}
#     for to_replace in re.findall('({0}{0}[^/]+/[^{0}]+{0}{0})'.format(delimiters),text):
#         text = text.replace(to_replace,'')
#
#     # в случае если delimiters = '%'
#     # автор/книга могут содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
#     # название параметра может содержать только английские буквы в нижнем регистре и нижнее подчёркивание
#     # значение параметра может быть любым, но без % и &
#     # название ссылки может содержать только английские буквы в нижнем регистре, цифры и нижнее подчёркивание
#     # (%%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%([a-z_0-9]+)%%)
#     # длинные ссылки
#     # в качестве текста может быть всё, кроме ||
#     # всё дальше - как выше для цитаты
#     # (%%([^%]+)%([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^%&]+&?)+)%%)
#
#     # для теста можно использовать этот текст:
#     # пишет, что %%maran:sha2:siman=106&seif=1%sha2_shah_92_11%%. А РАМО
#     # дальше %%в начале главы 109%maran:sha2:siman=109&seif=1%%" [Другими словами
#
#     # убираем разметку, которая нам тут не нужна
#     for markdown in re.findall(r'\[\[[^]]+]]',text,re.M):
#         text = text.replace(markdown, '')
#     # убираем [[refferer=sha2_shah_92_11]] и [[/refferer=sha2_shah_92_11]]
#     # for to_replace in re.findall('\[\[/?refferer=[a-z_0-9]+]]',text):
#     #     text = text.replace(to_replace, '')
#
#     # вставляем отрывки из других текстов
#     # %%maran:sha2:siman=106&seif=1%refferer%%
#     for to_replace, author_kitzur_name, book, params, refferer in re.findall(
#             '({0}{0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}([a-z_0-9]+){0}{0})'.format(
#             delimiters),text):
#         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#         quote = get_quote(author_kitzur_name, book, params, refferer)
#         text = text.replace(to_replace, '"{}"'.format(quote))
#
#     # обрабатываем "длинные" ссылки (как в url)
#     # %%в начале главы 106%maran:sha2:siman=106&seif=1%%
#     for to_replace, link_text, author_kitzur_name, book, params in re.findall(
#             '({0}{0}([^{0}]+){0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}{0})'.format(
#             delimiters),text):
#         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#         # url = reverse('text_api_request', args = (author_kitzur_name, book, params))
#         text = text.replace(to_replace, link_text)
#     # **текст** как термины
#     for term in re.findall('\*\*(.+?)\*\*',text):
#         text = text.replace("**{}**".format(term), '{0}'.format(term))
#     # ??текст?? как то, что надо доработать
#     for subtext in re.findall('\?\?(.+?)\?\?',text):
#         text = text.replace("??{}??".format(subtext), '{}'.format(
#             subtext))
#     return text





# def open_text_old(request, author, book, chapter_name, params):
#     # print(params)
#     author_name = AuthorName(author)
#     book = Book(book, author_name)
#     # book_TOC: Content = s.get_book_TOC(book)
#     book_TOC = s.get_book_TOC(book) # type:  Content
#
#     link = Link()
#     link.set_author_name(author_name)
#     link.set_book(book)
#     link.set_chapter_name(chapter_name)
#     link.set_params(params)
#     # parser(link, author, book, params)
#     if not link.validate():
#         return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
#             author, book, params, link, link.errors))
#
#     text = s.get_text_by_link(link)
#     context = dict()
#     context['title'] = '{}:{}'.format(author,book)
#     context['header'] = "{}:{}".format(link.chapter_name, link.get_subchapter().name)
#     # for openGraph
#     context['description'] = "{}...".format(demarking(text,link)[:200])
#     context['title'] = "{}: {}".format(link.author_name.full_name, context.get('header',''))
#     # TODO время публикации и урл для опенграф
#     context['pulished_time'] = "{}".format("GET pulished_time")
#     context['url'] = "{}".format("GET URL")
#
#     html = htmlizer(text, link)
#     context['text'] = html
#     book_TOC.set_current_place(link)
#     context['up'] = reverse('book', kwargs={'author': link.author_name.full_name,
#                                             'book': link.book.full_name})
#     context['prev'] = book_TOC.prev_subchapter_link()
#     context['next'] = book_TOC.next_subchapter_link()
#     return render(request, 'texts/open.html', context)

def demarking(text, xslt_path):
    # print("DEMARKING")
    # print(text)
    # преобразуем xml в нужный формат
    # print(text)
    from lxml.etree import XMLSyntaxError
    try:
        text = s.htmlizer(text, xslt_path)
    except XMLSyntaxError as e:
        print(e)
        return text
    # print(text)

    # вставляем цитаты
    quote_xslt_path = xslt_path.split(os.path.sep)
    # print(os.path.sep)
    # print(quote_xslt_path)
    if not quote_xslt_path[-1].startswith('quote'):
        quote_xslt_path[-1] = f'quote_{quote_xslt_path[-1]}'
    quote_xslt_path = os.path.sep.join(quote_xslt_path)
    quote_xslt_path = s.get_libraty_meta_filepath(quote_xslt_path)


    # print(quote_xslt_path)
    for quote_link, quote_tag in s.get_quotes(text):
        quote_text = s.get_text_by_link(quote_link)
        # print(quote_tag, quote_text)
        # print(s.htmlizer(quote_text, quote_xslt_path))
        try:
            quote_text = process_text(quote_text, quote_xslt_path)
            # quote_text = s.htmlizer(quote_text, quote_xslt_path)
        except XMLSyntaxError as e:
            print(e)
        text = text.replace(quote_tag, f'"{quote_text}"')
    # вставляем ссылки
    for link, link_text, link_tag in s.get_links(text):
        # print(link_tag, link_text)
        # url = reverse('text_api_request', args = (link.author_name.storage_id,
        #                                           link.book.storage_id,
        #                                           link.get_params()))
        #
        # replace_link_to  = f'<span class="ajax-block"><a href="#!" class="js-ajax-link" data-ajax-url="{url}">{link_text}</a></span>'
        # if link.upper:
        #     replace_link_to = '<sup>'+replace_link_to+'</sup>'
        text = text.replace(link_tag,link_text)
    # убираем обёртку, оставляем только текст
    from lxml import etree
    r = etree.fromstring(text)
    text = r.text.strip()
    # print("*"*20)
    # print(text)
    return text

def open_text(request, author, book, params):

    lang = get_language_from_request(request)
    # print(get_language_from_request(request))
    author_name = AuthorName(author, s, lang)
    book = Book(book, author_name, s, lang)
    # book_TOC: Content = s.get_book_TOC(book)
    book_TOC = s.get_book_TOC(book) # type:  Content

    link = Link()
    link.set_author_name(author_name)
    link.set_book(book)
    # link.set_chapter_name(chapter_name)
    link.set_params(params)
    # parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = s.get_text_by_link(link)
    context = dict()
    # TODO показывать локализованную информацию об авторе. Подумать , что делать если нет инфы на нужно м языке
    context['title'] = f'{author_name.full_name}: {book.full_name}: {link.str_inside_book_position()}'
    context['header'] = f'{author_name.full_name}: {book.full_name}: {link.str_inside_book_position()}'
    xslt_path = s.get_xslt_path(link.book)
    # for openGraph
    try:
        context['description'] = "{}...".format(demarking(text,s.get_xslt_path(link.book,'quote_html'))[:200])
    except AttributeError:
        print('views.397')
        print(text)
        context['description'] = ''
    # context['title'] = "{}: {}".format(link.author_name.full_name, context.get('header',''))
    # TODO время публикации и урл для опенграф
    context['pulished_time'] = "{}".format("GET pulished_time")
    context['url'] = "{}".format("GET URL")
    # print(text)

    # print(text)
    html = process_text(text, xslt_path)
    # html = text


    # print(html)
    context['text'] = html
    book_TOC.set_current_place(link)
    context['up'] = reverse('book', kwargs={'author': link.author_name.storage_id,
                                            'book': link.book.storage_id})
    if book_TOC.prev_subchapter_params():
        context['prev'] = reverse('open_from_xml', args=(link.author_name.storage_id,
                                                     link.book.storage_id,
                                                     book_TOC.prev_subchapter_params()))
    if book_TOC.next_subchapter_params():
        context['next'] = reverse('open_from_xml', args=(link.author_name.storage_id,
                                                     link.book.storage_id,
                                                     book_TOC.next_subchapter_params()))
    return render(request, 'texts/open.html', context)


# def get_quote(author, book, params, refferer):
#     # print(params)
#     author_name = AuthorName(author, s)
#     book = Book(book, author_name, s)
#
#     link = Link()
#     link.set_author_name(author_name)
#     link.set_book(book)
#     link.set_params(params)
#
#     if not link.validate():
#         return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
#             author, book, params, link, link.errors))
#
#     text = s.get_text_by_link(link)
#     quote = re.findall('\[\[refferer={0}]](.*)\[\[/refferer={0}]]'.format(refferer),text, re.M+re.DOTALL)
#     if quote:
#         quote = close_unclosed_tags(quote[0])
#         html = htmlizer(quote, link)
#         return html
#     return "NOT FOUND"


# TODO генерировать odt документы. разобраться, почему они как с ошибкой и требуют восстановления

# def api_request_old(request, author, book, params):
#     # print('api')
#     # print(params)
#
#     author_name = AuthorName(author)
#     book = Book(book, author_name)
#     link = Link()
#     link.set_author_name(author_name)
#     link.set_book(book)
#     # link.set_chapter_name(chapter_name)
#     link.set_params(params)
#
#     if not link.validate():
#         return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
#             author, book, params, link, link.errors))
#
#     text = s.get_text_by_link(link)
#     xslt_path = s.get_xslt_path(link.book)
#
#     html = process_text(text, xslt_path)
#     html += "<p><a href='{}' target='_blank'>к книге</a></p>".format(link.get_url())
#     author = get_author(author)
#     return JsonResponse({'title': '{}:{}:{}'.format(author_name.short_name, book.short_name, link.short_str()), 'content': html, 'cardColor':
#         author.css_class_name})
def api_request(request, author, book, params):
    # print('api')
    # print(params)

    author_name = AuthorName(author, s)
    book = Book(book, author_name, s)
    link = Link()
    link.set_author_name(author_name)
    link.set_book(book)
    # link.set_chapter_name(chapter_name)
    link.set_params(params)

    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))
    # print(link)
    text = s.get_text_by_link(link)
    xslt_path = s.get_xslt_path(link.book)
    # print("-"*50)
    # print(text)
    # print("-"*50)
    html = process_text(text, xslt_path)
    html += "<p><a href='{}' target='_blank'>к книге</a></p>".format(link.get_url())
    # author = get_author(author)

    lang = get_language_from_request(request)
    title = '{} {}. {}: {}'.format(
        author_name.info[lang]['first_name']['value'],
        author_name.info[lang]['last_name']['value'],
        book.info[lang]['full_name']['value'],
        link.str_inside_book_position())

    return JsonResponse({'title': title, 'content': html, 'cardColor':
        author_name.info['display']['css_class_name']['value']})


def index(request):

    language_code = get_language_from_request(request)
    authors = s.get_authors(language_code)

    # authors = get_authors()
    return render(request, 'texts/index.html', {
        'authors':authors, 'title': "Список авторов"
    })


def author(request, author):
    language_code = get_language_from_request(request)
    author = AuthorName(author, s, language_code)
    books = s.get_books_for_author(author)
    info = s.get_author_info(author)
    return render(request, 'texts/author.html', {
        'books':books, 'author': author, 'title': "Список книг для {}".format(author), 'info':info,
    })


def book(request, author, book):
    from django.template.loader import render_to_string
    import uuid
    language_code = get_language_from_request(request)
    author = AuthorName(author, s, language_code)
    book = Book(book, author, s, language_code)
    info = book.info['about']['value']
    content = s.get_book_TOC(book)
    def make_html_TOC(elements):
        def makeuuid(element):
            result = uuid.uuid4()
            return result.hex
        if elements:
            rendered = ''
            for element in elements:
                rendered += render_to_string('texts/html_toc.html', {'element': element, 'element_id': makeuuid(element), 'author': author, 'book': book})
                rendered += make_html_TOC(element.children)
                if element.children:
                    rendered += '</ol>'
            return rendered
        else:
            return ''

    html_toc = make_html_TOC(content.items)

    # print(content.items)
    lang = get_language_from_request(request)
    title = "Содержание книги {} от {} {}".format(book.info[lang]['full_name']['value'],
                                                  author.info[lang]['first_name']['value'],
                                                  author.info[lang]['last_name']['value'])
    return render(request, 'texts/book.html', {
        'content':content,'html_toc':html_toc, 'author': author, 'book': book, 'title': title, 'info':info,
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
                            pass
                            # print(term_definition)

    # for k in result:
        # print(k)

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
    raise NotImplementedError()
# def not_translated(request):
#     from urllib.request import urlopen
#     result = []
#     for root, dir, files in os.walk(r"F:\Yandex\Sites\jewTeX\TEXTS_DB"):
#         # print(root)
#         if not '.git' in root:
#             # for items in fnmatch.filter(files, "*"):
#             for items in files:
#                 filepath = os.path.join(root, items)
#                 with open(filepath, 'r', encoding = 'utf8') as fin:
#                     text = fin.read()
#                     # вставляем отрывки из других текстов
#                     # %%maran:sha2:siman=106&seif=1%refferer%%
#                     for to_replace, author_kitzur_name, book, params, refferer in re.findall(
#                             '({0}{0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}([a-z_0-9]+){0}{0})'.format(
#                                 delimiters), text):
#                         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#                         quote = get_quote(author_kitzur_name, book, params, refferer)
#                         if quote == "NOT FOUND":
#                             result.append([filepath, (author_kitzur_name, book, params, refferer)])
#
#                     # обрабатываем "длинные" ссылки (как в url)
#                     # %%в начале главы 106%maran:sha2:siman=106&seif=1%%
#                     for to_replace, link_text, author_kitzur_name, book, params in re.findall(
#                             '({0}{0}([^{0}]+){0}([a-z0-9_]+):([a-z0-9_]+):((?:[a-z_]+=[^{0}&]+&?)+){0}{0})'.format(
#                                 delimiters), text):
#                         # получаем полное имя комментатора. Потом по нему мы выберем нужный класс комментатора
#                         link = Link()
#                         link.set_author_name(AuthorName(author_kitzur_name))
#                         link.set_book(Book(book, AuthorName(author_kitzur_name)))
#                         link.set_params(params)
#                         url = reverse('text_api_request', args = (author_kitzur_name, book, link.chapter_name, params))
#                         a = urlopen("http://127.0.0.1:8000{}".format(url))
#                         if "TEXT NOT FOUND" in a.read().decode('utf8'):
#                             result.append([filepath, url])
#
#     # for k in result:
#     #     print(k)
#     return render(request, 'texts/need_to_be_done.html', {
#         'result':result, 'title': "Надо перевести"
#     })

def search(request):
    if request.method!='POST':
        raise ImportError()
    a = request.POST
    search_string = request.POST.get('search_string','')
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
                    with open(file,'r',encoding='utf8') as f:
                        content = f.read()
                    if content:
                        root = etree.XML(content)
                        # TODO: везде ли у меня всё в p?
                        for e in find(root):
                            found.append((file,e))

    my_path = Path(s.texts_path)
    check_out_path(my_path)
    result = []
    class Link:
        def __init__(self):
            self.author = None
            self.book = None
            self.link = None
            self.text = None
    for file,e in found:
        author = file.parts[-3]
        book = file.parts[-2]
        l = Link()
        l.author = author
        l.book = book
        l.text = e.text

        tmp = []
        while e.tag !='content':
            if e.tag == 'header':
                tmp.append((e.attrib['type'], e.attrib['name']))
            e = e.getparent()
        tmp.reverse()
        ll = ''
        for k,v in tmp:
            ll+=f"{k}={v}&"
        ll = ll[:-1]
        l.link = ll
        result.append(l)

    return render(request, 'texts/found.html', {
        'found':result, 'title': "Найдено"
    })
