from django.test import RequestFactory, TestCase, Client
from django.urls import reverse
from cart.context_processors import cart_context
from store.models import Product


class CartContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_cart_context_empty(self):
        request = self.factory.get('/')
        request.session = {}
        context = cart_context(request)
        self.assertEqual(context['cart_total_items'], 0)

    def test_cart_context_with_items(self):
        request = self.factory.get('/')
        request.session = {'cart': {'1': 2, '2': 3}}
        context = cart_context(request)
        self.assertEqual(context['cart_total_items'], 5)


class CartViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.in_stock = Product.objects.create(
            name='Mechanical Keyboard',
            description='Tactile switches',
            price=80.00,
            image_url='https://example.com/keyboard.jpg',
            stock=5,
        )
        self.out_of_stock = Product.objects.create(
            name='Sold Out Webcam',
            description='HD Webcam',
            price=40.00,
            image_url='https://example.com/webcam.jpg',
            stock=0,
        )

    def test_cart_detail_empty(self):
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your cart is empty')

    def test_cart_add_success(self):
        response = self.client.post(reverse('cart:cart_add', args=[self.in_stock.id]), {'quantity': 2})
        self.assertRedirects(response, reverse('cart:cart_detail'))
        session = self.client.session
        self.assertEqual(session['cart'][str(self.in_stock.id)], 2)

    def test_cart_add_out_of_stock_rejected(self):
        response = self.client.post(reverse('cart:cart_add', args=[self.out_of_stock.id]), {'quantity': 1})
        self.assertRedirects(response, reverse('store:product_detail', args=[self.out_of_stock.id]))
        session = self.client.session
        self.assertNotIn(str(self.out_of_stock.id), session.get('cart', {}))

    def test_cart_update_quantity(self):
        session = self.client.session
        session['cart'] = {str(self.in_stock.id): 1}
        session.save()

        response = self.client.post(reverse('cart:cart_update', args=[self.in_stock.id]), {'quantity': 3})
        self.assertRedirects(response, reverse('cart:cart_detail'))
        self.assertEqual(self.client.session['cart'][str(self.in_stock.id)], 3)

    def test_cart_remove_item(self):
        session = self.client.session
        session['cart'] = {str(self.in_stock.id): 2}
        session.save()

        response = self.client.post(reverse('cart:cart_remove', args=[self.in_stock.id]))
        self.assertRedirects(response, reverse('cart:cart_detail'))
        self.assertNotIn(str(self.in_stock.id), self.client.session.get('cart', {}))
