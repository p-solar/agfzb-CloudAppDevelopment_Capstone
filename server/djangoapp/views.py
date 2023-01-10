from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarMake
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request, get_dealer_by_id
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/index.html', context)
    else:
        return render(request, 'djangoapp/index.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        url = "https://56b09af2.us-south.apigw.appdomain.cloud/api/dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        # dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Create context
        context = {}
        context['dealership_list'] = dealerships
        # Render
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        # Get reviews
        url = "https://56b09af2.us-south.apigw.appdomain.cloud/api/review"
        reviews = get_dealer_reviews_from_cf(url, dealer_id)
        # Get dealer ID
        url = "https://56b09af2.us-south.apigw.appdomain.cloud/api/dealership"
        dealer = get_dealer_by_id(url, dealer_id)
        # Create context
        context = {}
        context['dealership_reviews'] = reviews
        context['dealer_id'] = dealer_id
        context['dealer'] = dealer
        # Render
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.method == 'GET':
        
        # Get cars
        cars = CarModel.objects.filter(dealer_id__exact=dealer_id)
        
        # Get dealer info
        url = "https://56b09af2.us-south.apigw.appdomain.cloud/api/dealership"
        dealer = get_dealer_by_id(url, dealer_id)
        
        # Prepare context
        context = dict(cars=cars)
        context['dealer_id'] = dealer_id
        context['dealer_name'] = dealer.full_name

        return render(request, 'djangoapp/add_review.html', context)
    if request.method == "POST":
        if request.user.is_authenticated:
            review = dict()
            review['review_time'] = datetime.utcnow().isoformat()
            review['reviewer_name'] = request.POST['reviewer_name']
            review['dealership'] = dealer_id
            review['review'] = request.POST['review']
            
            if 'purchase' in request.POST:
                if request.POST['purchase'] == 'true':
                    review['purchase'] = "true"
                else:
                    review['purchase'] = "false"
            else:
                review['purchase'] = "false"

            review['purchase_date'] = request.POST['purchase_date']
            car_id = int(request.POST['car'])
            car_details = CarModel.objects.get(id=car_id)
            
            review['car_model'] = car_details.model_name
            review['car_year'] = int(car_details.model_year.strftime("%Y"))
            car_makes = CarMake.objects.filter(carmodel__exact=car_id)
            review['car_make'] = car_makes[0].make_name
            print(review)
            
            # Configure POST request parameters
            url = "https://56b09af2.us-south.apigw.appdomain.cloud/api/review"
            json_payload = {}
            json_payload['review'] = review
            result = post_request(url=url, json_payload=review)
            print(result)
            return redirect('djangoapp:dealer_details', dealer_id=dealer_id)