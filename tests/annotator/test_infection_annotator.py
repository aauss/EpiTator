#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests the ability of the new infection annotator to annotatate counts of cases
and deaths in english text.
"""
from __future__ import absolute_import
import unittest
from . import test_utils
from epitator.annotator import AnnoDoc
from epitator.infection_annotator import InfectionAnnotator
from six.moves import zip


class TestInfectionAnnotator(unittest.TestCase):

    def setUp(self):
        self.annotator = InfectionAnnotator()

    def assertHasCounts(self, sent, counts):
        doc = AnnoDoc(sent)
        doc.add_tier(self.annotator)
        actuals = [span.metadata.get('count') for span in doc.tiers['infections']]
        expecteds = [count.get('count') for count in counts]
        self.assertEqual(actuals, expecteds)
        for actual, expected in zip(doc.tiers['infections'].spans, counts):
            test_utils.assertMetadataContents(actual.metadata, expected)

    def test_no_counts(self):
        doc = AnnoDoc('Fever')
        doc.add_tier(self.annotator)

    def test_false_positive_counts(self):
        examples = [
            # 'In the case of mosquito-borne diseases indoor spraying is a common intervention',
            'Measles - Democratic Republic of the Congo (Katanga) 2007.1775',
            'Meningitis - Democratic Republic of Congo [02] 970814010223',
            'On 11 / 16 / 1982 the The Last Unicorn was the most popular movie.'
        ]
        for example in examples:
            self.assertHasCounts(example, [])

    def test_age_elimination(self):
        doc = AnnoDoc(
            '1200 children under the age of 5 are afflicted with a mystery illness')
        doc.add_tier(self.annotator)
        test_utils.assertHasProps(
            doc.tiers['infections'].spans[0].metadata, {
                'count': 1200
            }
        )
        self.assertEqual(len(doc.tiers['infections'].spans), 1)

    # def test_complex(self):
    #     sent = 'These 2 new cases bring to 4 the number stricken in California this year [2012].'
    #     counts = [
    #         {'count': 2, 'attributes': ['infection']},
    #         {'count': 4, 'attributes': ['infection']}
    #     ]
    #     self.assertHasCounts(sent, counts)

    def test_complex_2(self):
        sent = 'Two patients died out of four patients.'
        counts = [
            {'count': 2, 'attributes': ['infection', 'death', 'person']},
            {'count': 4, 'attributes': ['infection']}
        ]
        self.assertHasCounts(sent, counts)

    def test_distance_and_percentage_filtering(self):
        examples = [
            ('48 percent of the cases occured in Seattle', []),
            ('28 kilometers away [17.4 miles]', [])
        ]
        for example in examples:
            sent, counts = example
            self.assertHasCounts(sent, counts)

    def test_tokenization_edge_cases(self):
        """
        These examples triggered some bugs with word token alignment in the past.
        """
        examples = [
            ('These numbers include laboratory-confirmed, probable, and suspect cases and deaths of EVD.', []),
            ("""22 new cases of EVD, including 14 deaths, were reported as follows:
        Guinea, 3 new cases and 5 deaths; Liberia, 8 new cases with 7 deaths; and Sierra Leone, 11 new cases and 2 deaths.
        """, [{'count': 22}, {'count': 14}, {'count': 3}, {'count': 5}, {'count': 8}, {'count': 7}, {'count': 11}, {'count': 2}])]
        for example in examples:
            sent, counts = example
            self.assertHasCounts(sent, counts)

    def test_singular_cases(self):
        self.assertHasCounts('The index case occured on January 22.', [
            {'count': 1, 'attributes': ['infection']}])

    def test_singular_cases_2(self):
        self.assertHasCounts('A lassa fever case was reported in Hawaii', [
            {'count': 1, 'attributes': ['infection']}])

    def test_singular_cases_3(self):
        self.assertHasCounts('They reported a patient infected with hepatitis B from a blood transfusion.',
                             [{'count': 1}])

    def test_year_count(self):
        self.assertHasCounts("""As of [Sun 19 March 2017] (epidemiological week 11),
        a total of 1407 suspected cases of meningitis have been reported.""", [
            {'count': 1407}])

    def test_count_suppression_fp(self):
        # Test that the count of 26 is not supressed by the 20 count
        doc = AnnoDoc('''
        20 in Montserrado County [Monrovia & environs); 26 deaths are among the confirmed cases.
        Foya, Lofa County, and New Kru Town [NW suburb of Monrovia],
        Montserrado County, remain the epicentres of this Ebola outbreak.
        ''')
        doc.add_tier(self.annotator)
        test_utils.assertMetadataContents(
            doc.tiers['infections'].spans[0].metadata, {
                'count': 26,
                'attributes': ['death']
            })

    def test_space_delimited_counts(self):
        self.assertHasCounts('There were 197 000 deaths in 2007.',
                             [{'count': 197000, 'attributes': ['death']}])

    def test_cumulative(self):
        sent = 'Nationwide, a total of 613 cases of the disease have been reported as of 2 July 2014, with 63 deceased patients'
        counts = [
            {'count': 613, 'attributes': ['infection', 'cumulative']},
            {'count': 63, 'attributes': ['death']}
        ]
        self.assertHasCounts(sent, counts)

    def test_attributes(self):
        self.assertHasCounts('There have been a total of 1715 confirmed cases of MERS-CoV infection. '
                             'There was one suspected case of bird flu in the country.',
                             [{'count': 1715, 'attributes': ['cumulative', 'confirmed', 'infection']},
                              {'count': 1, 'attributes': ['infection', 'suspected']}])

    def test_recovered_case_removal(self):
        self.assertHasCounts('5 recovered cases of Ebola were discharged from the hospital.', [])


if __name__ == '__main__':
    unittest.main()
