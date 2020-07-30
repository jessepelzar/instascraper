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
    # 'p.webshare.io:19999',
    'p.webshare.io:20012',
    'p.webshare.io:20013',
    'p.webshare.io:20014',
    'p.webshare.io:20015',
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
           
            for entry in entry_r:                
                thread = threading.Thread(target=start_scraping, args=(entry, choice_r, filename_r, tag_num_switch_r))
                thread_list.append(thread)
            
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
                        "entry": entry_r[0],
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

cookie_value = [

    # 'ig_did=81AB47FF-F146-46C7-9FF9-79B8B937BAF9; csrftoken=9BPcjalXIC7uqOfZg3lVJBNSxuo3NSMJ; rur=ATN; mid=Xx4WcQAEAAF6wRWyp2IAzgtRj_E2; ds_user_id=18093461285; sessionid=18093461285%3AaRAeg11INfixvN%3A4',
    
    # 'ig_did=0FF09810-2E7C-45B5-ADDB-63F5CA70A89D; csrftoken=gmQ96s0J7or5bCzSiqPByCVZfRCvaYvp; rur=ATN; mid=Xx8EQAAEAAEZt5Lc1m3-7k7zp5qB; ds_user_id=28683127656; sessionid=28683127656%3AHZ2catqnwqAMiJ%3A14',


    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=CW8as8P0qcxbF2gKiebKs4KEtnCfF9Sc; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=18070511049; sessionid=18070511049%3AE4dnz7ZO7jA3Ax%3A27',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=VXtk0he5e2szTN2CfXVO28WiJLBj2tCB; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=18262161604; sessionid=18262161604%3AJsYudrYQQoZk0u%3A5',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=OZ8NSndnxPDH6r3jWefl9lGuo22eXL8e; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=18096204756; sessionid=18096204756%3ACeruR35ml0RRER%3A4',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=1PGOieyCYaTB3gGBAKfKHFJIyTCqf91n; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=18093461285; sessionid=18093461285%3Adplflhi2jpxBW5%3A10',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=TbKAVW0UxUhB3HY9WwqJS6vKBmjaXS0W; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=11835832380; sessionid=11835832380%3AMoTz7jzWfC52fx%3A11',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=gHJD0fg4Vz5tdc6yzCG9xJhstyKMCDdW; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20250630209; sessionid=20250630209%3ARq0cfvo7bfvDsM%3A22',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=n8wB9LAiXLtN6h4r3w0PEuC4Jbr3ag8s; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20296395013; sessionid=20296395013%3A9T4jn3837WSs7n%3A8',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=0QlUH2DKQaSckRLF6wf3pawdV67JAAfM; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20251277674; sessionid=20251277674%3AjKg5GdqEwUUPIQ%3A25',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=B3wTeNr5Fg7YN8mH8xGuPzPLUqGVo00k; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28878069841; sessionid=28878069841%3ALZRldEXYgS8CcV%3A16',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=tmJyZndMnELn6Byx05RJ84qDMeoQudbU; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28694253617; sessionid=28694253617%3Al5FWPZ6vBgIwH0%3A28',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=cHGGIt52YwWUCZHVInGPDLUXWvrSvN4E; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29067884570; sessionid=29067884570%3AlTk26WBs1XPQJ4%3A6',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=VaamVIDOXS73ejQEsvSmMZV2UDDUqhqG; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29099456467; sessionid=29099456467%3AZvlIXMisOHdXgu%3A26',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=zLSrw1GcsZH7gq7ZkrCaNqnJ7Kd0pSD0; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29076243614; sessionid=29076243614%3AqGEaHufL7g4LRx%3A12',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=QZxGYcaQYCuQ7sfayIdpSQvVzpkV6BoP; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28514517496; sessionid=28514517496%3Ak2euuwRphNCBpI%3A29',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=wmRe9lv2F2GP6BbJ2cHaQQdI7kyR80hD; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28683127656; sessionid=28683127656%3APJmCapkgP1Cs4v%3A3',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=o1JCCUNRhg17mn6KDB4CaUOHKLuWsqKc; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28870662934; sessionid=28870662934%3AUSZzjytY6wgF29%3A19',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=64rKG5AB9O0vUQQkInETUIOw5eQlx0Ie; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29062029694; sessionid=29062029694%3AsiI5BQ8znQSfOP%3A5',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=C2JXmESxShKKudfCapAeKw1kXyS5qlqu; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29102216191; sessionid=29102216191%3AsorSZaC7pNXMQ9%3A28',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=bnBBqV9cOrWDpMVSNUG2kfaPB6iOe5Gr; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29084834611; sessionid=29084834611%3Aj5TIJPs8g7EQjA%3A28',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=jWlIAJ0wj9txMerrZquFOOnTCJNdINeY; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=29068268874; sessionid=29068268874%3AafD3vXRpDOcuIx%3A8',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=UwHcGJBjfmtMEMjhnW1VerKydS9B3MXv; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28888788623; sessionid=28888788623%3ACztpcwhrsb4xuB%3A15',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=0BKOvRT1AOhmT4F49rgLCFgqAFynwOYo; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20271859208; sessionid=20271859208%3AkMhWOxdtG0j7oy%3A0',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=kyErXkjs6iVr8kvkZCxphnyUqDIXbm1H; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20230623790; sessionid=20230623790%3AtYJNSknx73BytE%3A4',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=Rl9l5Sm4zYE4I83x6RkCTiIZUT89gGCW; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20477224439; sessionid=20477224439%3Ap2VABKuoG1IVab%3A14',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=NZh1Iooc4dGutC28qnxNYYDvEHxvCt9u; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=20476600456; sessionid=20476600456%3AkE7LS95wqvJuav%3A25',
    'ig_did=414B6125-6E04-416D-8F13-E84D3C0AAE64; csrftoken=28AgcxZLSqYLQ17pDa8si4iA96pJmqzY; rur=FRC; mid=W4mzAAALAAGfHuZyx_NZjzDM6FU-; ds_user_id=28729779488; sessionid=28729779488%3AHVf41ktUm8FAZg%3A10',
]

# cookie_value = [

#     'ig_did=E47FEC0C-30C6-472F-A9FC-0C1123F77B15; csrftoken=4NYlt3ps9weBjjQdupkFy7uGu3SYDImC; rur=ATN; mid=Xi9XzAALAAGmbiNZxhWMQWvdXAyw; ds_user_id=28683127656; sessionid=28683127656%3Arncw1sq26MLYf3%3A13',

#     'ig_did=33C11652-D6BA-4024-B66A-B54989AD7D4B; csrftoken=KRsKBnMKpZLkicXiFKq0xUnQZMEFxzOp; rur=FRC; mid=Xi9YcQALAAEwBFt_BXZeJ0Pvd7-P; ds_user_id=28870662934; sessionid=28870662934%3AnVnrQVTqTrT4nE%3A11',

#     'ig_did=0786D9EE-CD88-4F10-A7D3-F0D87130E4A8; csrftoken=ByB5JuP5vwfzQD46gorGEA7RtsdjAeEk; rur=FRC; mid=Xi9YxgALAAGc0eoDtILhDxgTuaQ2; ds_user_id=29083842507; sessionid=29083842507%3AvpsXr6YU9i9Bgt%3A18',

#     'ig_did=FB765A63-FF99-4A8D-AAED-0D249A55F3CE; csrftoken=3CG6Nf5MEJIPaQtNvEGeZVstlmsIPFtt; rur=FTW; mid=Xi9ZVQALAAF31DVcP2nUGkNy_nnH; ds_user_id=29062029694; sessionid=29062029694%3AKBq8O8JOeXnvxk%3A27',

#     'ig_did=A94986B1-983F-45F5-8D74-B2228BCC6322; csrftoken=GCFhI2A0Bjpnqj3kjVv2CVXFPxMt8ewC; rur=PRN; mid=Xi9ZgQALAAHZv2kCuAX9xQF0EaFH; ds_user_id=29102216191; sessionid=29102216191%3Aj7Dr1u5EeZ7dNH%3A4',

#     'ig_did=5A34F528-75F7-4AD8-A12F-18170196F9A6; csrftoken=5A34F528-75F7-4AD8-A12F-18170196F9A6; rur=FRC; mid=Xx4UswAEAAHQgKvi6Ukl2O2rIk3j; ds_user_id=18262161604; sessionid=18262161604%3Ah2E6yqnpMFDrD6%3A22',

#     'ig_did=9B7995CC-5C24-4DF0-B9B7-1A28F251BF65; csrftoken=tdaenDZToxyAxJoZ0KTCiBz9gksye07Y; rur=ATN; mid=Xx4V5QAEAAEjeo-av5JgbF3VQfnJ; ds_user_id=18096204756; sessionid=18096204756%3AcuFRPIzYIM8eYh%3A7',

#     'ig_did=7A91DFC7-A560-4C0D-B519-88DC615F7084; csrftoken=sVmflcfyctbPkhIm8r2EjZ8y8VBed26X; rur=ATN; mid=Xx4WywAEAAFqebQFz22GHXZuB7CT; ds_user_id=29067884570; sessionid=29067884570%3Ajxg4qRl8v94uuh%3A19',

#     'ig_did=8F870CEE-1D2F-4D17-BE3A-02B2DFED542F; csrftoken=Jz4GWwnyJP3KsmZ8lkGonuQlMKHWBXbC; rur=FRC; mid=Xx8C6gAEAAGQznzPWuufxy_y5ATA; ds_user_id=29099456467; sessionid=29099456467%3AGNymkgrSfvhUxN%3A21',

#     'ig_did=93637582-93A6-435E-B4FE-FB76B9CDB5E3; csrftoken=QKtF4LOElTNWF8Cs712ulpw3IvDAAfiw; rur=PRN; mid=Xx8DegAEAAEvi7UxslepSBPZTkUn; ds_user_id=29076243614; sessionid=29076243614%3AJjYOGcdwhtjdyV%3A22',

#     'ig_did=46D8A77C-C7E6-4D62-A53E-538D40EA40F1; csrftoken=AeoWPxHtEqnfD3543JaJmtiskPjZ9vZW; rur=VLL; mid=Xx8D5gAEAAFUEHF6rt4Si4Tqw320; ds_user_id=28514517496; sessionid=28514517496%3AXEs5EHVxct6eFq%3A10',
# ]

COOKIES = cycle(cookie_value)
# COOKIE = next(COOKIES)
chosen_cookie = ''


def get_user(user_id, user_info):
    global PROXY, PROXIES
    user_url = "https://i.instagram.com/api/v1/users/" + user_id + "/info/"
   
    try:
        response = requests.get(user_url, headers={"cookie": COOKIE, 'User-Agent': user_agent}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})
    except:
        PROXY = next(PROXIES)
    user_data = json.loads(response.text)

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------

    username = user_data['user']['username']
    # user_url_data = "https://www.instagram.com/" + username + "/?__a=1" 
    # COOKIE = next(COOKIES)
    # print(COOKIE)
    # try: 
    #     data_response = requests.get(user_url_data, headers={"cookie": COOKIE, 'User-Agent': user_agent}, timeout=10)
    # except:
    #     PROXY = next(PROXIES)
    # # print(data_response.status_code)
    # user_data_response = json.loads(data_response.text)


    # userFirstName = user_data_response['graphql']['user']['full_name'].split()[0]
    # userLastName = user_data_response['graphql']['user']['full_name'].split()[1]
    # numberOfPosts = user_data_response['graphql']['user']['edge_owner_to_timeline_media']['count']
    
    # external_url = user_data_response['graphql']['user']['external_url']
    # followers = user_data_response['graphql']['user']['edge_followed_by']['count']
    # following = user_data_response['graphql']['user']['edge_follow']['count']


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



def start_scraping(entry, choice, filename_r, tag_num_switch_r):
    # print(choice)
    # print("switch", tag_num_switch_r)
    global workbook_name, COOKIE
    workbook_name = filename_r + ".xlsx"
    # if choice is 'tagAndLocation':
    #     workbook_name = entry[0] + "_" + entry[1] + ".xlsx"
    # else:
    #     workbook_name = entry + ".xlsx"
    global row_count
    row_count = 0
    end_cursor = ''
    location_id = None
    
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
            print(COOKIE)
            entryChosen = ""
            try:
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
                
                r = requests.get(url, headers={"cookie": COOKIE, "User-Agent": user_agent}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

                if r.status_code != 200:
                    print(r.status_code)
                    print("No Posts found. Please Stop scraping before starting a new search")
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
                        # print(COOKIE)
                        info, username = get_user(user_id, user_info)
                        print(COOKIE)
                        if choice is "tag" or choice is "tagAndLocation":
                            # print("tag or tag and loc")
                            if str(tag_num_switch_r) == "true":
                                # print("tag switch true")
                                future_date = get_future_date(shortcode, entryChosen)
                                print(COOKIE)
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

                if choice is "tag":
                    end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']  # value for the next page
                else:
                    end_cursor = data['graphql']['location']['edge_location_to_media']['page_info']['end_cursor']  # value for the next page
                if end_cursor is None or end_cursor == "":
                    stop_scraping()
                    return

            except Exception as e:
                print(e)
                # stop_scraping()


def get_future_date(shortcode, tagwithnumber):

    print("get future date")
    user_url_data = "https://www.instagram.com/p/" + shortcode + "/?__a=1"
    daysTotalPregnant = 280
    # switch_count = 0
    # while switch_count < 5:
    # print(f'SWITCH COUNT SWITCH COUNT {switch_count}')
    COOKIE = next(COOKIES)
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

    numberStr = ""
    for i in range(len(tagwithnumber)):
        if tagwithnumber[i].isdigit():
            numberStr += tagwithnumber[i]

    tagWeek = int(numberStr)
    tagDays = tagWeek * 7

    postDate = datetime.datetime.fromtimestamp(timestamp)
    postDateList = [postDate.month, postDate.day, postDate.year]
    postDayOfYear = dayOfYear(postDateList[0], postDateList[1], postDateList[2])

    todaysDate = datetime.datetime.today()
    todayDayList = [todaysDate.month, todaysDate.day, todaysDate.year]
    todayDayOfYear = dayOfYear(todayDayList[0], todayDayList[1], todayDayList[2])

    daysSincePost = todayDayOfYear - postDayOfYear
    daysPreg = daysSincePost + tagDays
    daysLeft = daysTotalPregnant - daysPreg
    fomatedDaysLeft = datetime.timedelta(days=daysLeft)

    dueDate = todaysDate + fomatedDaysLeft
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
