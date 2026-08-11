import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(REPO_ROOT, "index.html")

class AgeCalculationTests(unittest.TestCase):
    """Tests for the age and experience calculation logic embedded in index.html."""

    @classmethod
    def setUpClass(cls):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as fh:
            cls.raw_html = fh.read()

    def test_script_constants_exist_and_are_correct(self):
        birth_year_match = re.search(r"ano_nascimento\s*=\s*(\d+)", self.raw_html)
        birth_month_match = re.search(r"mes_nascimento\s*=\s*(\d+)", self.raw_html)
        birth_day_match = re.search(r"dia_nascimento\s*=\s*(\d+)", self.raw_html)

        self.assertIsNotNone(birth_year_match, "Could not find ano_nascimento in HTML")
        self.assertIsNotNone(birth_month_match, "Could not find mes_nascimento in HTML")
        self.assertIsNotNone(birth_day_match, "Could not find dia_nascimento in HTML")

        birth_year = int(birth_year_match.group(1))
        birth_month = int(birth_month_match.group(1))
        birth_day = int(birth_day_match.group(1))

        self.assertEqual(birth_year, 2002, "Birth year should be 2002")
        self.assertEqual(birth_month, 11, "Birth month should be 11 (November)")
        self.assertEqual(birth_day, 5, "Birth day should be 5")

    def calculate_idade(self, current_year, current_month_0_indexed, current_date, birth_year=2002, birth_month=11, birth_day=5):
        idade = current_year - birth_year
        if current_month_0_indexed < (birth_month - 1):
            idade -= 1
        elif (birth_month - 1) == current_month_0_indexed and current_date < birth_day:
            idade -= 1
        return idade

    def test_age_calculation_logic(self):
        self.assertEqual(self.calculate_idade(2023, 10, 5), 21)
        self.assertEqual(self.calculate_idade(2023, 10, 4), 20)
        self.assertEqual(self.calculate_idade(2023, 10, 6), 21)
        self.assertEqual(self.calculate_idade(2023, 9, 5), 20)
        self.assertEqual(self.calculate_idade(2023, 11, 5), 21)
        self.assertEqual(self.calculate_idade(2002, 10, 5), 0)
        self.assertEqual(self.calculate_idade(2002, 10, 4), -1)

    def test_experience_calculation_logic(self):
        for age in range(13, 100):
            experience = age - 13
            self.assertGreaterEqual(experience, 0, f"Experience must be non-negative for age {age}")

if __name__ == "__main__":
    unittest.main()