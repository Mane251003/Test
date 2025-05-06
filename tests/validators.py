# validators.py
from django.core.exceptions import ValidationError

import json
from django.core.exceptions import ValidationError

def validate_options(value):
    """
    Վալիդացնում է, որ տրված արժեքը համապատասխանում է JSON կառուցվածքին,
    և որ այն պարունակում է ճիշտ տվյալներ։
    """
    if not isinstance(value, str):
        raise ValidationError('Value must be a JSON string')

    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError('Invalid JSON format')


    if not isinstance(data, list):
        raise ValidationError('Data must be a list')

 
    for item in data:
        if not isinstance(item, dict):
            raise ValidationError('Each item must be a dictionary')
        if 'text' not in item or 'value' not in item:
            raise ValidationError('Each item must contain "text" and "value" keys')
        if not isinstance(item['text'], str) or not isinstance(item['value'], int):
            raise ValidationError('"text" must be a string and "value" must be an integer')


    return True