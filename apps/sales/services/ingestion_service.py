from typing import Dict, List, Any
from decimal import Decimal
from apps.products.models import Product
from apps.sectors.models import Sector
from apps.audit.models import AuditLog
from apps.users.models import User
import csv
from io import StringIO
import uuid
from django.db import transaction
from django.utils import timezone
from .validation_service import validate_row
from ..models import Sale

class SalesIngestionService:
    @staticmethod
    @transaction.atomic
    def process_csv(csv_content: str, user_id: int) -> Dict[str, Any]:
        """
        Process CSV upload for sales data.
        CSV format: product_sku,sector_code,date,units_sold,price,region,revenue
        Compute revenue if missing.
        """
        reader = csv.DictReader(StringIO(csv_content))
        valid_rows = []
        invalid_rows = []
        ingestion_id = str(uuid.uuid4())
        
        for row_num, row in enumerate(reader, start=2):
            errors = validate_row(row)
            if not errors:
                try:
                    units = Decimal(row['units_sold'])
                    price = Decimal(row['price'])
                    revenue = Decimal(row['revenue']) if row.get('revenue') else units * price
                    product = Product.objects.get(sku=row['product_sku'])
                    sector = Sector.objects.get(code=row['sector_code'])
                    sale = Sale(
                        product=product,
                        sector=sector,
                        date=row['date'],
                        units_sold=units,
                        price=price,
                        region=row.get('region', ''),
                        revenue=revenue
                    )
                    valid_rows.append(sale)
                except (Product.DoesNotExist, Sector.DoesNotExist, ValueError):
                    invalid_rows.append({'row': row_num, 'errors': ['Product/Sector not found or invalid data']})
            else:
                invalid_rows.append({'row': row_num, 'errors': errors})
        
        if valid_rows:
            Sale.objects.bulk_create(valid_rows, ignore_conflicts=True)
        
        user = User.objects.get(id=user_id)
        AuditLog.objects.create(
            user=user,
            action='SALES_INGEST',
            metadata={'ingestion_id': ingestion_id, 'valid': len(valid_rows), 'invalid': len(invalid_rows)}
        )
        
        return {
            'ingestion_id': ingestion_id,
            'valid_count': len(valid_rows),
            'invalid_count': len(invalid_rows),
            'invalid_rows': invalid_rows[:10],
            'status': 'completed'
        }

    @staticmethod
    def get_status(ingestion_id: str) -> Dict[str, Any]:
        return {'status': 'completed', 'ingestion_id': ingestion_id}

    @staticmethod
    def export_csv(queryset):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'product_sku', 'sector_code', 'date', 'units_sold', 'revenue', 'price', 'region', 'created_at'])
        for sale in queryset:
            writer.writerow([
                str(sale.id),
                sale.product.sku,
                sale.sector.code,
                str(sale.date),
                str(sale.units_sold),
                str(sale.revenue),
                str(sale.price),
                sale.region,
                str(sale.created_at)
            ])
        return output.getvalue()
