from django.test import SimpleTestCase

from texts.storage import XMLFormat


class BookTOCSortTests(SimpleTestCase):
    def test_numeric_and_textual_siman_names_can_coexist(self):
        chronological = """<content>
            <header level="0" type="siman" name="3905" />
            <header level="0" type="siman" name="3900" />
            <header level="0" type="siman" name="3909 или 3915" />
        </content>"""
        biographies = """<content>
            <header level="0" type="siman"
                name="Таннаим и амораим — рабби Йеуда а-Наси" />
        </content>"""
        toc = XMLFormat().build_book_TOC([chronological, biographies])
        self.assertEqual(
            [item.name for item in toc.items],
            ["3900", "3905", "3909 или 3915",
             "Таннаим и амораим — рабби Йеуда а-Наси"],
        )

    def test_explicit_number_controls_sort_without_changing_link_name(self):
        xml = """<content>
            <header level="0" type="siman" name="3905"/>
            <header level="0" type="siman" name="Антонинус"
                number="3901"/>
            <header level="0" type="siman" name="Введение"/>
            <header level="0" type="siman" name="3900"/>
        </content>"""
        toc = XMLFormat().build_book_TOC([xml])
        self.assertEqual(
            [item.name for item in toc.items],
            ["3900", "Антонинус", "3905", "Введение"],
        )
        self.assertEqual(toc.items[1].get_link_params(), "siman=Антонинус")
