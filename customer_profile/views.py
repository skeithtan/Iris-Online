from django.shortcuts import render
from django.views import View
from customer_profile.forms import UserForm
from django.contrib.auth.models import User
from customer_profile.models import Customer
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect


class SignInView(View):
    @staticmethod
    def get(request):
        return render(request, 'sign_in.html', None)

    @staticmethod
    def post(request):
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, 'sign_in.html', {
                "error": "Invalid Credentials"
            })


class SignUpView(View):
    @staticmethod
    def get(request):
        return render(request, 'sign_up.html', None)

    @staticmethod
    def post(request):
        form = UserForm(request.POST)

        if not form.is_valid():
            return render(request, 'sign_up.html', {
                'form': form
            })

        username = request.POST["username"]
        password = request.POST["password"]
        full_name = request.POST["full_name"]
        address = request.POST["address"]
        city = request.POST["city"]
        postal_code = request.POST["postal_code"]
        phone_number = request.POST["phone_number"]

        conflicts = User.objects.filter(username=username)
        if conflicts:
            return render(request, 'sign_up.html', {
                'error': f'User with e-mail {username} already exists.'
            })

        user = User.objects.create_user(username=username, password=password)

        Customer.objects.create(user=user, phone_number=phone_number,
                                full_name=full_name, city=city,
                                address=address, postal_code=postal_code)

        login(request, user)
        return redirect('/')  # TODO Redirect to customer profile page


def sign_out(request):
    logout(request)
    return redirect('/')
