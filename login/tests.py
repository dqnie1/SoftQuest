from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from contenido.operaciones.OperacionesContenido import OperacionesContenido
from login.models import Usuario


User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='estudiante',
            email='estudiante@example.com',
            password='Clave-segura-928!',
        )

    def test_login_accepts_username_or_email(self):
        for identifier in ('estudiante', 'estudiante@example.com'):
            response = self.client.post(
                reverse('login'),
                {'username': identifier, 'password': 'Clave-segura-928!'},
            )
            self.assertRedirects(
                response,
                reverse('mapa_mundos'),
                fetch_redirect_response=False,
            )
            self.client.logout()

    def test_registration_creates_auth_account_and_login_profile(self):
        response = self.client.post(
            reverse('registro'),
            {
                'username': 'nueva',
                'nombre': 'Nueva Estudiante',
                'email': 'nueva@example.com',
                'password1': 'Una-clave-segura-928!',
                'password2': 'Una-clave-segura-928!',
            },
        )

        self.assertRedirects(
            response,
            reverse('mapa_mundos'),
            fetch_redirect_response=False,
        )
        user = User.objects.get(username='nueva')
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.perfil_contenido.nombre, 'Nueva Estudiante')
        self.assertEqual(user.perfil_contenido.email, 'nueva@example.com')

    def test_protected_pages_redirect_to_login(self):
        response = self.client.get(reverse('mapa_mundos'))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("mapa_mundos")}',
            fetch_redirect_response=False,
        )

    def test_login_and_registration_pages_render(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        response = self.client.get(reverse('registro'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'class="form-group password-confirmation" hidden',
        )
        self.assertNotContains(response, 'class="form-help"')

    def test_registration_shows_confirmation_after_password_submission(self):
        response = self.client.post(
            reverse('registro'),
            {
                'username': 'nueva',
                'nombre': 'Nueva Estudiante',
                'email': 'nueva@example.com',
                'password1': '123',
                'password2': '123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-group password-confirmation"')
        self.assertNotContains(
            response,
            'class="form-group password-confirmation" hidden',
        )
        self.assertContains(response, 'class="field-errors" role="alert"')

    def test_minigame_pages_require_authentication(self):
        for url_name in ('memorama:memorama', 'trivia:trivia', 'match:match'):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('login')))

    def test_authenticated_accounts_get_distinct_content_profiles(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        profile = OperacionesContenido().obtener_usuario(request)

        second_user = User.objects.create_user(
            username='otra',
            email='otra@example.com',
            password='Clave-segura-928!',
        )
        request.user = second_user
        second_profile = OperacionesContenido().obtener_usuario(request)

        self.assertNotEqual(profile.pk, second_profile.pk)
        self.assertEqual(profile.cuenta, self.user)
        self.assertEqual(second_profile.cuenta, second_user)
