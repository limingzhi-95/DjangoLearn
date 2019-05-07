from django import forms
import unittest


class AddForm(forms.Form):
    a = forms.IntegerField()
    b = forms.IntegerField()


class FormTest(unittest.TestCase):
    def test_one(self):
        data = {
            'a': 1,
            'b': 2
        }
        a = AddForm(data)

        a.is_valid()


if __name__ == '__main__':
    unittest.main()
