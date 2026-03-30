from typing import List
from decimal import Decimal, InvalidOperation
from datetime import datetime

def validate_row(row: dict) -> List[str]:
    errors = []
    required = ['product_sku', 'sector_code', 'date', 'units_sold', 'price']
    
    for field in required:
        if not row.get(field):
            errors.append(f'Missing {field}')
    
    try:
        datetime.strptime(row['date'], '%Y-%m-%d')
    except:
        errors.append('Invalid date format (YYYY-MM-DD)')
    
    try:
        units = Decimal(row['units_sold'])
        if units <= 0:
            errors.append('units_sold must be >0')
    except InvalidOperation:
        errors.append('Invalid units_sold')
    
    try:
        price = Decimal(row['price'])
        if price <= 0:
            errors.append('price must be >0')
    except InvalidOperation:
        errors.append('Invalid price')
    
    return errors

