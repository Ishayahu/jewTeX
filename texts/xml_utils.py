# -*- coding: utf-8 -*-
from lxml import etree


def copy_element(element):
    new_element = etree.Element(element.tag)
    for k in element.attrib.keys():
        new_element.attrib[k] = element.attrib[k]
    new_element.text = element.text
    new_element.tail = element.tail
    return new_element

def compare_elements(e,o):
    e_keys_for_iteration = set(e.attrib.keys())
    e_keys = set(e.attrib.keys())
    o_keys = set(o.attrib.keys())
    # print (e_keys, o_keys)
    # exit()
    for e_k in e_keys_for_iteration:
        if e_k not in o.attrib:
            return False
        if e.attrib[e_k] != o.attrib[e_k]:
            return False
        else:
            e_keys.remove(e_k)
            o_keys.remove(e_k)
    o_keys_for_iteration = o_keys.copy()
    for o_k in o_keys_for_iteration:
        if o_k not in e.attrib:
            return False
        if e.attrib[o_k] != o.attrib[o_k]:
            return False
        else:
            e_keys.remove(o_k)
            o_keys.remove(o_k)
    if e_keys or o_keys:
        return False
    return True

def merge_two_elements(e,o):
    for c in o.getchildren():
        e.append(c)

def copy_wihtout_pages(root):
    # if root.tag == 'page':

    new_root = copy_element(root)

    for c in root.getchildren():
        if c.tag in ('page','daf'):
            for gc in c.getchildren():
                new_gc = copy_wihtout_pages(gc)
                if new_gc.tag == 'header' and len(new_root):
                    # print(new_root[-1].attrib, new_gc.attrib, compare_elements(new_root[-1], new_gc))
                    if compare_elements(new_root[-1], new_gc):
                        merge_two_elements(new_root[-1], new_gc)
                        continue
                new_root.append(new_gc)
        else:
            new_c = copy_wihtout_pages(c)
            if new_c.tag == 'header' and len(new_root):
                # print(new_root[-1].attrib, new_c.attrib, compare_elements(new_root[-1], new_c))
                if compare_elements(new_root[-1], new_c):
                    merge_two_elements(new_root[-1], new_c)
                    continue

            new_root.append(new_c)
    return new_root

def remove_girsaot(root_or_dom):
    if type(root_or_dom) == type(etree._ElementTree()):
        root = root_or_dom.getroot()
    else:
        root = root_or_dom
    # for girsa in root.findall(f".//header[@type='girsa']"):
    #     if girsa.attrib['name'] != 'main':
    #         root.remove(girsa)
    for c in root.getchildren():
        if c.tag == 'header' and c.attrib['type'] == 'girsa' and c.attrib['name'] != 'main':
            root.remove(c)
        else:
            remove_girsaot(c)
