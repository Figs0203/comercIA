from abc import ABC, abstractmethod
from typing import Iterable, Tuple
from django.conf import settings
import csv
import io
import json


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, products: Iterable) -> Tuple[bytes, str, str]:
        """
        Returns (content_bytes, content_type, filename)
        """
        raise NotImplementedError


class CSVReportGenerator(ReportGenerator):
    def generate(self, products: Iterable) -> Tuple[bytes, str, str]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['id', 'name', 'category', 'price', 'available'])
        for p in products:
            writer.writerow([p.id, p.name, p.category, f"{p.price}", 'yes' if p.available else 'no'])
        data = buffer.getvalue().encode('utf-8')
        return data, 'text/csv; charset=utf-8', 'products_report.csv'


class JSONReportGenerator(ReportGenerator):
    def generate(self, products: Iterable) -> Tuple[bytes, str, str]:
        payload = []
        for p in products:
            payload.append({
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': float(p.price),
                'available': p.available,
            })
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        return data, 'application/json; charset=utf-8', 'products_report.json'


def get_report_generator() -> ReportGenerator:
    strategy = getattr(settings, 'REPORT_GENERATOR', 'csv').lower()
    if strategy == 'json':
        return JSONReportGenerator()
    return CSVReportGenerator()


