import csv
import glob
import json
import os
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
from pyvirtualdisplay import Display
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

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
            if t1.is_alive():
                print("thread still alive man. Fuck")
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
        # --------------
        multiple = False
        # --------------
        hashtag_r = request.POST.get('hashtag')
        location_r = request.POST.get('location')
        zip_r = request.POST.get('zip')
        # filename_r = request.POST.get('filename')
        hashtag_list_r = request.POST.get('hashtag-list')
        tag_num_switch_r = request.POST.get('tagwithnumberswitch')
        print(tag_num_switch_r)
        hashtag_list_r = str(hashtag_list_r)
        hashtag_list_r = hashtag_list_r.split(',')
        print(hashtag_list_r)
        
        print("number of hashtags:", len(hashtag_list_r))
        
        # added here - jesse
        # if hashtag_r != "" and zip_r != "" or location_r != "":
        # --------------
        if len(hashtag_list_r) > 0 and location_r != "":
            multiple = True
            choice_r = "tagAndLocation"
            entry_r = [hashtag_list_r, location_r]
            print("tag and loc")
        # --------------
        else:
            if len(hashtag_list_r) > 0:
                choice_r = "tag"
                # entry_r = hashtag_r
                entry_r = hashtag_list_r
            if zip_r != "":
                choice_r = "zip"
                entry_r = [zip_r]
            if location_r != "":
                choice_r = "location"
                entry_r = [location_r]

        if request.POST.get('startscraping'):
            global row_count
            row_count = 0
            
           
            # global thread
            global thread_list
            for tag in entry_r:
                create_text_file(tag)
                thread = threading.Thread(target=start_scraping, args=(tag, choice_r, tag, tag_num_switch_r))
                thread_list.append(thread)
            
            for thread in thread_list:
                thread.daemon = True
                thread.start()

            if multiple is True:
                if len(entry_r) > 0:
                    print(row_count)
                    context = {
                        "row_count": row_count,
                        "entry": entry_r[0],
                        "running": "True",
                    }
            else:
                if len(entry_r) > 0:
                    print(row_count)
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
                    "entry": entry_r[0],
                }
            else:
                location_list = get_location_list(entry_r[0], choice_r)
                context = {
                    "location_list": location_list,
                    "entry": entry_r[0],
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

    # 'ig_did=E47FEC0C-30C6-472F-A9FC-0C1123F77B15; csrftoken=4NYlt3ps9weBjjQdupkFy7uGu3SYDImC; rur=ATN; mid=Xi9XzAALAAGmbiNZxhWMQWvdXAyw; ds_user_id=28683127656; sessionid=28683127656%3Arncw1sq26MLYf3%3A13',

    # 'ig_did=33C11652-D6BA-4024-B66A-B54989AD7D4B; csrftoken=KRsKBnMKpZLkicXiFKq0xUnQZMEFxzOp; rur=FRC; mid=Xi9YcQALAAEwBFt_BXZeJ0Pvd7-P; ds_user_id=28870662934; sessionid=28870662934%3AnVnrQVTqTrT4nE%3A11',

    # 'ig_did=0786D9EE-CD88-4F10-A7D3-F0D87130E4A8; csrftoken=ByB5JuP5vwfzQD46gorGEA7RtsdjAeEk; rur=FRC; mid=Xi9YxgALAAGc0eoDtILhDxgTuaQ2; ds_user_id=29083842507; sessionid=29083842507%3AvpsXr6YU9i9Bgt%3A18',

    # 'ig_did=FB765A63-FF99-4A8D-AAED-0D249A55F3CE; csrftoken=3CG6Nf5MEJIPaQtNvEGeZVstlmsIPFtt; rur=FTW; mid=Xi9ZVQALAAF31DVcP2nUGkNy_nnH; ds_user_id=29062029694; sessionid=29062029694%3AKBq8O8JOeXnvxk%3A27',

    # 'ig_did=A94986B1-983F-45F5-8D74-B2228BCC6322; csrftoken=GCFhI2A0Bjpnqj3kjVv2CVXFPxMt8ewC; rur=PRN; mid=Xi9ZgQALAAHZv2kCuAX9xQF0EaFH; ds_user_id=29102216191; sessionid=29102216191%3Aj7Dr1u5EeZ7dNH%3A4',

    'ig_did=40840E02-2385-4458-91C7-F7E5658A3C2E; csrftoken=pSG9zxxfGiKOoIBROaQ0Vjhh3G0azvYm; rur=FRC; mid=XooWHgAEAAED4b4tv9gff5YRXyyT; ds_user_id=17855852863; sessionid=17855852863%3AFRDcbz6lTN6mnk%3A2',

    # 'ig_did=F32CCF72-711B-4250-ABEB-31278AE63465; csrftoken=MYrMXkGnAnty2cHn9zutv66CKxWhhN6b; rur=ASH; mid=XxSkyQAEAAESIBtGIhWAPB-2URjQ; ds_user_id=314946530; sessionid=314946530%3AyO17zHD7llrrxR%3A2',

    # 'ig_did=F32CCF72-711B-4250-ABEB-31278AE63465; csrftoken=HRQOCJpHe3TBkMae1jsG52yfzRn2FFyM; rur=ASH; mid=XxSkyQAEAAESIBtGIhWAPB-2URjQ; ds_user_id=28514517496; sessionid=28514517496%3AZjT1Qhdswi7mwH%3A1',
]


chosen_cookie = ''


def get_user(user_id, user_info):
    global PROXY, PROXIES
    user_url = "https://i.instagram.com/api/v1/users/" + user_id + "/info/"
    print(user_url)
    switch_count = 0
    # print('SWITCH COUNT SWITCH COUNT')
    while switch_count < 5:
        print(f'SWITCH COUNT SWITCH COUNT {switch_count}')

        try:
            response = requests.get(user_url, headers={"cookie": random.choice(cookie_value), 'User-Agent': user_agent},
                                timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})
            break
        except:
            PROXY = next(PROXIES)
            switch_count+=1
    if switch_count == 5:
        return user_info
        # print(cookie)
    user_data = json.loads(response.text)
    user_data_string = json.dumps(response.text)

    # print(user_data)
    sleep(3)
    
    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    username = user_data['user']['username']

    print("data user str:")
    
    user_url_data = "https://www.instagram.com/" + username + "/?__a=1"

    switch_count = 0
    while switch_count < 5:
        print(f'SWITCH COUNT SWITCH COUNT {switch_count}')
        try: 
            data_response = requests.get(user_url_data, headers={"cookie": random.choice(cookie_value), 'User-Agent': user_agent}, timeout=10)
            break
        except:
            PROXY = next(PROXIES)
            switch_count+=1
    if switch_count == 5:
        return user_info
        # print(cookie)
    print(data_response.status_code)
    user_data_response = json.loads(data_response.text)

    # username - get from api request
    # userEmail - get from api request
    userFirstName = user_data_response['graphql']['user']['full_name'].split()[0]
    userLastName = user_data_response['graphql']['user']['full_name'].split()[1]
    # locationOfPost - get from https://www.instagram.com/p/ shortcode /?__a=1
    numberOfPosts = user_data_response['graphql']['user']['edge_owner_to_timeline_media']['count']
    igURL = 'https://www.instagram.com/' + username + '/'
    external_url = user_data_response['graphql']['user']['external_url']
    followers = user_data_response['graphql']['user']['edge_followed_by']['count']
    following = user_data_response['graphql']['user']['edge_follow']['count']
    # posts = user_data_response['graphql']['user']['edge_owner_to_timeline_media']['edges']
    # timestamp = posts[10]['node']['taken_at_timestamp'] # converts epoch number into date and time
    
    
    
#     user_info.extend([followers, following, numberOfPosts, igURL, external_url])
#     return user_info
    
#     # -------------------------
#     # -------------------------

#     sleep(3)

    follower_count = user_data['user']['follower_count']
    try:
        public_email = user_data['user']['public_email']
    except:
        public_email = ' '
    full_name = user_data['user']['full_name']

    user_info.extend([username, userFirstName, userLastName, public_email, followers, following, external_url, numberOfPosts, igURL])
    return user_info, username
        # print(
        #     "ID: " + user_id + " " + "Username : " + username + " " + str(score))



def start_scraping(entry, choice, filename_r, tag_num_switch_r):
    print(choice)
    print("switch", tag_num_switch_r)
    global workbook_name
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
    if choice is 'tagAndLocation':
        print("tag and location chosen")
    if choice is 'tag':
        print("tag chosen")
    if choice is "location":
        location_id = get_location_id(entry[0])
    if choice is 'zip':
        location_name = get_location_name(entry[0])
        if location_name is None:
            abort = True
            print('Zipcode 404')
        if abort is False:
            location_id = get_location_id(location_name)


    if abort is False:
        for page in range(num_of_pages):
            
            # number_of_entries = len(entry)
            try:
                # entryChosen = entry[i % number_of_entries]
                entryChosen = entry.replace(" ", "")
                print("entry in start scraping", entryChosen)
                if page == 0:
                    if choice is "tag":
                        url = "https://www.instagram.com/explore/tags/" + entryChosen + "/?__a=1"

                    else:
                        url = "https://www.instagram.com/explore/locations/" + location_id + "/?__a=1"

                else:
                    if choice is "tag":
                        url = "https://www.instagram.com/explore/tags/" + entryChosen + "/?__a=1&max_id=" + end_cursor
                    else:
                        url = "https://www.instagram.com/explore/locations/" + location_id + "/?__a=1&max_id=" + end_cursor

                print(url)
                r = requests.get(url, headers={"cookie": random.choice(cookie_value), "User-Agent": user_agent}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

                if r.status_code != 200:
                    print(r.status_code)
                    print("No Posts found. Please Stop scraping before starting a new search")
                    continue

                # print(r.text)
                data = json.loads(r.text)
                
                f= open("guru99.txt","w+")
                f.write(str(data))
                if choice is "tag":
                    edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges']  # list with posts
                else:
                    edges = data['graphql']['location']['edge_location_to_media']['edges']  # list with posts

                for item in edges:
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
                        info, username = get_user(user_id, user_info)

                        if choice is "tag" or choice is "tagAndLocation":
                            print("tag or tag and loc")
                            if str(tag_num_switch_r) == "true":
                                print("tag switch true")
                                future_date = get_future_date(shortcode, entryChosen)
                                info.extend([future_date, entryChosen])
                                
                        print(info)
                        print("--- %s seconds | User Time ---" % round(time.time() - start_time1, 2))
                        start_time2 = time.time()
                        print("test 11")
                        if len(info) != 0:
                            print("22")
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


def get_future_date(shortcode, tagwithnumber):

    print("get future date")
    user_url_data = "https://www.instagram.com/p/" + shortcode + "/?__a=1"
    daysTotalPregnant = 280
    # switch_count = 0
    # while switch_count < 5:
    # print(f'SWITCH COUNT SWITCH COUNT {switch_count}')
    try: 
        data_response = requests.get(user_url_data, headers={"cookie": random.choice(cookie_value), 'User-Agent': user_agent}, timeout=10)
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
    print(todayDayOfYear)
    print(postDayOfYear)
    print(daysPreg)
    print(daysLeft)
    print(dueDate.date())
    print('day of year', todayDayOfYear)
    
    
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
            r = requests.get(url, headers={"cookie": random.choice(cookie_value)}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})
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

        # # split the full name
        # name_arr = data[4].split(" ", 1)
        # first = name_arr[0]
        # last = name_arr[1] if len(name_arr) > 1 else ""
        # # remove the fullname element and add fname and lname
        # data.pop()
        # data.append(first)
        # data.append(last)
        # print(data)
        save_data.append(data)
        if row_count % 100 == 0:

            print("Storing data in bulk YOLO")
            headers = ['Location','Username','First Name', 'Last Name', 'Public Email', 'Followers', 'Following', 'External URL', 'Number of Posts', 'Profile URL', 'Due Date', 'Tag']

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
    req = requests.get(get_location_id_url, headers={"cookie": random.choice(cookie_value)}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

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
    req = requests.get(get_location_id_url, headers={"cookie": random.choice(cookie_value)}, timeout=10, proxies={'http': f'http:{PROXY}', 'https': f'https:{PROXY}'})

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

    # deleting the location file - location.txt
    if os.path.isfile('entry.txt'):
        os.remove("entry.txt")

    try:

        headers = ['Location', 'Username', 'Followers', 'Email', 'First name', 'Last name']

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
        sheet.column_dimensions['B'].width = 20
        sheet.column_dimensions['D'].width = 30
        sheet.column_dimensions['E'].width = 20
        sheet.column_dimensions['F'].width = 20

        wb.save(filename=workbook_name)
        save_data.clear()
        for thread in thread_list:
            thread.join()

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
