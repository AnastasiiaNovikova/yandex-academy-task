import unittest
from unittest.mock import MagicMock

from jsonschema import ValidationError
from parameterized import parameterized

from application.data_validator import DataValidator
from tests import test_utils


class ImportValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_validator = DataValidator()

    def assert_exception(self, import_data: dict, expected_exception_message: str):
        with self.assertRaises(ValidationError) as context:
            self.data_validator.validate_import(import_data)
        print(str(context.exception))
        self.assertIn(expected_exception_message, str(context.exception))

    def test_correct_import_should_be_valid(self):
        import_data = test_utils.read_data('import.json')
        self.data_validator.validate_import(import_data)

    @parameterized.expand([
        ({}, 'citizens'),
        ({'citizens': [{'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A', 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'citizen_id'),
        ({'citizens': [{'citizen_id': 0, 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A', 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'town'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'building': 'A', 'apartment': 0, 'name': 'A', 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'street'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'apartment': 0, 'name': 'A', 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'building'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'name': 'A', 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'apartment'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'birth_date': '',
                        'gender': 'male', 'relatives': []}]}, 'name'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'gender': 'male', 'relatives': []}]}, 'birth_date'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'relatives': []}]}, 'gender'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male'}]}, 'relatives'),
    ])
    def test_import_should_be_incorrect_when_missing_field(self, import_data: dict, field_name: str):
        self.assert_exception(import_data, f'\'{field_name}\' is a required property')

    @parameterized.expand([
        ({'citizens': None}, 'array'),
        ({'citizens': [{'citizen_id': None, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'integer'),
        ({'citizens': [{'citizen_id': 0, 'town': None, 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': None, 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': None, 'apartment': '', 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': None, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'integer'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': None,
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': None, 'gender': 'male', 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': None, 'relatives': []}]}, 'string'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': None}]}, 'array'),
        ({'citizens': ['']}, 'object'),
        ({'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': ['']}]}, 'integer'),
    ])
    def test_import_should_be_incorrect_when_wrong_type_of_field(self, import_data: dict, data_type: str):
        self.assert_exception(import_data, f'is not of type \'{data_type}\'')

    def test_import_should_be_correct_with_different_field_order(self):
        import_data = {'citizens': [
            {'town': 'A', 'citizen_id': 0, 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
             'birth_date': '01.01.2019', 'gender': 'male', 'relatives': []}]}
        self.data_validator.validate_import(import_data)

    @parameterized.expand([
        [{'EXTRA': 0, 'citizens': [
            {'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
             'birth_date': '01.01.2019', 'gender': 'male', 'relatives': []}]}],
        [{'citizens': [
            {'EXTRA': 0, 'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
             'birth_date': '01.01.2019', 'gender': 'male', 'relatives': []}]}],
    ])
    def test_import_should_be_incorrect_when_containing_extra_fields(self, import_data: dict):
        self.assert_exception(import_data, '')

    @unittest.mock.patch('jsonschema.validate')
    def test_import_should_be_incorrect_when_citizen_ids_not_unique(self, _):
        import_data = {'citizens': [{'citizen_id': 1}, {'citizen_id': 1}]}
        self.assert_exception(import_data, 'Citizens ids are not unique')

    def test_import_should_be_incorrect_when_relatives_not_duplex(self):
        import_data = {'citizens': [
            {'citizen_id': 1, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
             'birth_date': '01.01.2019', 'gender': 'male', 'relatives': [2]},
            {'citizen_id': 2, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
             'birth_date': '01.01.2019', 'gender': 'male', 'relatives': []}
        ]}
        self.assert_exception(import_data, 'Citizen relatives are not duplex')

    @unittest.mock.patch('jsonschema.validate')
    def test_import_should_be_incorrect_when_citizen_is_relative_to_himself(self, _):
        import_data = {'citizens': [{'citizen_id': 1, 'relatives': [1]}]}
        self.assert_exception(import_data, 'Citizen can not be relative to himself')

    @unittest.mock.patch('jsonschema.validate')
    def test_import_should_be_incorrect_when_citizen_relative_not_exists(self, _):
        import_data = {'citizens': [{'citizen_id': 1, 'relatives': [2]}]}
        self.assert_exception(import_data, 'Citizen relative does not exists')

    def test_import_should_be_correct_when_no_citizens(self):
        import_data = {'citizens': []}
        self.data_validator.validate_import(import_data)

    @unittest.mock.patch('jsonschema.validate')
    def test_import_should_be_incorrect_when_relatives_not_unique(self, _):
        import_data = {'citizens': [{'citizen_id': 0, 'relatives': [1, 1]}]}
        self.assert_exception(import_data, 'Relatives ids should be unique')

    def test_import_should_be_incorrect_when_gender_not_male_or_female(self):
        import_data = {
            'citizens': [{'citizen_id': 1, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                          'birth_date': '', 'gender': 'helicopter', 'relatives': []}]}
        self.assert_exception(import_data, 'is not one of [\'male\', \'female\']')

    @parameterized.expand([
        [{'citizens': [{'citizen_id': -1, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}],
        [{'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': -1, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}]
    ])
    def test_import_should_be_incorrect_when_less_then_zero(self, import_data: dict):
        self.assert_exception(import_data, 'Failed validating \'minimum\'')

    @parameterized.expand([
        [{'citizens': [{'citizen_id': 0, 'town': '', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}],
        [{'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': '', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}],
        [{'citizens': [{'citizen_id': 0, 'town': 'A', 'street': '', 'building': 'A', 'apartment': 0, 'name': 'A',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}],
        [{'citizens': [{'citizen_id': 0, 'town': 'A', 'street': 'A', 'building': 'A', 'apartment': 0, 'name': '',
                        'birth_date': '', 'gender': 'male', 'relatives': []}]}],
    ])
    def test_import_should_be_incorrect_empty_string(self, import_data: dict):
        self.assert_exception(import_data, 'is too short')


if __name__ == '__main__':
    unittest.main()
