from django.shortcuts import render
from django.http import HttpResponse
import os
import re
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse

TEXTS_PATH = os.path.join(os.getcwd(),'TEXTS_DB')

author_kitzur = {'taz': 'david_alevi_segel'}


def parser(link, author, book, params):
    """
    Из автора (в полном или сокрыщённом виде), книги и параметров получаем запрос, по которому будем искать текст. params что-то вроде глава=4&пункт=8
    :param link: Link
    :param author: str
    :param book: str
    :param params: str
    """
    if author in author_kitzur:
        author = author_kitzur[author]
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
        self.seif = None
        self.page = None
        self.dibur_amathil = None
        self.siman_katan = None
        #TODO надо сделать API для получения id referrer'a
        self.referrerer = None
        self.errors = []

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

    def set_chapter(self, v):
        self.chapter = v

    def set_seif(self, v):
        self.seif = v

    def set_page(self, v):
        self.page = v

    def set_dibur_amathil(self, v):
        self.dibur_amathil = v

    def set_siman_katan(self, v):
        self.siman_katan = v

    def set_referrerer(self, v):
        self.referrerer = v

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
        return os.path.join(self.author, self.book, filename)

    def get_regexp(self):
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

        r += "(.*?)"
        if self.referrerer:
            r += r"\[\[/{}]]".format(self.referrerer)
        else:
            r += r"\[\["
        r += ".*"
        return r


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
    with open("{}.txt".format(fullpath), 'r', encoding = 'utf8') as f:
        fulltext = f.read()
    pattern = link.get_regexp()
    print(pattern)
    result = re.findall(pattern, fulltext, re.DOTALL)
    if result:
        return result[0]
    else:
        # вроде как при успешном поиске не должно такого быть
        return "TEXT NOT FOUND"

class Taz:
    def __init__(self, link_to_parent, siman_katan):
        """

        :param link_to_parent: Link
        :param siman_katan: str
        """
        self.helek = "_".join(link_to_parent.book.split("_")[-2:])
        self.siman = link_to_parent.siman
        self.siman_katan = siman_katan
    def get_href(self):
        return reverse('text_api_request', args=[author_kitzur['taz'],
                                                 'taz_al_{}'.format(self.helek),
                                                 'siman={}&siman_katan={}'.format(self.siman, self.siman_katan)])


def htmlizer(text, link):
    """
    Делаем из текста html
    :param text: str
    :param link: Link
    :return: str
    """
    text = text.replace('\n','<p>')
    # TODO заменяем ссылки {{taz_al_yore_dea/1}} на ссылки /api/text/taz/taz_al_yore_dea/siman=92&siman_katan=1/
    for g in re.findall('({{([^/]+)/(.+)}})',text):
        # [('{{taz/1}}', 'taz', '1')]
        text = text.replace(g[0],Taz(link,g[2]).get_href())
    return text


def open_text(request, author, book, params):
    link = get_link()
    parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = get_text(link)
    html = htmlizer(text, link)
    # TODO static files

    # template = loader.get_template('texts/index.html')
    # context = {
    #     'title': '{}:{}'.format(author,book),
    #     'text':html
    # }
    # return HttpResponse(template.render(context, request))
    return render(request, 'texts/index.html', {
        'title': '{}:{}'.format(author,book),
        'text':html
    })

def api_request(request, author, book, params):
    link = get_link()
    parser(link, author, book, params)
    if not link.validate():
        return HttpResponse("author = {}<p>book = {}<p>params = {}<hr />link = {}<hr />link_errors = {}".format(
            author, book, params, link, link.errors))

    text = get_text(link)
    html = htmlizer(text, link)
    # TODO static files

    # template = loader.get_template('texts/index.html')
    # context = {
    #     'title': '{}:{}'.format(author,book),
    #     'text':html
    # }
    # return HttpResponse(template.render(context, request))
    return render(request, 'texts/clean_text.html', {
        'text':html
    })