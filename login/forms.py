from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario o correo electrónico',
        widget=forms.TextInput(attrs={'autocomplete': 'username'}),
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            matching_usernames = list(
                User._default_manager.filter(email__iexact=username)
                .values_list('username', flat=True)[:2]
            )
            if len(matching_usernames) == 1:
                self.cleaned_data['username'] = matching_usernames[0]
        return super().clean()


class RegistroForm(UserCreationForm):
    nombre = forms.CharField(max_length=30, label='Nombre')
    email = forms.EmailField(label='Correo electrónico')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'nombre', 'email')
        labels = {'username': 'Nombre de usuario'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'

    def clean_email(self):
        email = self.cleaned_data['email']
        if User._default_manager.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
