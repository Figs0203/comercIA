from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product
from .services.reporting import CSVReportGenerator


class ProductsApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p')
        Product.objects.create(
            name='Prod', description='Desc', price=10, seller=self.user, available=True
        )

    def test_products_api_returns_json(self):
        url = reverse('products_api')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)


class ReportGeneratorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u2', password='p')
        Product.objects.create(
            name='ReportProd', description='D', price=20, seller=self.user, available=True
        )

    def test_csv_report_generator_outputs_bytes(self):
        gen = CSVReportGenerator()
        content, content_type, filename = gen.generate(Product.objects.all())
        self.assertIsInstance(content, (bytes, bytearray))
        self.assertIn('text/csv', content_type)
        self.assertTrue(filename.endswith('.csv'))
