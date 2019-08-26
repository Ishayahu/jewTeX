import os
import fnmatch
import re
from texts.storage import Storage

s = Storage(r'F:\Yandex\Sites\jewTeX\TEXTS_DB')
result = []
for root, dir, files in os.walk(r"F:\Yandex\Sites\jewTeX\TEXTS_DB"):
        # print(root)
        if not '.git' in root:
            # for items in fnmatch.filter(files, "*"):
            for items in files:
                filepath = os.path.join(root, items)
                with open(filepath,'r',encoding = 'utf8') as fin:
                    text = fin.read()
                    for subtext in re.findall('\?\?(.+?)\?\?', text):
                        result.append([filepath, subtext])
                        # result.append([filepath.replace(s.texts_path,'').split(os.path.sep)[1:], subtext])

for k in result:
    print(k)