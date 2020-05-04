from django.shortcuts import render
from django.http import JsonResponse
import time

# Create your views here.
def index(request):
  return JsonResponse({"yay!": "you made it!"})