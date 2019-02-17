with open(r'C:\Users\ishay\YandexDisk\Sites\jewTeX\TEXTS_DB\yosef_karo\shulkhan_arukh_yore_dea\92.txt', 'r',
          encoding='utf8') as f:
    ft = f.read()
# with open(r'C:\Users\ishay\YandexDisk\Sites\jewTeX\TEXTS_DB\yakov_ben_osher\tur\89.txt', 'r',
#           encoding='utf8') as f:
#     ft2 = f.read()


# ft == ft2
import re

# pattern = '.*\[\[seif=4]].*?(.*?)\[\[.*'
pattern = '({{([^/]+)/(.+)}})'

# re.findall(pattern, ft2, re.DOTALL)
re.findall(pattern, ft, re.DOTALL)