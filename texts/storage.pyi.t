class Storage:
    get_authors = None # type:
    get_books_for_author = None # type: Callable

class Author:
    full_name = None
    short_name = None
    author_kitzur = None # type: dict
    author2kitzur = None # type: dict

class Book:
    name = None # type: str