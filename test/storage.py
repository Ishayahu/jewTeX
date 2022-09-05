import os
from texts.storage import *
TEXTS_DB_PATH = os.path.join(os.getcwd(),'..', 'TEXTS_DB')
s2 = Storagev2(
    storageType=FileStorage(TEXTS_DB_PATH),
    storageFormat=XMLFormat()
)
author_name = AuthorName('joseph_isaac_schneersohn', s2)
book = Book('sefer_hamaamarim_5682', author_name, s2)
link = Link()
link.set_author_name(author_name)
link.set_book(book)
link.set_params('dibur_amathil=Песнь Давида&letter=א&')

t = s2.get_text_by_link(link)
# print(len(t))
print(t)
