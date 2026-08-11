"use strict";

/**
 * Tests for index.html covering the markup introduced/modified in this PR:
 *  - New "Codebrain integration validation" comment right after the DOCTYPE.
 *  - The <title> element.
 *  - The <section id="hero"> opening tag.
 *  - Overall balance of <main>, <section> and <div> opening/closing tags,
 *    which is affected by the removal of the <main>, <section id="about">
 *    and the two wrapping <div> opening tags that used to precede the
 *    "Sobre" heading.
 *
 * Run with: node --test test/index.test.js
 */

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const INDEX_HTML_PATH = path.join(__dirname, "..", "index.html");
const html = fs.readFileSync(INDEX_HTML_PATH, "utf8");

function countMatches(content, regex) {
  const matches = content.match(regex);
  return matches ? matches.length : 0;
}

test("document head", async (t) => {
  await t.test("starts with the HTML5 DOCTYPE declaration", () => {
    assert.match(html, /^<!DOCTYPE html>/);
  });

  await t.test(
    "includes the Codebrain integration validation comment right after the DOCTYPE",
    () => {
      const lines = html.split(/\r?\n/);
      assert.equal(lines[0], "<!DOCTYPE html>");
      assert.equal(
        lines[1],
        "<!-- Codebrain integration validation: valid document structure. -->"
      );
    }
  );

  await t.test(
    "declares the html root element with the expected lang attribute",
    () => {
      assert.match(html, /<html lang="en">/);
    }
  );

  await t.test("has a single, well-formed <title> element", () => {
    const titleMatches = html.match(/<title>([^<]*)<\/title>/);
    assert.ok(
      titleMatches,
      "expected to find a properly closed <title>...</title> element"
    );
    assert.equal(titleMatches[1], "Maike R. Silva");
  });

  await t.test(
    "does not leave the <title> tag unterminated (regression)",
    () => {
      // The closing tag must be immediately followed by '>' so that the
      // parser does not swallow the following <meta> tags into the title's
      // closing tag token.
      assert.doesNotMatch(
        html,
        /<\/title\s*\n/,
        "</title> must be closed with '>' on the same line, not left dangling"
      );
    }
  );
});

test("hero section markup", async (t) => {
  await t.test(
    "defines the hero <section> with distinct, properly quoted id and class attributes",
    () => {
      assert.match(
        html,
        /<section id="hero" class="d-flex flex-column justify-content-center">/,
        'expected a well-formed <section id="hero" class="..."> opening tag'
      );
    }
  );

  await t.test(
    "does not merge the id and class attribute values (regression)",
    () => {
      // Guards against `id="hero class="..."` where the missing closing
      // quote on the id attribute merges it with the class attribute.
      assert.doesNotMatch(html, /id="hero class="/);
    }
  );

  await t.test("still renders the hero heading and social links", () => {
    assert.match(html, /<h1>Maike R\. Silva<\/h1>/);
    assert.match(html, /class="social-links"/);
    assert.match(html, /class="linkedin"/);
    assert.match(html, /class="github"/);
    assert.match(html, /class="instagram"/);
  });
});

test("document structural integrity", async (t) => {
  await t.test("has a matching number of <main> and </main> tags", () => {
    const open = countMatches(html, /<main\b[^>]*>/g);
    const close = countMatches(html, /<\/main>/g);
    assert.equal(
      open,
      close,
      `expected <main> open (${open}) and close (${close}) tag counts to match`
    );
  });

  await t.test(
    "has a matching number of <section> and </section> tags",
    () => {
      const open = countMatches(html, /<section\b[^>]*>/g);
      const close = countMatches(html, /<\/section>/g);
      assert.equal(
        open,
        close,
        `expected <section> open (${open}) and close (${close}) tag counts to match`
      );
    }
  );

  await t.test("has a matching number of <div> and </div> tags", () => {
    const open = countMatches(html, /<div\b[^>]*>/g);
    const close = countMatches(html, /<\/div>/g);
    assert.equal(
      open,
      close,
      `expected <div> open (${open}) and close (${close}) tag counts to match`
    );
  });

  await t.test(
    "opens the #about section before the 'Sobre' heading (regression)",
    () => {
      const soberIndex = html.indexOf("<h2>Sobre</h2>");
      assert.notEqual(soberIndex, -1, "expected to find the 'Sobre' heading");

      const aboutSectionOpenIndex = html.indexOf(
        '<section id="about" class="about">'
      );
      assert.notEqual(
        aboutSectionOpenIndex,
        -1,
        'expected an opening <section id="about" class="about"> tag'
      );
      assert.ok(
        aboutSectionOpenIndex < soberIndex,
        "the #about section must open before its 'Sobre' heading"
      );
    }
  );

  await t.test(
    "wraps the #main content in an opening <main id=\"main\"> tag (regression)",
    () => {
      const mainCloseIndex = html.indexOf("</main>");
      assert.notEqual(mainCloseIndex, -1, "expected a closing </main> tag");

      const mainOpenIndex = html.indexOf('<main id="main">');
      assert.notEqual(
        mainOpenIndex,
        -1,
        'expected an opening <main id="main"> tag'
      );
      assert.ok(
        mainOpenIndex < mainCloseIndex,
        "the opening <main> tag must precede its closing </main> tag"
      );
    }
  );
});