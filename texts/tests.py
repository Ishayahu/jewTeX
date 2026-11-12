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

class DafAddressingTests(SimpleTestCase):
    """Regression: daf leaves are also addressable with a chapter qualifier."""

    XML = """<content>
        <header level="0" type="chapter" name="5">
            <daf number="445" name="44b"><p>Лист 44б</p></daf>
            <daf number="450" name="45a"><p>Лист 45а</p></daf>
        </header>
    </content>"""

    def test_daf_only_still_selects_leaf(self):
        from texts.storage import Link
        link = Link()
        link.set_params("daf=44b")
        root = XMLFormat.select_text([self.XML], link)
        self.assertEqual(root.xpath("string(p)"), "Лист 44б")

    def test_chapter_and_daf_selects_same_leaf(self):
        from texts.storage import Link
        link = Link()
        link.set_params("chapter=5&daf=44b")
        root = XMLFormat.select_text([self.XML], link)
        self.assertEqual(root.xpath("string(p)"), "Лист 44б")

    def test_wrong_chapter_cannot_select_leaf(self):
        from texts.storage import Link
        link = Link()
        link.set_params("chapter=6&daf=44b")
        root = XMLFormat.select_text([self.XML], link)
        self.assertEqual(len(root), 0)

    def test_chapter_qualified_daf_navigates_with_short_toc_key(self):
        from texts.storage import Link
        toc = XMLFormat().build_book_TOC([self.XML])
        link = Link()
        link.set_params("chapter=5&daf=44b")
        toc.set_current_place(link)
        self.assertEqual(toc.next_subchapter_params, "daf=45a")

    def test_daf_only_toc_navigation_remains_unchanged(self):
        from texts.storage import Link
        toc = XMLFormat().build_book_TOC([self.XML])
        link = Link()
        link.set_params("daf=44b")
        toc.set_current_place(link)
        self.assertEqual(toc.next_subchapter_params, "daf=45a")
