import base64
import os
import time
import json
import urllib.parse as urlparse

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import datetime 


CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
#'/app/.chromedriver/bin/chromedriver'
# GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'


def parseCompany(pageContent):

    packGameInfo = {
        "companyName" : "",
        "webSite"     : "",
        "twitter"     : "",
        "youtube"     : "",
    }
    
    # Get App Site Link
    siteLink = ''
    siteLinkTag = pageContent.select("a.curator_url.ttip")
    if len (siteLinkTag):
        if siteLinkTag[0]['href']:
            siteLink = siteLinkTag[0]['href']
    packGameInfo["webSite"] = siteLink

    # Get Social Link
    socialWrapper = pageContent.select("div.socialmedia_accounts")
    if len(socialWrapper):
        socialTagList = socialWrapper[0].find_all('span' , recursive=False)
        if len(socialTagList):
            # socialTagList[0].select('a')[0]['href']  # facebook
            # socialTagList[1].select('a')[0]['href']  # steam community
            # packGameInfo['twitter'] = socialTagList[2].select('a')[0]['href'] # twitter
            # packGameInfo['youtube'] = socialTagList[3].select('a')[0]['href'] # youtube
            for eachSpan in socialTagList:
                if "twitter" in eachSpan.select('a')[0]['href']:
                    packGameInfo['twitter'] = eachSpan.select('a')[0]['href']
                if "youtube" in eachSpan.select('a')[0]['href']:
                    packGameInfo['youtube'] = eachSpan.select('a')[0]['href']               

    gameList = []
    listWrapper = pageContent.select("img.capimg")
    if len(listWrapper):
        for imgTag in listWrapper:
            gameList.append(imgTag.parent['href'])

    return packGameInfo, gameList

def parseAGame(pageContent, driver):

    aGameInfo = {}

    appNameTagList = pageContent.select("div#appHubAppName")
    if len(appNameTagList):
        aGameInfo["gameName"] = appNameTagList[0].text

    gameInfoPanel = pageContent.select("div.glance_ctn_responsive_left")
    if len(gameInfoPanel):
        gameInfoWrap = gameInfoPanel[0]

        # Get App Release Date
        releaseDateTagList = gameInfoWrap.find("div" , class_="release_date")
        if len(releaseDateTagList):
            releaseDateTag = releaseDateTagList.select("div.date")
            if len(releaseDateTag):
                aGameInfo["releaseDate"] = releaseDateTag[0].text

        # Get App Developer Information
        developerRowTag = gameInfoWrap.find("div" , id="developers_list")
        developerLink = ''
        if len(developerRowTag):
            appDeveloperTagList = developerRowTag.select("a")
            if len(appDeveloperTagList):
                aGameInfo["developer"] = appDeveloperTagList[0].text
                developerLink = appDeveloperTagList[0]['href']

        # Get App Publisher Information
        publisherRowTagWrapper = gameInfoWrap.select("div.dev_row")
        if len(publisherRowTagWrapper):
            publisherRowTag = publisherRowTagWrapper[len(publisherRowTagWrapper) - 1]
            if publisherRowTag:
                appPublisherTagList = gameInfoWrap.select("a")
                if len(appPublisherTagList):
                    aGameInfo["publisher"] = appPublisherTagList[0].text

    # Get App ScreenShot Links
    screenshots = []
    videoScreenShots = pageContent.select("div.highlight_movie")
    for videoScreenShot in videoScreenShots:
        screenshots.append({ "type": "video", "link": videoScreenShot['data-mp4-hd-source']})

    dicts = driver.execute_script("return rgScreenshotURLs;")
    for url in dicts.values():
        screenshots.append({ "type": "screenshot", "link": url.replace("_SIZE_" , ".1920x1080")})

    aGameInfo['media'] = screenshots

    # Get App Popular Tag
    tags = []
    tagsListWrapper = pageContent.select("div.glance_tags.popular_tags a")
    if len(tagsListWrapper):
        for tag in tagsListWrapper:
            tags.append(tag.text.replace("\t" , "").replace("\n" , ""))
    aGameInfo['tags'] = tags

    # Add unique tags to allTags array
    # for tag in tags:
    #     if tag not in allTagsArray:
    #         allTagsArray.append(tag)

    # Get App Description
    descTag = pageContent.select("div.game_description_snippet")
    if len(descTag):
        aGameInfo["description"] = descTag[0].text.replace("\t" , "")   

    return aGameInfo , developerLink

def categoryPageParse(targetLink):
       
    delay = 10 # seconds that wait to loading page
    resAr = []

    # targetLink is input link
    # file1 = open('input_link.txt', 'r')
    # targetLink = file1.readline()

    # chrome_options = Options()
    # chrome_options.binary_location = GOOGLE_CHROME_PATH
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--disable-gpu')
    print ("test")
    print (os.environ)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driverCategory = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
    
   # driverCategory = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH ) # , chrome_options=chrome_options)

    try:
        driverCategory.get(targetLink)

        try:
            wait = WebDriverWait(driverCategory, delay)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_content.page_content')))
        except TimeoutException:

            # if this page is age detect page
            pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")
            ageDetectTags = pageContent.select("div.agegate_birthday_selector")
            if len (ageDetectTags): # set user's age is Jan 1, 1951
                yearDrop = driverCategory.find_element_by_id('ageYear')
                dropdown = Select(yearDrop)
                dropdown.select_by_visible_text('1951')
                viewPageBtns = driverCategory.find_elements_by_css_selector("a.btnv6_blue_hoverfade")
                if len(viewPageBtns):
                    viewPageBtns[0].click()
                    
                    driverCategory.get(targetLink)
                    wait = WebDriverWait(driverCategory, delay)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_content.page_content')))
            else:
                raise Exception("Over Loading Time/We skipped this page.")

        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_responsive_horizontal_scroll.store_horizontal_autoslider.block_content')))
        pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")

        gameInfo , developerLink = parseAGame(pageContent, driverCategory)

        # set steam_link for the game
        gameInfo['steam_link'] = targetLink
        comInfo = {}

        if developerLink.find('/search/?') < 0:

            driverCategory.get(developerLink)
            WebDriverWait(driverCategory, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.page_content_ctn')))
            pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")
            comInfo , gameList = parseCompany(pageContent)

        comInfo["games"] = []
        comInfo["games"].append(gameInfo)
        comInfo['companyName'] = gameInfo['publisher']

        resAr.append(comInfo)

    except Exception as ex:
        unknownExceptionOccur(ex)

    driverCategory.close()
    
    return resAr

def get_screenshot(request):
    """
    Take a screenshot and return a png file based on the url.
    """
    width = 1024
    height = 768

    if request.method == 'POST' and 'url' in request.POST:
        url = request.POST.get('url', '')
        if url is not None and url != '':

            res = categoryPageParse (url)
            # save = False
            # base_url = '{0.scheme}://{0.netloc}/'.format(urlparse.urlsplit(url))
            # domain = urlparse.urlsplit(url)[1].split(':')[0]
            # params = urlparse.parse_qs(urlparse.urlparse(url).query)

            # driver = webdriver.Chrome(DRIVER)
            # driver.get(url)
            # driver.set_window_size(width, height)

            # if 'save' in params and params['save'][0] == 'true':
            #     save = True
            #     now = str(datetime.today().timestamp())
            #     img_dir = settings.MEDIA_ROOT
            #     img_name = ''.join([now, '_image.png'])
            #     full_img_path = os.path.join(img_dir, img_name)
            #     if not os.path.exists(img_dir):
            #         os.makedirs(img_dir)
            #     driver.save_screenshot(full_img_path)
            #     screenshot = img_name
            # else:
            #     screenshot_img = driver.get_screenshot_as_png()
            #     screenshot = base64.encodestring(screenshot_img)

            # var_dict = {
            #     'screenshot': screenshot,
            #     'domain': domain,
            #     'base_url': base_url,
            #     'full_url': url,
            #     'save': save
            # }
            # driver.quit()    

            result = {
                'data': json.dumps(res , indent=4),
                'full_url': url
            }

            return render(request, 'home.html', result)
    else:
        return render(request, 'home.html')
