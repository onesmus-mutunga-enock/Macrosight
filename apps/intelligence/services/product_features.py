"""
Product feature extraction service.
Returns ML-ready dict for cross-app feature builder.
"""
from typing import Dict, Any, Union
from datetime import date
from apps.products.models import Product


def get_product_features(product_id: Union[int, str, Product]) -> Dict[str, float]:
	"""Return product-level deterministic features.

	Features provided:
	  - category_id: numeric category identifier
	  - shelf_life_days: numeric (0 if unknown)
	  - is_perishable: 0/1
	  - avg_price: product list price or 0.0
	  - seasonality_sin / seasonality_cos: simple month-based encoding

	Accepts a Product instance or id.
	"""
	# Resolve product instance
	if isinstance(product_id, Product):
		product = product_id
	else:
		try:
			product = Product.objects.get(pk=product_id)
		except Exception:
			# Return safe defaults when product not found
			return {
				'category_id': 0.0,
				'shelf_life_days': 0.0,
				'is_perishable': 0.0,
				'avg_price': 0.0,
				'seasonality_sin': 0.0,
				'seasonality_cos': 0.0,
			}

	# Basic encodings
	category_id = float(getattr(product, 'category_id', 0) or 0)
	shelf_life = getattr(product, 'shelf_life_days', None)
	shelf_life_days = float(shelf_life) if shelf_life is not None else 0.0
	is_perishable = 1.0 if shelf_life_days and shelf_life_days < 30 else 0.0

	avg_price = float(getattr(product, 'price', 0.0) or 0.0)

	# Simple seasonality encoding using current month to keep deterministic
	month = date.today().month
	import math
	seasonality_sin = math.sin(2 * math.pi * (month / 12.0))
	seasonality_cos = math.cos(2 * math.pi * (month / 12.0))

	return {
		'category_id': category_id,
		'shelf_life_days': shelf_life_days,
		'is_perishable': is_perishable,
		'avg_price': avg_price,
		'seasonality_sin': seasonality_sin,
		'seasonality_cos': seasonality_cos,
	}
