"""Parsing rules that keep a generated page honest.

The rule these tests exist for is that unknown and zero are different. A section
that says "None." is a founder telling us there are no live deals; a section that
is absent is us not knowing. A parser that returns 0 for both produces a page
that is confidently wrong, which is the failure mode the whole product argues
against.
"""
import importlib
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"


def load_dashboard(name):
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.%s" % name)


parse = load_dashboard("parse")


class TestMoney(unittest.TestCase):
    def test_dollar_amount_with_separators(self):
        value = parse.parse_money("$31,000")
        self.assertEqual(value.number, 31000.0)
        self.assertEqual(value.currency, "$")

    def test_amount_inside_a_sentence(self):
        self.assertEqual(parse.parse_money("Booked: $18,000 fixed fee").number, 18000.0)

    def test_unparseable_keeps_the_raw_text_and_no_number(self):
        value = parse.parse_money("to be agreed")
        self.assertIsNone(value.number)
        self.assertEqual(value.raw, "to be agreed")

    def test_empty_is_not_zero(self):
        self.assertIsNone(parse.parse_money("").number)
        self.assertIsNone(parse.parse_money(None).number)

    def test_a_date_is_not_an_amount(self):
        value = parse.parse_money("Acme — won 2026-08-15 — $18,000")
        self.assertEqual(value.number, 18000.0)
        self.assertEqual(value.currency, "$")

    def test_an_entry_carrying_only_a_date_has_no_amount(self):
        self.assertIsNone(parse.parse_money("Northwind — 2026-07-17 — qualified").number)

    def test_digits_inside_an_identifier_are_not_an_amount(self):
        self.assertIsNone(
            parse.parse_money("[q-0717b] publish the case study — bet: B2").number)

    def test_a_comma_separated_list_is_not_one_number(self):
        self.assertEqual(parse.parse_money("last four: 4, 3, 3, 2").number, 4.0)

    def test_trailing_currency_code_is_read(self):
        value = parse.parse_money("15 000 PLN")
        self.assertEqual(value.number, 15000.0)
        self.assertEqual(value.currency, "PLN")

    def test_trailing_currency_sign_is_read(self):
        self.assertEqual(parse.parse_money("12 000 zł").currency, "zł")
        self.assertEqual(parse.parse_money("18,000 EUR").currency, "EUR")
        self.assertEqual(parse.parse_money("3 500 €").currency, "€")

    def test_a_hyphenated_acronym_is_not_a_currency(self):
        value = parse.parse_money("8 ICP-matched discovery calls")
        self.assertEqual(value.number, 8.0)
        self.assertIsNone(value.currency)

    def test_an_unmarked_amount_reports_no_currency(self):
        value = parse.parse_money("Amount: 18,000")
        self.assertEqual(value.number, 18000.0)
        self.assertIsNone(value.currency)

    def test_comma_before_three_digits_is_a_thousands_separator(self):
        self.assertEqual(parse.parse_money("$1,234").number, 1234.0)
        self.assertEqual(parse.parse_money("1,234,567").number, 1234567.0)

    def test_decimal_comma_is_not_a_thousands_separator(self):
        self.assertEqual(parse.parse_money("24 000,50 PLN").number, 24000.5)
        self.assertEqual(parse.parse_money("1 234,56 PLN").number, 1234.56)
        self.assertEqual(parse.parse_money("Runway: 9,7 months").number, 9.7)

    def test_dot_thousands_with_a_decimal_comma(self):
        self.assertEqual(parse.parse_money("18.000,50").number, 18000.5)

    def test_a_lone_dot_before_three_digits_is_too_ambiguous_to_read(self):
        value = parse.parse_money("18.000")
        self.assertIsNone(value.number)
        self.assertEqual(value.raw, "18.000")

    def test_us_decimal_point_still_reads(self):
        self.assertEqual(parse.parse_money("$24,000.50").number, 24000.5)
        self.assertEqual(parse.parse_money("9.7 months").number, 9.7)

    def test_a_leading_minus_keeps_the_sign(self):
        self.assertEqual(parse.parse_money("-4,200").number, -4200.0)
        value = parse.parse_money("Cash on hand: -4 200 PLN")
        self.assertEqual(value.number, -4200.0)
        self.assertEqual(value.currency, "PLN")

    def test_a_number_glued_to_a_unit_is_not_read_as_its_first_digits(self):
        self.assertIsNone(parse.parse_money("3.5h").number)
        self.assertIsNone(parse.parse_money("18k").number)
        self.assertIsNone(parse.parse_money("last four: 4,3,3,2").number)

    def test_a_minus_written_apart_from_the_amount_is_still_a_minus(self):
        value = parse.parse_money("Cash on hand: - 4,200 PLN")
        self.assertEqual(value.number, -4200.0)
        self.assertEqual(value.currency, "PLN")

    def test_an_acronym_after_a_number_is_not_a_currency(self):
        for prose in ("3 CEO intros", "2 SOW drafts", "5 API keys",
                      "4 QBR sessions", "3 NDA rounds before signature",
                      "12 MRR reviews"):
            value = parse.parse_money(prose)
            self.assertIsNone(value.currency, prose)

    def test_an_acronym_before_a_number_is_not_a_currency(self):
        self.assertIsNone(parse.parse_money("CEO 3 intros").currency)
        self.assertIsNone(parse.parse_money("SOW 2 drafts").currency)

    def test_a_supported_code_is_still_read_after_the_amount(self):
        for text, number, code in (("15 000 PLN", 15000.0, "PLN"),
                                   ("18,000 EUR", 18000.0, "EUR"),
                                   ("24,000.50 USD", 24000.5, "USD"),
                                   ("GBP 1,200", 1200.0, "GBP")):
            value = parse.parse_money(text)
            self.assertEqual(value.number, number, text)
            self.assertEqual(value.currency, code, text)

    def test_a_grouped_number_that_cannot_be_decided_is_not_read(self):
        for text in ("1 234,567 PLN", "12 345,6789", "1000,500",
                     "Amount: 1 234,567", "1 234,56kg"):
            value = parse.parse_money(text)
            self.assertIsNone(value.number, text)
            self.assertIsNone(value.currency, text)

    def test_a_second_space_before_the_marker_keeps_the_currency(self):
        for text, number, code in (("$  18,000", 18000.0, "$"),
                                   ("18 000  PLN", 18000.0, "PLN"),
                                   ("18 000\tPLN", 18000.0, "PLN"),
                                   ("$\t18,000", 18000.0, "$")):
            value = parse.parse_money(text)
            self.assertEqual(value.number, number, text)
            self.assertEqual(value.currency, code, text)

    def test_accounting_parentheses_are_a_negative_amount(self):
        self.assertEqual(parse.parse_money("(4,200)").number, -4200.0)
        self.assertEqual(parse.parse_money("(4 200 PLN)").number, -4200.0)

    def test_a_parenthesised_aside_is_not_a_negative_amount(self):
        self.assertEqual(parse.parse_money("$24,000 (77%)").number, 24000.0)
        self.assertEqual(parse.parse_money("Runway 9 months (2026 plan)").number, 9.0)


class TestDates(unittest.TestCase):
    def test_iso_date_parses(self):
        self.assertEqual(parse.parse_iso_date("Judgment date: 2026-09-30"),
                         date(2026, 9, 30))

    def test_non_iso_date_is_not_guessed(self):
        self.assertIsNone(parse.parse_iso_date("30 September 2026"))

    def test_impossible_iso_date_is_rejected(self):
        self.assertIsNone(parse.parse_iso_date("2026-02-31"))


class TestFields(unittest.TestCase):
    BODY = "Closed: 2026-07-01\n\nBooked: $31,000\n\nCollected: $24,000 (77%)\n"

    def test_field_by_label(self):
        self.assertEqual(parse.parse_field(self.BODY, "Booked"), "$31,000")

    def test_absent_field_is_none(self):
        self.assertIsNone(parse.parse_field(self.BODY, "Receivables"))


class TestEntries(unittest.TestCase):
    def test_h3_blocks_become_entries(self):
        body = ("### Acme — sprint — $18,000 — proposal\n\n"
                "Next action: finish scope — 2026-07-20\n\n"
                "### Northwind — sprint — $15,000 — qualified\n\n"
                "Next action: send references — 2026-07-17\n")
        entries = parse.split_entries(body)
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].title.startswith("Acme"))
        self.assertIn("2026-07-20", entries[0].body)

    def test_list_items_become_entries_with_continuations_joined(self):
        body = ("- [q-0717b] publish the case study — bet: B2\n"
                "- [q-0717c] book 2 calls — bet: B1 — from:\n"
                "  pipeline.md 2026-07-17\n")
        entries = parse.split_entries(body)
        self.assertEqual(len(entries), 2)
        self.assertIn("pipeline.md 2026-07-17", entries[1].body)

    def test_indented_sub_bullets_stay_inside_their_entry(self):
        body = ("- [q-0717b] publish the case study — bet: B2\n"
                "  - waiting on the scope call\n"
                "- [q-0717c] book 2 calls — bet: B1\n"
                "  * second sub point\n")
        entries = parse.split_entries(body)
        self.assertEqual(len(entries), 2)
        self.assertIn("waiting on the scope call", entries[0].body)
        self.assertIn("second sub point", entries[1].body)

    def test_a_bullet_indented_less_than_the_content_column_is_a_sibling(self):
        entries = parse.split_entries("- a\n - b\n- c\n")
        self.assertEqual([entry.title for entry in entries], ["a", "b", "c"])

    def test_a_bullet_indented_to_the_content_column_stays_inside_its_entry(self):
        entries = parse.split_entries("- a\n  - note\n- b\n")
        self.assertEqual([entry.title for entry in entries], ["a", "b"])
        self.assertIn("note", entries[0].body)

    def test_declared_empty_is_recognised(self):
        self.assertTrue(parse.is_declared_empty("None.\n"))
        self.assertTrue(parse.is_declared_empty("none"))
        self.assertFalse(parse.is_declared_empty("Pending Friday review."))
        self.assertFalse(parse.is_declared_empty(""))

    def test_declared_empty_yields_no_entries(self):
        self.assertEqual(parse.split_entries("None.\n"), ())


class TestAmountsAreNeverInvented(unittest.TestCase):
    """The two shapes that put a number on the page the workspace never wrote.

    Both were introduced while fixing the other one, which is why they are pinned
    together: a parser that guesses a currency from shape reads prose as money,
    and a number pattern that has to both delimit and validate a token reports a
    fragment of the text — or a zero — when it cannot do either.
    """

    def test_an_uppercase_acronym_is_not_a_currency(self):
        for text in ("3 CEO intros", "2 SOW drafts", "5 API keys",
                     "4 QBR sessions", "3 NDA rounds before signature"):
            with self.subTest(text=text):
                self.assertIsNone(parse.parse_money(text).currency)

    def test_a_listed_code_is_still_a_currency(self):
        for text, code in (("15 000 PLN", "PLN"), ("18,000 EUR", "EUR"),
                           ("USD 1,200", "USD"), ("12 000 zl", None)):
            with self.subTest(text=text):
                if code is not None:
                    self.assertEqual(parse.parse_money(text).currency, code)

    def test_a_marked_amount_survives_the_prose_after_it(self):
        for text in ("Acme - $18,000 3 calls",
                     "Acme won $18,000 2026 renewal"):
            with self.subTest(text=text):
                value = parse.parse_money(text)
                self.assertEqual(value.number, 18000.0)
                self.assertEqual(value.currency, "$")

    def test_an_undelimitable_amount_is_unknown_and_never_zero(self):
        for text in ("100 00", "18 00", "5 0", "1234 567", "24 000 5",
                     "MRR: 100 00 PLN", "18,000 5 PLN"):
            with self.subTest(text=text):
                value = parse.parse_money(text)
                self.assertIsNone(
                    value.number,
                    "%r must not read as %r" % (text, value.number))

    def test_parenthesised_prose_is_not_an_accounting_negative(self):
        for text in ("(11 months at current burn)", "(estimate: 9 months)",
                     "(TBC - 68 000 PLN)", "(3 CEO intros)"):
            with self.subTest(text=text):
                number = parse.parse_money(text).number
                self.assertIsNotNone(number)
                self.assertGreater(number, 0, "%r read as a debt" % text)

    def test_a_parenthesised_value_is_an_accounting_negative(self):
        self.assertEqual(parse.parse_money("(4,200)").number, -4200.0)
        self.assertEqual(parse.parse_money("Cash on hand: (4 200)").number,
                         -4200.0)


class TestASectionIsEmptyOrUnreadableButNeverBoth(unittest.TestCase):
    """`None` and `()` are different answers and the callers must see both.

    A `## Live` written as a sentence used to return the same empty tuple as one
    written `None.`, so every caller counted it as zero deals and the page said
    so, citing the file that named them.
    """

    def test_a_section_written_as_prose_cannot_be_listed(self):
        prose = ("Two deals are live: Acme at $18,000 and Northwind at "
                 "$15,000, both proposals out.")
        self.assertIsNone(parse.split_entries(prose))

    def test_a_declared_empty_section_is_a_real_zero(self):
        self.assertEqual(parse.split_entries("None.\n"), ())

    def test_a_blank_section_is_a_real_zero(self):
        self.assertEqual(parse.split_entries("   \n"), ())
        self.assertEqual(parse.split_entries(None), ())

    def test_a_listed_section_still_lists(self):
        self.assertEqual(
            [entry.title for entry in parse.split_entries("- a\n- b\n")],
            ["a", "b"])


if __name__ == "__main__":
    unittest.main()
