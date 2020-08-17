import csv
import glob
import json
import os
import sys
import random
import threading
import time
from itertools import cycle
import dload
import re
from time import sleep
# import time
import datetime
# pip3 install selenium
# pip3 install chromedriver
# pip3 install webdriver-manager
#  pip3 install pyvirtualdisplay
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.keys import Keys  
# from selenium.webdriver.chrome.options import Options 
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from .radius import *
from .utils import create_text_file



PROXIES = [
    # 'p.webshare.io:20012',
    # 'p.webshare.io:20013',
    # 'p.webshare.io:20014',
    # 'p.webshare.io:20015',
    'p.webshare.io:20000',
    'p.webshare.io:20001',
    'p.webshare.io:20002',
    'p.webshare.io:20003',
    'p.webshare.io:20004',
    'p.webshare.io:20005',
    'p.webshare.io:20006',
    'p.webshare.io:20007',
    'p.webshare.io:20008',
    'p.webshare.io:20009',
    'p.webshare.io:20010',
    'p.webshare.io:20011',
    'p.webshare.io:20012',
    'p.webshare.io:20013',
    'p.webshare.io:20014',
    'p.webshare.io:20015',
    'p.webshare.io:20016',
    'p.webshare.io:20017',
    'p.webshare.io:20018',
    'p.webshare.io:20019',
    'p.webshare.io:20020',
    'p.webshare.io:20021',
    'p.webshare.io:20022',
    'p.webshare.io:20023',
    'p.webshare.io:20024',
    'p.webshare.io:20025',
    'p.webshare.io:20026',
    'p.webshare.io:20027',
    'p.webshare.io:20028',
    'p.webshare.io:20029',
]
PROXIES = cycle(PROXIES)
PROXY = next(PROXIES)
# Create your views here.

def faq(request):
    return render(request, 'scraper/faq.html')


def radius_check(request):
    if request.method == 'POST':
        city_name_r = request.POST.get('radius_value')
        city_list, dist_list = get_cities(city_name_r)
        city_list = zip(city_list, dist_list)
        context = {
            'city_list': city_list,
            'city_name_r': city_name_r,
        }
        return render(request, 'scraper/radius.html', context)

    return render(request, 'scraper/radius.html')


def show(request):
    if request.method == 'POST':
        file_name_r = request.POST.get('filename')
        file_path = os.path.join(file_name_r)
        if os.path.exists(file_path):

            if request.POST.get('delete_file'):
                # deleting the file
                os.remove(file_path)
                file_names = []
                for file in glob.glob("*.xlsx"):
                    file_names.append(file)
                return render(request, 'scraper/show.html', {"file_names": file_names})
            else:
                # downloading the file
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + json.dumps(os.path.basename(file_path))
                    return response

        raise Http404

    else:
        file_names = []
        for file in glob.glob("*.xlsx"):
            file_names.append(file)
        return render(request, 'scraper/show.html', {"file_names": file_names})


@csrf_exempt
def row_ajax(request):
    if request.method == 'POST':
        return HttpResponse(row_count)


pause_thread = False


def stop_scrap(request):
    if request.method == 'POST':
        if request.POST.get('stop_scrap'):
            
            stop_scraping()
            # for thread in thread_list:
            #     if thread.is_alive():
            #         print("thread still alive man. Fuck")
            return render(request, 'scraper/index.html')
        else:
            global pause_value
            pause_value = pause_scraping()  # stop the scraper

            if os.path.isfile('entry.txt'):
                f = open("entry.txt", "r")
                contents = f.read()
                context = {
                    "row_count": row_count,
                    "entry": contents,
                    "running": "True",
                    "pause_scrap": pause_value,
                }
                return render(request, 'scraper/index.html', context)

        return render(request, 'scraper/index.html')

thread_list = []
def index(request):
    if request.method == 'POST':

        global entry_r
        global choice_r

        entry_r = []
        # --------------
        multiple = False
        # --------------
        hashtag_r = request.POST.get('hashtag')
        location_r = request.POST.get('location')
        zip_r = request.POST.get('zip')
        filename_r = request.POST.get('filename')
        hashtag_list_r = request.POST.get('hashtag-list')
        tag_num_switch_r = request.POST.get('tagwithnumberswitch')
        # print(tag_num_switch_r)
        hashtag_list_r = str(hashtag_list_r)
        hashtag_list_r = hashtag_list_r.split(',')
        print(hashtag_list_r)
        
        print("number of hashtags:", len(hashtag_list_r))
        
        # added here - jesse
        # if hashtag_r != "" and zip_r != "" or location_r != "":
        # --------------
        # if len(hashtag_list_r) > 0 and location_r != "":
        #     multiple = True
        #     choice_r = "tagAndLocation"
        #     entry_r = [hashtag_list_r, location_r]
        #     print("tag and loc")
        # --------------
        # else:
        if len(hashtag_list_r) != 0:
            choice_r = "tag"
            # entry_r = hashtag_r
            entry_r.clear()
            entry_r = hashtag_list_r
        elif zip_r != "":
            choice_r = "zip"
            entry_r.clear()
            entry_r.append(zip_r)
        elif location_r != "":
            choice_r = "location"
            entry_r.clear()
            entry_r.append(location_r)
        else:
            stop_scraping()
        if request.POST.get('startscraping'):
            global row_count
            row_count = 0
            create_text_file(filename_r)

            cookie_idx = 0
            thread_idx = 0
            for entry in entry_r:
                print("entry", entry)                
                thread = threading.Thread(target=start_scraping, args=(entry, choice_r, filename_r, tag_num_switch_r, cookie_idx, thread_idx))
                thread_list.append(thread)
                cookie_idx += 1
                thread_idx += 1
            
            for thread in thread_list:
                # thread.daemon = True
                thread.start()

            if multiple is True:
                if len(entry_r) > 0:
                    # print(row_count)
                    context = {
                        "row_count": row_count,
                        "entry": entry_r[0],
                        "running": "True",
                    }
            else:
                if len(entry_r) > 0:
                    # print(row_count)
                    context = {
                        "row_count": row_count,
                        "entry": filename_r,
                        "running": "True",
                    }
                return render(request, 'scraper/index.html', context)

        elif request.POST.get('checklocation'):
            if multiple is True:
                location_list = get_location_list(entry_r[0], choice_r)
                context = {
                    "location_list": location_list,
                    "entry": filename_r,
                }
            else:
                location_list = get_location_list(entry_r[0], choice_r)
                context = {
                    "location_list": location_list,
                    "entry": filename_r,
                }
                return render(request, 'scraper/index.html', context)

        #  elif request.POST.get('checklocation'):
        #     if choice_r == "tagAndLocation":
        #         location_list = get_location_and_tag_list(entry_r[0], entry_r[1], choice_r)
        #         context = {
        #             "location_list": location_list,
        #             "entry": entry_r,
        #         }
        #         return render(request, 'scraper/index.html', context)

        else:
            pass

    else:
        if os.path.isfile('entry.txt'):
            f = open("entry.txt", "r")
            contents = f.read()
            context = {
                "row_count": row_count,
                "entry": contents,
                "running": "True",
                "pause_scrap": pause_thread,
            }
            return render(request, 'scraper/index.html', context)
        else:

            return render(request, 'scraper/index.html')


num_of_pages = 500000
row_count = 0
stop_thread = False

save_data = []
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)"

# cookie_value = [

#     'ig_did=81AB47FF-F146-46C7-9FF9-79B8B937BAF9; csrftoken=9BPcjalXIC7uqOfZg3lVJBNSxuo3NSMJ; rur=ATN; mid=Xx4WcQAEAAF6wRWyp2IAzgtRj_E2; ds_user_id=18093461285; sessionid=18093461285%3AaRAeg11INfixvN%3A4',
    
#     'ig_did=0FF09810-2E7C-45B5-ADDB-63F5CA70A89D; csrftoken=gmQ96s0J7or5bCzSiqPByCVZfRCvaYvp; rur=ATN; mid=Xx8EQAAEAAEZt5Lc1m3-7k7zp5qB; ds_user_id=28683127656; sessionid=28683127656%3AHZ2catqnwqAMiJ%3A14',

#     'ig_did=40840E02-2385-4458-91C7-F7E5658A3C2E; csrftoken=kfKVi6vtYCH9jN2m2zS5KpWpSSe9NB7S; rur=FRC; mid=XooWHgAEAAED4b4tv9gff5YRXyyT; ds_user_id=314946530; sessionid=314946530%3AIc4y0OrGbMf1Vl%3A29',
    
#     'ig_did=40840E02-2385-4458-91C7-F7E5658A3C2E; csrftoken=XHgtdBEjbTxNNvL3LZGLKc6owRWyH8Vd; rur=FRC; mid=XooWHgAEAAED4b4tv9gff5YRXyyT; ds_user_id=32815208; sessionid=32815208%3A80gtJLAEJ6oC4H%3A27',
    
#     'ig_did=40840E02-2385-4458-91C7-F7E5658A3C2E; csrftoken=WaIzlKULuffrdIomegHCDSz2p21Rs7KE; rur=FRC; mid=XooWHgAEAAED4b4tv9gff5YRXyyT; ds_user_id=39270679562; sessionid=39270679562%3Aauy0o6tEcMx4Ty%3A28',

#     'ig_did=40840E02-2385-4458-91C7-F7E5658A3C2E; csrftoken=A26cuuk1vCDgdfJAsW6Aqy6RKzmncrko; rur=FRC; mid=XooWHgAEAAED4b4tv9gff5YRXyyT; ds_user_id=19582340696; sessionid=19582340696%3A5zVLQSyAw1xx2u%3A14',

# ]


dateCounter = 0

def get_user(user_id, user_info, COOKIE):
    global PROXY, PROXIES
    user_url = "https://i.instagram.com/api/v1/users/" + user_id + "/info/"
   
    try:
        response = requests.get(user_url, headers={"cookie": COOKIE, 'User-Agent': user_agent}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})
    except:
        PROXY = next(PROXIES)
    user_data = json.loads(response.text)

    username = user_data['user']['username']
    follower_count = user_data['user']['follower_count']
    try:
        public_email = user_data['user']['public_email']
    except:
        public_email = ' '
    full_name = user_data['user']['full_name']
    igURL = 'https://www.instagram.com/' + username + '/'

    # user_info.extend([username, userFirstName, userLastName, public_email, followers, following, external_url, numberOfPosts, igURL])
    user_info.extend([username, full_name, public_email, follower_count, igURL])
    return user_info, username
        # print(
        #     "ID: " + user_id + " " + "Username : " + username + " " + str(score))



def start_scraping(entry, choice, filename_r, tag_num_switch_r, cookie_idx, thread_idx):
    cookie_value = [
        [
            # 'csrftoken=dRTsYWvytntVWd95FuKdxrYDtn7PA5DC; ds_user_id=39486888671; sessionid=39486888671%3AZuNI7wSCeHb2Kd%3A6',
            # 'csrftoken=smNb8Cc0KA3GeSPXdpPHm4lWrKvC7ubf; ds_user_id=39840629093; sessionid=39840629093%3AAfskgsIQWBtlsB%3A2',
            # 'csrftoken=Rb3nutdMwMhny6hERsJezPpl6APEo1qo; ds_user_id=39446071257; sessionid=39446071257%3AruZi3w7OV1YRc6%3A19',
            # 'csrftoken=5eyKyB44fL9X5RSzXQ7Pi859CIJUTnu7; ds_user_id=39662219772; sessionid=39662219772%3Aaenim4gUsEXDTW%3A11',
            # 'csrftoken=UJt5EbhILZHM3OQZzNOQiOezOfwJaW9C; ds_user_id=39263989296; sessionid=39263989296%3AnZfa8BKqZlqZrA%3A6',
            # 'csrftoken=L8dkxORCfKf0zofmrgBq8SgDDJM9oK1y; ds_user_id=39465292199; sessionid=39465292199%3Ai8WCvXZWqi7HfD%3A6',
            'csrftoken=Q7L5HPRjQnOnzYFD4T6buXsNXdEH3fsq; ds_user_id=39855219675; sessionid=39855219675%3AxipHZOd9q9Y8RR%3A23',
            'csrftoken=kq6Cgn0xgQyoZe4FBucjwvcMsLtgnlkY; ds_user_id=39861002518; sessionid=39861002518%3ADv2Hd1oowRHt9Y%3A16',
            'csrftoken=yhANPWS0s2kVVibreN3ONqUMVCWXDBS6; ds_user_id=39064067168; sessionid=39064067168%3AnRIhC5zG9IHZOe%3A9',
            'csrftoken=jvuGItawYgl3QIVN4xjYbIk7TAXptIYF; ds_user_id=39449198551; sessionid=39449198551%3A2ZL3pp4L9XFFvS%3A27',
            'csrftoken=BLNAkvsksxnH2ZtpCGi24VFXNQHBNAQ2; ds_user_id=39844036345; sessionid=39844036345%3AXIcYZWSOWmxdT1%3A2',
            'csrftoken=HYOuPVDt8cR2aq6hgTe4KfST0vdfwVUA; ds_user_id=39660588055; sessionid=39660588055%3Aazb9UFJj4aEK3x%3A27',
            # 'csrftoken=QVwvyUNRpRyaVGvCWmzPZcsHMO4t4PNQ; ds_user_id=39054021672; sessionid=39054021672%3Au8ZkG0fwRrCIt2%3A20',
            # 'csrftoken=XcBC3Ll6Xc8o9tu8GleErAZksKTeIrfz; ds_user_id=39857795293; sessionid=39857795293%3AuLfrdGiFTQ69oM%3A27',
            # 'csrftoken=qwckkKm4Y2TJfXamIBID3IcNyeepdSAH; ds_user_id=39678472611; sessionid=39678472611%3AaMffztqoPSpTGN%3A5',
            # 'csrftoken=KwMzi2N2WO9eR97qrO3HrjbfU3GxTH0u; ds_user_id=39866417292; sessionid=39866417292%3Av0ldVwyQLT3Tdo%3A22',
            # 'csrftoken=2toSvJDqDHyPLjIjfFG7cTl3sJw2tBLM; ds_user_id=39267340409; sessionid=39267340409%3AWKSdrMW99rlkBO%3A7',
            # 'csrftoken=UgxQOmiN2vapXUpKVk1KOz1rKCIEvxaV; ds_user_id=39472210860; sessionid=39472210860%3AXCGJJZMLxczC2g%3A27',
            'csrftoken=fRAUYpcLxaGMWfDKpEmeuRmI2pRfQIgg; ds_user_id=39069778187; sessionid=39069778187%3AX1qoTROSbLdiiP%3A22',
            'csrftoken=oHje4nsG76djd6WAyNVb7c6qFeiqEc39; ds_user_id=39647230311; sessionid=39647230311%3A6ZBA1KfJ3UedVh%3A2',
            'csrftoken=UdNr6Hnk1emJQud4EKZ45unp3SiLTivP; ds_user_id=39655580572; sessionid=39655580572%3ARIf4YBOm2MUkBU%3A29',
            'csrftoken=hTHVk9e41tFsjP28yNRaMWWAaeKXylqh; ds_user_id=39669609943; sessionid=39669609943%3APNvcwmH86OAsHN%3A5',
            'csrftoken=SiU6H9WibnKVKW0iA3k3qkAJ7sJ2bDGY; ds_user_id=39455549808; sessionid=39455549808%3AmAmHXE8RxdKcJX%3A17',
            'csrftoken=QnWHe1r8j3WdW83wXQytzDfih1F4jIOg; ds_user_id=39667578984; sessionid=39667578984%3AfkdBiWuwa9JmKx%3A2',
            # 'csrftoken=MrbhIadB1grwA3o36JrvTE3Ts3vFza1O; ds_user_id=39257878272; sessionid=39257878272%3AchtN56C0UMPxwM%3A5',
            # 'csrftoken=DG1HgyV56sMDEQoHCtgcdHjTDHI66wq0; ds_user_id=39279928812; sessionid=39279928812%3A8gLBysJStnV2RI%3A3',
            # 'csrftoken=dV5QwJCF2vykCirJxUuX384HFZoLGhCH; ds_user_id=39069634614; sessionid=39069634614%3Arq92KZJWUfALYq%3A17',
            # 'csrftoken=y7I0FOXIMrbJSeC8EaLXrpX1Cv3WNcVa; ds_user_id=39842644448; sessionid=39842644448%3A81SmZdsfwxv6UY%3A22',
            # 'csrftoken=k91DCQzgF3uXnoG75EyLlQ3cmB2V3FRD; ds_user_id=39471579390; sessionid=39471579390%3AnPEeJEVZx4Bj2L%3A21',
            # 'csrftoken=nwm3lfeqQhi5vx93CdVwMosvsSuJAe8K; ds_user_id=39065259163; sessionid=39065259163%3AzjiqNblcazL7xt%3A1',
        ],
        [
            'csrftoken=t7jPJ7fSZ6WaV2IMGAUTahu8ElO4lxFB; ds_user_id=39451598641; sessionid=39451598641%3ABvhNle9CPS9JlY%3A4',
            'csrftoken=s6a1mhmUXi3X8p4YC7DkUXb7va6wFPPG; ds_user_id=39284536589; sessionid=39284536589%3AXX5tAgdYdbJNcC%3A15',
            'csrftoken=2BpiQdr69qbTuPPPJi5QVzkrKqkGLyFB; ds_user_id=39669058838; sessionid=39669058838%3AEfW2OJOgSvFsl1%3A5',
            'csrftoken=A90LqZ0TndNcngrw7lqaPhe0Bg3uwQNZ; ds_user_id=39465012861; sessionid=39465012861%3AODs2NtQRrnIfg9%3A8',
            'csrftoken=uVdfA16BHoMcHKKaGBwUGM1HR7c1ivqi; ds_user_id=39047823261; sessionid=39047823261%3AYiALLuIBda3oEj%3A7',
            'csrftoken=FWsbltPD7W4iLm1PIzWosYFlsLQz1yzn; ds_user_id=39655637062; sessionid=39655637062%3AezwGIfwBkznbBm%3A12',
            'csrftoken=heiu3WMQIWAilPYiRs6ieMdYQrEnaaeD; ds_user_id=39670066342; sessionid=39670066342%3AKOuVF4qOaBB6eM%3A14',
            'csrftoken=3Ib6pA54N6Vr4S1usPx58PeQXVqBKe5g; ds_user_id=39278361521; sessionid=39278361521%3ALqbIPWZf5ncH45%3A11',
            'csrftoken=uriCRD19tQubr0wo1OoY3vwWCt8Ib5Yh; ds_user_id=39859787060; sessionid=39859787060%3AllsvUZuYgnrRWA%3A15',
            'csrftoken=w9wn4H37hvL9yTZ4ZyvEKpaQ8A7Ug9fl; ds_user_id=39279057474; sessionid=39279057474%3AaOauIBCZWMONWF%3A14',
            'csrftoken=Ll9telbYOKBP3Y3hw4iKaItJdNOYt2dy; ds_user_id=39487384591; sessionid=39487384591%3AUcJRvwAwWOCfVz%3A18',
            'csrftoken=I2wnEP11tYkU03JfQbS5hNAxA9rUWRtj; ds_user_id=39865729360; sessionid=39865729360%3Agg2EiQ4MrQ0tku%3A20',
        ],
        [
            'csrftoken=KTheciU22YaBwq17mQ16b5dExa7gDHUv; ds_user_id=39254575000; sessionid=39254575000%3Am5JTYF3An2AUFm%3A10',
            'csrftoken=dV3ColH9l26LyPxKZXd9yhoft9sCCDr4; ds_user_id=39669570334; sessionid=39669570334%3A9iQhHT0WamnALj%3A26',
            'csrftoken=6fp8pOzkOageySphTXFJiIYgRA9ojgbf; ds_user_id=39068898101; sessionid=39068898101%3AoyisXJgaE8NHm5%3A13',
            'csrftoken=vPvef30ibbAC0MTSefd4XOI7GLlkw3q8; ds_user_id=39063259489; sessionid=39063259489%3A1k4IMeYhznyAt3%3A28',
            'csrftoken=AvkSZDaCANaur0VXdn3alHbuDoE9GxIw; ds_user_id=39460549353; sessionid=39460549353%3ABiSFpoANcnKTh1%3A25',
            'csrftoken=gXmZhgK9VRTeJjG5xECw2DvaWU96v6FF; ds_user_id=39649101802; sessionid=39649101802%3AbrL4bWJw4apRt2%3A29',
            'csrftoken=AggA1ZVy3qnZ0IkhPrdWF8TdOptkrgBR; ds_user_id=39457741774; sessionid=39457741774%3Acga3xqEdr3r17d%3A8',
            'csrftoken=5bx0Z7VcucnWMBty5iaYHxUVmWHTFK1w; ds_user_id=39855963639; sessionid=39855963639%3A83tXUoLVGuKWJV%3A11',
            'csrftoken=6DA39i3VW8hi28kvTXyq7IepCLkMw0I8; ds_user_id=39456469887; sessionid=39456469887%3AypWXH5Y9RnPaMx%3A7',
            'csrftoken=uYI6N54pL2kXQxejuhTO5k4KWhVM6Kcr; ds_user_id=39051238222; sessionid=39051238222%3AE5qHGnix5nDxn8%3A1',
            'csrftoken=ea698pp13dIlxamRjAMctE8vuEDHGBMH; ds_user_id=39872704378; sessionid=39872704378%3AUWXbGTG4rpx3W0%3A26',
            'csrftoken=qUHuyfjbu79Mfnj2uYYixoNKA79rJw7H; ds_user_id=39857091061; sessionid=39857091061%3AqOnwqQs1DXsErE%3A6',
        ],
        # [
        #     'csrftoken=5BFl3rlvdYF33D1xjvpVao2pKD5DcHxd; ds_user_id=39472026907; sessionid=39472026907%3AMt2mOdJC6dSAZw%3A21',
        #     'csrftoken=Fq1IdTT3BFLUI21Lxbngeci6uaFJ5Pnr; ds_user_id=39487272621; sessionid=39487272621%3APKJ0OMxUY0gKrH%3A1',
        #     'csrftoken=DMJdawaQvmTnGTWXjvbZQRyhS7pNpA56; ds_user_id=39250847597; sessionid=39250847597%3AA61HMyjlQoWfRK%3A20',
        #     'csrftoken=mPdrYaWfiDRMtsqF1NpvWJRkf5HcfwwA; ds_user_id=39050254424; sessionid=39050254424%3AH3bTuhxSmZ2Pxm%3A15',
        #     'csrftoken=8XGyx6T5yR1gucRpbM6BxRPEfhXEtoBf; ds_user_id=39841829113; sessionid=39841829113%3A4Q94q9xghVVxUa%3A16',
        #     'csrftoken=SmYpjm20NN9W7GB17PYZvTKv2Vfk2MfM; ds_user_id=39264005111; sessionid=39264005111%3AtEWhqNgnWBbmuL%3A5',
        # ],
        # [
        #     'csrftoken=AqFM7aipU7OulBgYzTUhokwz8gNw4VqE; ds_user_id=39448830531; sessionid=39448830531%3Az3YlYSXvkcAIlZ%3A14',
        #     'csrftoken=KB5iD86WNWBxRNS04wtbwI0Jf7OJTmKc; ds_user_id=39272330864; sessionid=39272330864%3Aad2rmewRzaK815%3A26',
        #     'csrftoken=taYLqWZc041jMO7Xv2oIHKHIu80qmZo5; ds_user_id=39634999781; sessionid=39634999781%3AOxksWcaOHjInkW%3A18',
        #     'csrftoken=51Y1daX1QQMtO6gwOdFAlsik4HxGzZFV; ds_user_id=39470115359; sessionid=39470115359%3AzcZmEEG6gCHDH2%3A14',
        #     'csrftoken=iKshrJoucI2Su4UvPRMkjPmvhWgmy7tI; ds_user_id=39640791110; sessionid=39640791110%3AedPChQVSDKc7N2%3A7',
        #     'csrftoken=DOoGgdbvNEnyb7MlPoVBuNWa4IzhBdN4; ds_user_id=39056125350; sessionid=39056125350%3ASqaiPCcI9HbTsZ%3A25',
        #     'csrftoken=XyupD9RQoIebQYcVtxNEspMv7MWFiOzy; ds_user_id=39487520914; sessionid=39487520914%3AzWwICSyPh0p59y%3A3',
        #     'csrftoken=bAbWIo7hDed6k0QYoOoeitKJyYqD9B7z; ds_user_id=39449310383; sessionid=39449310383%3AlfEXUnd8volHXg%3A28',
        #     'csrftoken=luuCslrvDnYePdaldrav04lhv3q1b6MH; ds_user_id=39069794204; sessionid=39069794204%3Ay3WABa8Bkl9RGn%3A28',
        #     'csrftoken=jmhPZoAbn9LOsBKyCcbLgJw4A0djCIRg; ds_user_id=39052006215; sessionid=39052006215%3A8baapjGJZ6bhWr%3A14',
        #     'csrftoken=2MRdRtEB8DCHoE9VFTH8hyr4yFoRPdip; ds_user_id=39056069749; sessionid=39056069749%3A5ZeEwhh9OhdoKf%3A0',
        #     'csrftoken=qxOogADgm6gbE9UHR42SQrYrVV7emRXc; ds_user_id=39644006622; sessionid=39644006622%3AiMY4HaQg4iXJNz%3A21',
        # ],
        # [
        #     'csrftoken=Zm4w7SFDjA1exCGlDn2GKpBd5Xj2BN0e; ds_user_id=39637367591; sessionid=39637367591%3AyotgmN44NvObMl%3A5',
        #     'csrftoken=hTEgbMTxv953pcbk1GcrHARx0jsqbHo0; ds_user_id=39486808617; sessionid=39486808617%3AiBBuFlwOZsJPi5%3A16',
        #     'csrftoken=4crFiu06r2QI5NRVLwoPlISNCqkwafjd; ds_user_id=39251463602; sessionid=39251463602%3Al5zoLZuYvgs8eK%3A3',
        #     'csrftoken=wApRLMFLrArwp3dhKzjnzcOr5x0zgHwq; ds_user_id=39060500155; sessionid=39060500155%3AwahheyOcBqHmwj%3A5',
        #     'csrftoken=NMYiI1J5GdxsUJIq3xjDzQrSTEnllAdm; ds_user_id=39044015985; sessionid=39044015985%3AsyPDqdzLUJEeqZ%3A22',
        #     'csrftoken=fcxEG6rsI7usmmlzrRu0LGnzu2gZA6PX; ds_user_id=39047679093; sessionid=39047679093%3AnMYecZkVtnOjAC%3A26',
        #     'csrftoken=diLnfozPgfvgMg4eGytCivFa5004NFXn; ds_user_id=39070690139; sessionid=39070690139%3AzATOaT1LLCSoG7%3A25',
        #     'csrftoken=90y2stI6cgwluwv4L1SHlDgzId27WVIH; ds_user_id=39467883648; sessionid=39467883648%3A3pYlfYKiBqOmmn%3A10',
        #     'csrftoken=Am8ANuKoGK2UagiNmWSrwfBjxL70Z9cu; ds_user_id=39678088451; sessionid=39678088451%3APGdR0aQCe0DgUm%3A3',
        #     'csrftoken=sMWHmF6eUlFvr4vYn33ssHSgIyXAfUqV; ds_user_id=39843972795; sessionid=39843972795%3AZIklqQZujSJMSL%3A12',
        #     'csrftoken=PrFuDg5BXwoetJg3fN61M7R4cWu7jrLl; ds_user_id=39272963183; sessionid=39272963183%3ApQE6F6TOJmwBgR%3A10',
        #     'csrftoken=bdKk66h8bJ3DRwX2kyOaIXykj6ANBqmK; ds_user_id=39643534571; sessionid=39643534571%3ANdCW8JgsSagp8I%3A8',
        # ],
        # [
        #     'csrftoken=oW3NeGHNFwuUd5IAI6sTXil2WpmbM5vY; ds_user_id=39253303204; sessionid=39253303204%3A0QkdKeVTH64Gtw%3A27',
        #     'csrftoken=xOKG0R9ora4WRBd6zYerBLYwwv310AKl; ds_user_id=39674992869; sessionid=39674992869%3AqSbDTQVVjlh6bM%3A23',
        #     'csrftoken=s3l91ks3c9QLJJJ5BaKDGEePIJxMQjVu; ds_user_id=39259566268; sessionid=39259566268%3AE3i3kN9Roqfl9B%3A29',
        #     'csrftoken=e0COTm5AZEZCcWczNAJqZcoDH4r2mRW3; ds_user_id=39257902405; sessionid=39257902405%3A0T61ACIzO9pMn5%3A15',
        # ]
    ]

    COOKIES = cycle(cookie_value[cookie_idx])
    # print(choice)
    # print("switch", tag_num_switch_r)
    global workbook_name, COOKIE, dateCounter
    workbook_name = filename_r + ".xlsx"
    # if choice is 'tagAndLocation':
    #     workbook_name = entry[0] + "_" + entry[1] + ".xlsx"
    # else:
    #     workbook_name = entry + ".xlsx"
    global row_count
    row_count = 0
    end_cursor = ''
    location_id = None
    # entryChosen = entry
    abort = False
    # if choice is 'tagAndLocation':
    #     print("tag and location chosen")
    if choice is 'tag':
        print("tag chosen")
    if choice is "location":
        location_id = get_location_id(entry)
        print("location id", location_id)
    if choice is 'zip':
        location_name = get_location_name(entry)
        if location_name is None:
            abort = True
            print('Zipcode 404')
        if abort is False:
            location_id = get_location_id(location_name)

    # sys.exit()
    if abort is False:
        for page in range(num_of_pages):
            COOKIE = next(COOKIES)
            # print(COOKIE)
            entryChosen = None
            try:
                # if entry == "" and location_id == None:
                #     print("scraping stopped")
                #     stop_scraping()

                if page == 0:
                    if choice is "tag":
                        entryChosen = entry.replace(" ", "")
                        url = "https://www.instagram.com/explore/tags/" + entryChosen + "/?__a=1"

                    else:
                        url = "https://www.instagram.com/explore/locations/" + location_id + "/?__a=1"

                else:
                    if choice is "tag":
                        entryChosen = entry.replace(" ", "")
                        url = "https://www.instagram.com/explore/tags/" + entryChosen + "/?__a=1&max_id=" + end_cursor
                    else:
                        url = "https://www.instagram.com/explore/locations/" + location_id + "/?__a=1&max_id=" + end_cursor

                # print(url)
                print("REQUEST COOKIE", COOKIE)
                r = requests.get(url, headers={"cookie": COOKIE, "User-Agent": user_agent}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

                if r.status_code != 200:
                    print(r.status_code)
                    print("No Posts found. Please Stop scraping before starting a new search")
                    sys.exit()
                    continue

                # print(r.text)
                data = json.loads(r.text)
                
                if choice is "tag":
                    edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges']  # list with posts
                else:
                    edges = data['graphql']['location']['edge_location_to_media']['edges']  # list with posts

                for item in edges:
                    COOKIE = next(COOKIES)
                    # print(COOKIE)
                    if stop_thread is True:
                        return
                    while pause_thread:
                        pass

                    try:
                        start_time1 = time.time()
                        post = (item['node'])
                        owner = post['owner']
                        user_id = owner['id']
                        shortcode = post['shortcode']
                        location = get_location(shortcode)

                        user_info = []
                        print("USER INFO COOKIE", COOKIE)
                        info, username = get_user(user_id, user_info, COOKIE)
                        # print(COOKIE)
                        if choice is "tag" or choice is "tagAndLocation":
                            # print("tag or tag and loc")
                            if str(tag_num_switch_r) == "true":
                                # print("tag switch true")
                                COOKIE = next(COOKIES)
                                print("FUTURE DATE COOKIE", COOKIE)
                                future_date = get_future_date(shortcode, entryChosen, COOKIE)
                                if future_date is None:
                                    dateCounter += 1
                                    if dateCounter > 5:
                                        thread_list[thread_idx].join()
                                        thread_list[thread_idx] = None
                                        # stop_scraping()
                                else:
                                    dateCounter = 0
                                print("date counter", dateCounter)
                                info.extend([future_date, entryChosen])
                                
                        print(info)
                        print("--- %s seconds | User Time ---" % round(time.time() - start_time1, 2))
                        start_time2 = time.time()
                        # print("test 11")
                        if len(info) != 0:
                            # print("22")
                            move_to_excel(info, location, entryChosen)
                            row_count += 1
                            print(row_count)

                        print("--- %s seconds --- | Excel time" % round(time.time() - start_time2, 2))

                    except Exception as e:
                        print(e)
                        # sys.exit()
                        

                if choice is "tag":
                    end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']  # value for the next page
                else:
                    end_cursor = data['graphql']['location']['edge_location_to_media']['page_info']['end_cursor']  # value for the next page
                if end_cursor is None or end_cursor == "":
                    stop_scraping()
                    return

            except Exception as e:
                # sys.exit()
                print(e)
                # stop_scraping()


def get_future_date(shortcode, tagwithnumber, COOKIE):

    print("get future date")
    user_url_data = "https://www.instagram.com/p/" + shortcode + "/?__a=1"
    daysTotalPregnant = 280

    numberStr = ""
    for i in range(len(tagwithnumber)):
        if tagwithnumber[i].isdigit():
            numberStr += tagwithnumber[i]
    if numberStr == "":
        return None
        
    tagWeek = int(numberStr)
    tagDays = tagWeek * 7
    # switch_count = 0
    # while switch_count < 5:
    # print(f'SWITCH COUNT SWITCH COUNT {switch_count}')
    try: 
        data_response = requests.get(user_url_data, headers={"cookie": COOKIE, 'User-Agent': user_agent}, timeout=10)
        # break
    except:
        PROXY = next(PROXIES)
    #     switch_count+=1
    # if switch_count == 5:
    #     return None
        # print(cookie)

    data = json.loads(data_response.text)
    timestamp = data['graphql']['shortcode_media']['taken_at_timestamp']

    
    

    postDate = datetime.datetime.fromtimestamp(timestamp)
    postDateList = [postDate.month, postDate.day, postDate.year]
    postDayOfYear = dayOfYear(postDateList[0], postDateList[1], postDateList[2])

    todaysDate = datetime.datetime.today()
    todayDayList = [todaysDate.month, todaysDate.day, todaysDate.year]
    todayDayOfYear = dayOfYear(todayDayList[0], todayDayList[1], todayDayList[2])

    daysSincePost = todayDayOfYear - postDayOfYear
    daysPreg = daysSincePost + tagDays
    daysLeft = daysTotalPregnant - daysPreg
    formatedDaysLeft = datetime.timedelta(days=daysLeft)

    dueDate = todaysDate + formatedDaysLeft
    dueDayOfYear = dayOfYear


    daysRemaining = (dueDate - todaysDate).days
    if daysRemaining < 0:
        return None
    # projectedDueDayOfYear = todayDayOfYear + daysLeft
    # print(todayDayOfYear)
    # print(postDayOfYear)
    # print(daysPreg)
    # print(daysLeft)
    # print(dueDate.date())
    # print('day of year', todayDayOfYear)
    
    
    # user_info.extend([dueDate])
    return str(dueDate.date())
    
    # -------------------------
    # -------------------------

def dayOfYear(month, day, year):
    # date = '%s-%s-%s' % (year, month, day)
    days = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    # d = list(map(int, date.split("-")))
    d = [year, month, day]
    if d[0] % 400 == 0:
        days[2]+=1
    elif d[0]%4 == 0 and d[0]%100!=0:
        days[2]+=1
    for i in range(1,len(days)):
        days[i]+=days[i-1]
    return days[d[1]-1]+d[2]

def get_location(shortcode):
    r = ""
    try:
        url = "https://www.instagram.com/p/" + shortcode + "/?__a=1"
        try:
            r = requests.get(url, headers={"cookie": COOKIE}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})
        except Exception as e:
            print(e)
            get_location(shortcode)

        data = json.loads(r.text)
        try:
            location = data['graphql']['shortcode_media']['location']['name']  # get location for a post
        except:
            location = ''  # if location is NULL
    except:
        location = ''

    return location
    # print(location)


def move_to_excel(data, location, tag):
    try:
        data.insert(0, location)
        save_data.append(data)
        if row_count % 100 == 0:

            # print("Storing data in bulk YOLO")
            # headers = ['Location','Username','First Name', 'Last Name', 'Public Email', 'Followers', 'Following', 'External URL', 'Number of Posts', 'Profile URL', 'Due Date', 'Tag']
            headers = ['Location','Username','Full Name', 'Public Email', 'Followers', 'Profile URL', 'Due Date', 'Tag']
            
            if row_count % 100000 == 0 and row_count > 0:
                global counter
                counter += 1
                global workbook_name
                workbook_name = tag + str(counter) + ".xlsx"

            global wb
            if os.path.isfile(workbook_name):
                wb = load_workbook(filename=workbook_name)
                sheet = wb.active
            else:
                wb = Workbook()
                sheet = wb.active
                sheet.append(headers)
                for cell in sheet["1:1"]:
                    cell.font = Font(bold=True)

            for d in save_data:
                sheet.append(d)

            sheet.column_dimensions['A'].width = 30
            sheet.column_dimensions['B'].width = 30
            sheet.column_dimensions['C'].width = 20
            sheet.column_dimensions['D'].width = 20
            sheet.column_dimensions['E'].width = 30
            sheet.column_dimensions['F'].width = 10
            sheet.column_dimensions['G'].width = 10
            sheet.column_dimensions['H'].width = 30
            sheet.column_dimensions['I'].width = 10
            sheet.column_dimensions['J'].width = 30
            sheet.column_dimensions['K'].width = 30
            sheet.column_dimensions['L'].width = 30

            wb.save(filename=workbook_name)
            save_data.clear()

    except Exception as e:
        print(e)


# sheet.cell(row=row_num + 1, column=1, value=location)
# for i in range(0, 4):
#     sheet.cell(row=row_num + 1, column=i + 2, value=data[i])


def get_location_id(entry):
    location_id = None
    get_location_id_url = "https://www.instagram.com/web/search/topsearch/?context=blended&query=" + entry + "&rank_token=0.20850940886082237&include_reel=true"
    req = requests.get(get_location_id_url, headers={"cookie": COOKIE}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

    location_data = json.loads(req.text)
    places = location_data['places']
    for place in places:
        location_id = place['place']['location']['pk']
        break
    return location_id


def get_location_name(entry_now):
    with open('zip_code_database.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                pass
            else:
                if entry_now == row["zip"]:
                    return row["primary_city"]
            line_count += 1
    return None

def get_location_list(entry, choice):
    location = entry
    if choice == "zip":
        location = get_location_name(entry)
        if location is None:
            return None

    get_location_id_url = "https://www.instagram.com/web/search/topsearch/?context=blended&query=" + location + "&rank_token=0.20850940886082237&include_reel=true"
    req = requests.get(get_location_id_url, headers={"cookie": COOKIE}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

    location_data = json.loads(req.text)
    places = location_data['places']
    place_count = 1
    location_list = []
    for place in places:
        location_name = place['place']['location']['name']
        location_list.append(location_name)
        place_count += 1

    return location_list


def stop_scraping():
    
    global stop_thread
    stop_thread = True
    for thread in thread_list:
        thread.join()
    thread_list.clear()
    # deleting the location file - location.txt
    if os.path.isfile('entry.txt'):
        os.remove("entry.txt")

    try:

        # headers = ['Location','Username','First Name', 'Last Name', 'Public Email', 'Followers', 'Following', 'External URL', 'Number of Posts', 'Profile URL', 'Due Date', 'Tag']
        headers = ['Location','Username','Full Name', 'Public Email', 'Followers', 'Profile URL', 'Due Date', 'Tag']
        global wb
        if os.path.isfile(workbook_name):
            wb = load_workbook(filename=workbook_name)
            sheet = wb.active
        else:
            wb = Workbook()
            sheet = wb.active
            sheet.append(headers)
            for cell in sheet["1:1"]:
                cell.font = Font(bold=True)

        for d in save_data:
            sheet.append(d)

        sheet.column_dimensions['A'].width = 30
        sheet.column_dimensions['B'].width = 30
        sheet.column_dimensions['C'].width = 20
        sheet.column_dimensions['D'].width = 20
        sheet.column_dimensions['E'].width = 30
        sheet.column_dimensions['F'].width = 10
        sheet.column_dimensions['G'].width = 10
        sheet.column_dimensions['H'].width = 30
        sheet.column_dimensions['I'].width = 10
        sheet.column_dimensions['J'].width = 30
        sheet.column_dimensions['K'].width = 30
        sheet.column_dimensions['L'].width = 30

        wb.save(filename=workbook_name)
        save_data.clear()
        stop_thread = False
    except:
        print("Save failed")


def pause_scraping():
    global pause_thread
    if pause_thread:
        pause_thread = False
    else:
        pause_thread = True

    return pause_thread
