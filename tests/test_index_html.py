"""Regression tests for index.html.

These tests target exactly the markup that was touched by the PR:

  * an HTML comment inserted right after the <!DOCTYPE html> declaration
  * the <title> tag's closing bracket
  * the #hero <section> element's id/class attributes
  * the <main>/#about wrapper elements (<main id="main">,
    <section id="about" class="about">, the .container div and the
    .section-title div) that were removed

The document is parsed with the stdlib ``html.parser`` module, which
tokenizes markup the same way a browser would (it does not build a DOM
tree, but it does resolve tag/attribute boundaries the same way), so the
tests below observe the real, effective structure of the page rather than
just its raw source text.

Note: an HTML comment claiming "valid document structure" was added to
the file by this PR. Comments are not executable and cannot be trusted to
describe the actual state of the markup, so these tests verify the actual
parsed structure instead of relying on that claim.
"""

import os
import re
import unittest
from html.parser import HTMLParser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, "index.html")


class _RecordingHTMLParser(HTMLParser):
    """Records the linear stream of tags/text encountered in the document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.start_tags = []  # list of (tag, {attr: value or None})
        self.start_tag_counts = {}
        self.end_tag_counts = {}
        self.text_chunks = []  # list of (most_recent_start_tag, stripped_text)
        self._current_tag = None

    def handle_starttag(self, tag, attrs):
        self.start_tags.append((tag, dict(attrs)))
        self.start_tag_counts[tag] = self.start_tag_counts.get(tag, 0) + 1
        self._current_tag = tag

    def handle_endtag(self, tag):
        self.end_tag_counts[tag] = self.end_tag_counts.get(tag, 0) + 1

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_chunks.append((self._current_tag, stripped))

    def tags_named(self, tag_name):
        return [attrs for tag, attrs in self.start_tags if tag == tag_name]

    def has_tag_with_attrs(self, tag_name, **expected):
        for attrs in self.tags_named(tag_name):
            if all(attrs.get(key) == value for key, value in expected.items()):
                return True
        return False


class IndexHtmlStructureTests(unittest.TestCase):
    """Structural regression tests scoped to the lines changed in this PR."""

    @classmethod
    def setUpClass(cls):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as fh:
            cls.raw_html = fh.read()
        cls.parser = _RecordingHTMLParser()
        cls.parser.feed(cls.raw_html)

    # -- doctype / inserted comment -----------------------------------------

    def test_file_exists_and_is_not_empty(self):
        self.assertTrue(os.path.isfile(INDEX_HTML_PATH))
        self.assertGreater(len(self.raw_html), 0)

    def test_document_still_starts_with_doctype(self):
        self.assertTrue(self.raw_html.lstrip().startswith("<!DOCTYPE html>"))

    def test_inserted_comment_does_not_break_html_root_tag(self):
        # A comment was added between <!DOCTYPE html> and <html lang="en">.
        # Verify it doesn't disturb the following root element/attribute.
        self.assertTrue(
            self.parser.has_tag_with_attrs("html", lang="en"),
            'Expected <html lang="en"> to still parse correctly right '
            "after the newly inserted comment",
        )

    # -- <title> tag ----------------------------------------------------------

    def test_title_tag_is_properly_closed(self):
        self.assertIn(
            "</title>",
            self.raw_html,
            "The </title> end tag must be terminated with '>' "
            "(found an unterminated '</title' end tag)",
        )

    def test_title_text_content_is_unaffected(self):
        title_texts = [
            text for tag, text in self.parser.text_chunks if tag == "title"
        ]
        self.assertEqual(title_texts, ["Maike R. Silva"])

    def test_meta_description_tag_is_preserved_as_its_own_tag(self):
        # An unterminated </title end tag swallows whatever markup follows
        # it up to the next '>', which previously destroyed the following
        # <meta name="description"> tag entirely.
        self.assertTrue(
            self.parser.has_tag_with_attrs("meta", name="description"),
            '<meta name="description"> must be parsed as an independent '
            "tag, not merged into the preceding </title> end tag",
        )

    def test_meta_keywords_tag_is_still_present(self):
        self.assertTrue(self.parser.has_tag_with_attrs("meta", name="keywords"))

    # -- #hero section ----------------------------------------------------------

    def test_hero_section_has_correct_id(self):
        hero_sections = [
            attrs
            for attrs in self.parser.tags_named("section")
            if attrs.get("id") == "hero"
        ]
        self.assertEqual(
            len(hero_sections),
            1,
            'Expected exactly one <section id="hero"> element',
        )

    def test_hero_section_has_expected_class_attribute(self):
        hero_sections = [
            attrs
            for attrs in self.parser.tags_named("section")
            if attrs.get("id") == "hero"
        ]
        self.assertTrue(hero_sections, "hero section (id=hero) not found")
        self.assertEqual(
            hero_sections[0].get("class"),
            "d-flex flex-column justify-content-center",
        )

    def test_hero_section_attribute_is_not_merged_with_class(self):
        # Regression guard for the specific corruption pattern introduced by
        # this PR: `id="hero class="d-flex ...">` parses as an `id` value of
        # "hero class=" plus three bogus boolean attributes instead of a
        # separate id/class pair.
        for attrs in self.parser.tags_named("section"):
            if "d-flex" in attrs or "flex-column" in attrs:
                self.fail(
                    "Found a <section> whose id/class attributes were "
                    "merged into bogus boolean attributes: %r" % (attrs,)
                )

    def test_hero_nav_anchor_resolves_to_hero_section_id(self):
        self.assertIn('href="#hero"', self.raw_html)
        self.assertTrue(self.parser.has_tag_with_attrs("section", id="hero"))

    # -- <main> / #about wrapper --------------------------------------------

    def test_main_element_present_with_id(self):
        self.assertTrue(
            self.parser.has_tag_with_attrs("main", id="main"),
            'Expected a <main id="main"> wrapper element',
        )

    def test_main_open_and_close_tag_counts_match(self):
        self.assertEqual(
            self.parser.start_tag_counts.get("main", 0),
            self.parser.end_tag_counts.get("main", 0),
            "Mismatched <main> open/close tag counts",
        )

    def test_about_section_present_with_id_and_class(self):
        about_sections = [
            attrs
            for attrs in self.parser.tags_named("section")
            if attrs.get("id") == "about"
        ]
        self.assertEqual(
            len(about_sections),
            1,
            'Expected exactly one <section id="about"> element',
        )
        self.assertEqual(about_sections[0].get("class"), "about")

    def test_about_nav_anchor_resolves_to_about_section_id(self):
        self.assertIn('href="#about"', self.raw_html)
        self.assertTrue(self.parser.has_tag_with_attrs("section", id="about"))

    def test_about_heading_text_still_present(self):
        headings = [text for tag, text in self.parser.text_chunks if tag == "h2"]
        self.assertIn("Sobre", headings)

    # -- overall tag balance (catches the removed wrapper <div>s too) -------

    def test_section_open_close_counts_match(self):
        self.assertEqual(
            self.parser.start_tag_counts.get("section", 0),
            self.parser.end_tag_counts.get("section", 0),
            "Mismatched <section> open/close tag counts",
        )

    def test_div_open_close_counts_match(self):
        self.assertEqual(
            self.parser.start_tag_counts.get("div", 0),
            self.parser.end_tag_counts.get("div", 0),
            "Mismatched <div> open/close tag counts (e.g. missing "
            '.container/.section-title wrapper divs for #about)',
        )

    # -- all in-page nav links should resolve -------------------------------

    def test_all_in_page_nav_anchors_resolve_to_existing_element_ids(self):
        nav_match = re.search(r'<nav id="navbar".*?</nav>', self.raw_html, re.S)
        self.assertIsNotNone(nav_match, 'Could not find <nav id="navbar"> block')
        hrefs = re.findall(r'href="#([\w-]+)"', nav_match.group(0))
        self.assertTrue(hrefs, "No in-page nav anchors found")

        known_ids = {
            attrs["id"] for _, attrs in self.parser.start_tags if "id" in attrs
        }

        missing = [href for href in hrefs if href not in known_ids]
        self.assertEqual(
            missing,
            [],
            "Nav links point to ids that do not exist in the parsed "
            "document: %r" % (missing,),
        )


if __name__ == "__main__":
    unittest.main()