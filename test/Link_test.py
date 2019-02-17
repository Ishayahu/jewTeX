# -*- coding: utf-8 -*-
from texts.views import Link
import re

with open(r'F:\TEMP\text.txt','r',encoding = 'utf8') as f:
    text = f.read()

a = Link()
a.set_page(6)
a.set_dibur_amathil('ahalya mahalya')
pattern = a.get_regexp()
re.findall(pattern,text,re.DOTALL)


a = Link()
a.set_seif(7)
a.set_referrerer('refer')
pattern = a.get_regexp()
re.findall(pattern,text,re.DOTALL)

