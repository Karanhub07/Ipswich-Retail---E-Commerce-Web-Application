from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Product


class CategoryModelTests(TestCase):
    def test_category_str(self):
        category = Category.objects.create(name='Audio', slug='audio')
        self.assertEqual(str(category), 'Audio')


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Audio', slug='audio')
        self.product = Product.objects.create(
            category=self.category,
            name='Wireless Headphones',
            description='Active noise cancellation',
            price=99.99,
            image_url='https://example.com/headphones.jpg',
            stock=10,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), 'Wireless Headphones')

    def test_product_fields(self):
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(float(self.product.price), 99.99)
        self.assertEqual(self.product.category.name, 'Audio')


class StoreViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Peripherals', slug='peripherals')
        self.product = Product.objects.create(
            category=self.category,
            name='Gaming Mouse',
            description='High precision sensor',
            price=49.99,
            image_url='https://example.com/mouse.jpg',
            stock=5,
        )

    def test_product_list_view_status_200(self):
        response = self.client.get(reverse('store:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gaming Mouse')

    def test_product_filter_by_category(self):
        other_cat = Category.objects.create(name='Displays', slug='displays')
        Product.objects.create(
            category=other_cat,
            name='4K Monitor',
            description='UHD Display',
            price=300.00,
            image_url='https://example.com/monitor.jpg',
            stock=3,
        )
        response = self.client.get(reverse('store:product_list'), {'category': 'peripherals'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gaming Mouse')
        self.assertNotContains(response, '4K Monitor')

    def test_product_search_finds_match(self):
        response = self.client.get(reverse('store:product_list'), {'q': 'Gaming'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gaming Mouse')

    def test_product_search_no_match(self):
        response = self.client.get(reverse('store:product_list'), {'q': 'NonExistentProduct'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No products found')

    def test_product_detail_view_status_200(self):
        response = self.client.get(reverse('store:product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'High precision sensor')

    def test_product_detail_view_404_missing(self):
        response = self.client.get(reverse('store:product_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_metrics_endpoint_returns_200(self):
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
