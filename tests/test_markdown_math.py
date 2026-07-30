"""Unit tests for KaTeX / LaTeX markdown helper."""

from __future__ import annotations

import unittest

from dashboard.components.markdown_math import latex_to_streamlit_md


class TestLatexToStreamlit(unittest.TestCase):
    def test_display_brackets(self):
        src = r"Before \[ E = mc^2 \] after"
        out = latex_to_streamlit_md(src)
        self.assertIn("$$", out)
        self.assertIn("E = mc^2", out)
        self.assertNotIn(r"\[", out)

    def test_inline_parens(self):
        src = r"Power \( P = V I \) here"
        out = latex_to_streamlit_md(src)
        self.assertIn("$P = V I$", out)
        self.assertNotIn(r"\(", out)

    def test_dollar_passthrough(self):
        src = r"Already $$ x^2 $$ and $y$"
        out = latex_to_streamlit_md(src)
        self.assertIn("$$ x^2 $$", out)
        self.assertIn("$y$", out)

    def test_empty(self):
        self.assertEqual(latex_to_streamlit_md(""), "")


if __name__ == "__main__":
    unittest.main()
