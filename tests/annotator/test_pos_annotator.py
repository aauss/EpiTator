#!/usr/bin/env python
"""Tests for the POSAnnotator that annotates a sentence with part of speech tags
   that align with the token tier."""
from __future__ import absolute_import
import unittest

from epitator.annotator import AnnoDoc
from epitator.pos_annotator import POSAnnotator


class POSAnnotatorTest(unittest.TestCase):

    def setUp(self):
        self.annotator = POSAnnotator()

    def test_simple_sentence(self):

        self.doc = AnnoDoc("Hi Joe.")
        self.annotator.annotate(self.doc)

        self.assertEqual(len(self.doc.tiers['pos'].spans), 3)

        self.assertEqual(self.doc.tiers['pos'].spans[0].label, 'UH')
        self.assertEqual(self.doc.tiers['pos'].spans[0].start, 0)
        self.assertEqual(self.doc.tiers['pos'].spans[0].end, 2)

        self.assertEqual(self.doc.tiers['pos'].spans[1].label, 'NNP')
        self.assertEqual(self.doc.tiers['pos'].spans[1].start, 3)
        self.assertEqual(self.doc.tiers['pos'].spans[1].end, 6)

        self.assertEqual(self.doc.tiers['pos'].spans[2].label, '.')
        self.assertEqual(self.doc.tiers['pos'].spans[2].start, 6)
        self.assertEqual(self.doc.tiers['pos'].spans[2].end, 7)

    def test_initial_space(self):

        self.doc = AnnoDoc(" Hi.")
        self.annotator.annotate(self.doc)

        # This is true for the default wordpunct annotator, but not e.g. the
        # SpaceAnnotator
        self.assertEqual(len(self.doc.tiers['pos'].spans), 2)

        self.assertEqual(self.doc.tiers['pos'].spans[0].label, 'UH')
        self.assertEqual(self.doc.tiers['pos'].spans[0].start, 1)
        self.assertEqual(self.doc.tiers['pos'].spans[0].end, 3)

        self.assertEqual(self.doc.tiers['pos'].spans[1].label, '.')
        self.assertEqual(self.doc.tiers['pos'].spans[1].start, 3)
        self.assertEqual(self.doc.tiers['pos'].spans[1].end, 4)

    def test_multiple_spaces_in_a_row(self):

        self.doc = AnnoDoc("         Hi  there      Joe  .")
        self.annotator.annotate(self.doc)

        # This is true for the default wordpunct annotator, but not e.g. the
        # SpaceAnnotator
        self.assertEqual(len(self.doc.tiers['pos'].spans), 4)

        self.assertEqual(self.doc.tiers['pos'].spans[0].label, 'UH')
        self.assertEqual(self.doc.tiers['pos'].spans[0].text, 'Hi')
        self.assertEqual(self.doc.tiers['pos'].spans[0].start, 9)
        self.assertEqual(self.doc.tiers['pos'].spans[0].end, 11)

        self.assertEqual(self.doc.tiers['pos'].spans[1].label, 'RB')
        self.assertEqual(self.doc.tiers['pos'].spans[1].text, 'there')
        self.assertEqual(self.doc.tiers['pos'].spans[1].start, 13)
        self.assertEqual(self.doc.tiers['pos'].spans[1].end, 18)

        self.assertEqual(self.doc.tiers['pos'].spans[2].label, 'NNP')
        self.assertEqual(self.doc.tiers['pos'].spans[2].text, 'Joe')
        self.assertEqual(self.doc.tiers['pos'].spans[2].start, 24)
        self.assertEqual(self.doc.tiers['pos'].spans[2].end, 27)

        self.assertEqual(self.doc.tiers['pos'].spans[3].label, '.')
        self.assertEqual(self.doc.tiers['pos'].spans[3].text, '.')
        self.assertEqual(self.doc.tiers['pos'].spans[3].start, 29)
        self.assertEqual(self.doc.tiers['pos'].spans[3].end, 30)


if __name__ == '__main__':
    unittest.main()
