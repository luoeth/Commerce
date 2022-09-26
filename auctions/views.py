from email import message
from unicodedata import category
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

def listing(request, id):
    listingdate = Listing.objects.get(pk=id)
    islistinginwatchlist = request.user in listingdate.watchlist.all()
    allcomment = Comment.objects.filter(listing=listingdate)
    isowner = request.user.username == listingdate.owner.username
    return render(request, "auctions/listing.html",{
        "listing" : listingdate,
        "islistinginwatchlist" : islistinginwatchlist,
        "allcomment" : allcomment,
        "isowner" : isowner,
    })

def closeauction(request, id):
    listingdate = Listing.objects.get(pk=id)
    listingdate.isactive = False
    listingdate.save()
    isowner = request.user.username == listingdate.owner.username
    islistinginwatchlist = request.user in listingdate.watchlist.all()
    allcomment = Comment.objects.filter(listing=listingdate)

    return render(request, "auctions/listing.html",{
        "listing" : listingdate,
        "isowner" : isowner,
        "update" : True,
        "message" : "Your auction is closed",
        "islistinginwatchlist" : islistinginwatchlist,
        "allcomment" : allcomment,
    })


def removewatchlist(request, id):
    listingdate = Listing.objects.get(pk=id)
    currentuser = request.user
    listingdate.watchlist.remove(currentuser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addwatchlist(request, id):
    listingdate = Listing.objects.get(pk=id)
    currentuser = request.user
    listingdate.watchlist.add(currentuser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))
    
def displaywatchlist(request):
    currentuser = request.user
    listings = currentuser.listingwatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings" : listings,
    })

def addcomment(request, id):
    listingdate = Listing.objects.get(pk=id)
    currentuser = request.user
    message = request.POST['addcomment']

    addcomment = Comment(
        listing = listingdate,
        author = currentuser,
        message = message,
    )
    addcomment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addbid(request, id):
    newbid = request.POST['addbid']
    listingdate = Listing.objects.get(pk=id)
    islistinginwatchlist = request.user in listingdate.watchlist.all()
    allcomment = Comment.objects.filter(listing=listingdate)
    isowner = request.user.username == listingdate.owner.username
    if int(newbid) > listingdate.price.bid:
        updatebid = Bid(user=request.user, bid=int(newbid))
        updatebid.save()
        listingdate.price = updatebid
        listingdate.save()
        return render(request, "auctions/listing.html",{
            "listing" : listingdate,
            "message" : "Bid successfully",
            "update" : True,
            "islistinginwatchlist" : islistinginwatchlist,
            "allcomment" : allcomment,
            "isowner" : isowner,
        })
    else:
        return render(request, "auctions/listing.html",{
            "listing" : listingdate,
            "message" : "Bid failed",
            "update" : False,
            "islistinginwatchlist" : islistinginwatchlist,
            "allcomment" : allcomment,
            "isowner" : isowner,
        })

def index(request):
    activelistings = Listing.objects.filter(isactive=True)
    allcategory = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings" : activelistings,
        "category" : allcategory,
    })

def displaycategory(request):
    if request.method == "POST":
        categoryfromform = request.POST['category']
        category = Category.objects.get(categoryname=categoryfromform)
        activelistings = Listing.objects.filter(isactive=True, category=category)
        allcategory = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings" : activelistings,
            "category" : allcategory,
        })


def createlisting(request):
    if request.method == "GET":
        allcategory = Category.objects.all()
        return render(request, "auctions/create.html", {
            "category" : allcategory
        })
    else:
        #Get date from the form
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]
        #Who is user
        currentuser = request.user
        #Get all content about the particular category
        categorydate = Category.objects.get(categoryname=category)
        #Creat a bid object
        bid = Bid(bid=int(price), user=currentuser)
        bid.save()
        #Creat a new listing
        newListing = Listing(
            title=title,
            description=description,
            imageurl=imageurl,
            price=bid,
            category=categorydate,
            owner=currentuser
        )
        #Insert the object in the database
        newListing.save()
        #Redirect to index
        return HttpResponseRedirect(reverse("index")) 

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
