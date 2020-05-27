from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import time
import re
import json
from bs4 import BeautifulSoup
import pdb
import os
from . import similar_patterns as sp

# Create your views here.

@csrf_exempt
def process(request):
  query = None
  try:
      query = request.POST['query']
  except:
      return JsonResponse({"error": "request not received", "result": ""})
  else:
      url = None
      if not re.match(r"^((https?):\/\/)?(www\.)?ravelry\.com\/patterns\/library\/\S+$", query):
          return JsonResponse({"error": "Please enter a valid URL.", "result": ""})
      try:
          url = sp.pattern_url_to_website_search_url(query)
      except:
          return JsonResponse({"error": "No data found for this pattern.", "result": ""})
      else: 
          return JsonResponse({"result": url, "error": ""})