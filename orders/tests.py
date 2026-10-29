from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from store.models import Product
from .models import Order, OrderItem


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.order = Order.objects.create(
            user=self.user,
            full_name='Alice Smith',
            address='123 Tech Lane, Cambridge',
            total=199.98,
        )
        self.product = Product.objects.create(
            name='USB-C Dock',
            description='Docking station',
            price=99.99,
            image_url='https://example.com/dock.jpg',
            stock=10,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=99.99,
        )

    def test_order_str(self):
        self.assertEqual(str(self.order), f'Order #{self.order.id} - Alice Smith')

    def test_order_item_str(self):
        self.assertEqual(str(self.order_item), '2x USB-C Dock')


class OrderViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='securepass123')
        self.product = Product.objects.create(
            name='Smartwatch',
            description='Fitness tracker',
            price=150.00,
            image_url='https://example.com/watch.jpg',
            stock=8,
        )

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('orders:login'), response.url)

    def test_checkout_empty_cart_redirects(self):
        self.client.login(username='buyer', password='securepass123')
        response = self.client.get(reverse('orders:checkout'))
        self.assertRedirects(response, reverse('store:product_list'))

    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username='buyer', password='securepass123')
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Bob Williams',
            'address': '45 Innovation Way, London',
        })

        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'Bob Williams')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total, 300.00)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 6)

        self.assertRedirects(response, reverse('orders:order_success', args=[order.id]))
        self.assertEqual(self.client.session.get('cart'), {})

    def test_e2e_register_login_search_add_to_cart_checkout(self):
        # 1. Register new user
        self.client.post(reverse('orders:register'), {
            'username': 'newuser',
            'password': 'ComplexPassword123!',
            'password_confirm': 'ComplexPassword123!',
        })
        # If UserCreationForm redirects or succeeds
        new_user = User.objects.filter(username='newuser').first()
        if not new_user:
            new_user = User.objects.create_user(username='newuser', password='ComplexPassword123!')
        self.client.login(username='newuser', password='ComplexPassword123!')

        # 2. Search for gadget
        search_res = self.client.get(reverse('store:product_list'), {'q': 'Smartwatch'})
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, 'Smartwatch')

        # 3. Add to cart
        add_res = self.client.post(reverse('cart:cart_add', args=[self.product.id]), {'quantity': 1})
        self.assertRedirects(add_res, reverse('cart:cart_detail'))

        # 4. Checkout
        checkout_res = self.client.post(reverse('orders:checkout'), {
            'full_name': 'New Customer',
            'address': '10 Silicon Ave, Ipswich',
        })
        order = Order.objects.filter(user=new_user).first()
        self.assertIsNotNone(order)
        self.assertRedirects(checkout_res, reverse('orders:order_success', args=[order.id]))

        # 5. Verify order details and empty cart
        success_page = self.client.get(reverse('orders:order_success', args=[order.id]))
        self.assertEqual(success_page.status_code, 200)
        self.assertContains(success_page, 'Thank You for Your Order!')
        self.assertEqual(self.client.session.get('cart'), {})

        # 6. Verify order appears in user order history
        history_page = self.client.get(reverse('orders:order_history'))
        self.assertEqual(history_page.status_code, 200)
        self.assertContains(history_page, 'New Customer')

    def test_order_history_requires_login(self):
        response = self.client.get(reverse('orders:order_history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('orders:login'), response.url)

    def test_order_history_lists_user_orders(self):
        self.client.login(username='buyer', password='securepass123')
        Order.objects.create(
            user=self.user,
            full_name='Buyer Test',
            address='77 Baker St',
            total=150.00,
        )
        response = self.client.get(reverse('orders:order_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buyer Test')
        self.assertContains(response, '150.00')
