from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import time
import pandas as pd
import numpy as np 
import re
import json
from bs4 import BeautifulSoup
import pickle
import pdb
import os

# Create your views here.


def create_yarn_list(input_weight):
    id_dict = pickle.load( open( "ravrec/yarn_id_dict.p", "rb" ) )
    input_weight = input_weight.lower()
    yarn_list = [input_weight]
    for num,name in id_dict.items():
        if name == input_weight:
            input_id = num
    if input_id == 0:
        yarn_list.append(id_dict[1])
    elif input_id == 11:
        yarn_list.append(id_dict[10])
    else:
        yarn_list.extend((id_dict[input_id-1], id_dict[input_id+1]))
    return yarn_list

def url_to_code(url):
    split_list = url.split('https://www.ravelry.com/patterns/library/')
    return split_list[-1]

def single_pattern_request(code):
    if type(code) is not str:
        code = str(code)
    pattern_url = 'https://api.ravelry.com/patterns/{}.json'.format(code)
    pattern = requests.get(pattern_url, 
                            auth = (os.environ['RAVELRY_USERNAME'], os.environ['RAVELRY_PASSWORD']))
    return pattern.json()['pattern']

def attrs_single_pattern(pattern):
    data = pattern['pattern_categories'][0]    
    df = pd.io.json.json_normalize(data)
    df = df.filter(regex = 'permalink$', axis = 1)
    atrib_dict = df.to_dict(orient='records')[0]
    cat_list = [v for v in atrib_dict.values() if v != 'categories']
    if 'yarn_weight' in pattern.keys():
        yarn_weight = '-'.join(pattern['yarn_weight']['name'].split(' '))
    else:
        yarn_weight = None
    attr_dict = {'yarn_weight':yarn_weight,
    'pattern_attributes': [attr['permalink'] for attr in pattern['pattern_attributes']],
    'pattern_categories':cat_list}
    return attr_dict

def single_request_to_attrs(code):
    pattern = single_pattern_request(code)
    return attrs_single_pattern(pattern)

def url_to_attrs(url):
    code = url_to_code(url)
    return single_request_to_attrs(code)

def or_string(attr_list):
    return '%7C'.join(attr_list)

def fit_and_attr_split(attr_list):
    fit_name_list = ['adult','baby','child','doll-size',
 'newborn-size','preemie','teen','toddler',
 'negative-ease','no-ease','positive-ease',
 'maternity','fitted','miniature','oversized',
 'petite','plus','tall','female','male','unisex']
    attribute_list = []
    fit_list = []
    for item in attr_list:
        if item in fit_name_list:
            fit_list.append(item)
        else:
            attribute_list.append(item)
    return [fit_list, attribute_list]

def unique_search_url_section(attr_dict):
    attr_and_fit_list = fit_and_attr_split(attr_dict['pattern_attributes'])
    attr_list = attr_and_fit_list[1]
    url_sect = None
    if len(attr_list) > 0:
        attr_str = or_string(attr_list)
        url_sect = 'pa={}&'.format(attr_str)
    fit_list = attr_and_fit_list[0]
    if len(fit_list) > 0:
        fit_str = or_string(fit_list)
        fit_url_sect = 'fit={}&'.format(fit_str)
        if url_sect is not None:
            url_sect = url_sect + fit_url_sect
        else:
            url_sect = fit_url_sect
    cat_str = or_string(attr_dict['pattern_categories'][1:])
    cat_url_sect = 'pc={}&'.format(cat_str)
    url_sect = url_sect + cat_url_sect
    if attr_dict['yarn_weight'] is not None:
        yarn_list = create_yarn_list(attr_dict['yarn_weight'])
        yarn_str = or_string(yarn_list)
        yarn_url_sect = 'weight={}&'.format(yarn_str)
        url_sect = yarn_url_sect + url_sect
    if url_sect.endswith('&'):
        url_sect = url_sect[:-1]
    return url_sect

def full_search_url(url_sect):
    return 'https://api.ravelry.com/patterns/search.json?{}&sort=recently-popular&view=captioned_thumbs'.format(url_sect)

def full_website_search_url(url_sect):
    return 'https://www.ravelry.com/patterns/search#{}&sort=best&view=captioned_thumbs'.format(url_sect)

def create_search_url(attr_dict):
    url_sect = unique_search_url_section(attr_dict)
    return full_search_url(url_sect)

def create_website_search_url(attr_dict):
    url_sect = unique_search_url_section(attr_dict)
    return full_website_search_url(url_sect)

def pattern_url_to_website_search_url(url):
    attrs = url_to_attrs(url)
    return create_website_search_url(attrs)

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
          url = pattern_url_to_website_search_url(query)
      except:
          return JsonResponse({"error": "No data found for this pattern.", "result": ""})
      else: 
          return JsonResponse({"result": url, "error": ""})