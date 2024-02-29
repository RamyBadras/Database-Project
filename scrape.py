from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import csv

''' only 300 cars were excluded (around 2700 out of the 3015 that i processed).
    Much more processing to the data was done using other python programs, such as turning sep 2023 into 2023-09-01.
    I wasn't able to import the data due to non ascii characters in them. removing the non ascii characters removed the 
    arabic letters in my data resulting in weird car descriptions in place of the arabic ones. 
'''

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

maxPage = 78
carNum = 0

# Login.

url = "https://www.olx.com.eg/en/vehicles/cars-for-sale/cairo/?page=1&filter=new_used_eq_2%2Cyear_between_2000_to_2023"
driver.get(url)

# Enter Valid email and password.
email = ""   
password = ""

driver.implicitly_wait(10)
driver.find_element(By.XPATH, "//span[text()=\"Login\"]").click()
driver.implicitly_wait(3)
driver.find_element(By.XPATH, "//span[text()=\"Continue with Email\"]" ).click()
driver.implicitly_wait(3)
emailBox = driver.find_element(By.XPATH, "//input[@name=\"email\"]")
emailBox.send_keys(email)
driver.find_element(By.XPATH, "//span[text()=\"Next\"]").click()
driver.implicitly_wait(5)
passwordBox = driver.find_element(By.XPATH, "//input[@id=\"password\"]")
passwordBox.send_keys(password)
driver.find_element(By.XPATH, "//span[text()=\"Log in\"]").click()
driver.implicitly_wait(5)

# Gathering all Sellers to process them at the end and only take the unique values.
all_sellers_url = []

for page in range(1, maxPage):
    url = "https://www.olx.com.eg/en/vehicles/cars-for-sale/cairo/?page=" + str(page) + "&filter=new_used_eq_2%2Cyear_between_2000_to_2023"

    i=0
    driver.get(url)
    req = driver.page_source

    # Creating Soup Object
    soup = BeautifulSoup(req, "html.parser")
    allDivs = soup.find_all("div", class_="a52608cc")

    while(len(allDivs) < 1):
        driver.get(url)
        req = driver.page_source
        soup = BeautifulSoup(req, "html.parser")
        allDivs = soup.find_all("div", class_="a52608cc")
        time.sleep(1)
        i+=1
        print("TRY NO: " + str(i) + " AllDivs Length: " + str(len(allDivs)))

    # Gathering Product Links in an Array and skipping every other link cause every link exists twice for some reason.

    links = []
    skip = False
    for tag in allDivs:
        for anchor in tag.find_all('a'):
            if (skip==False):
                links.append(anchor['href'])
                skip=True
            else:
                skip = False

    olxURL = "https://www.olx.com.eg"
    count=0
    for i in range(0, len(links)):

        driver.get(olxURL+links[i])
        req = driver.page_source
        soup = BeautifulSoup(req, "html.parser")
        details = soup.find_all("div", class_="b44ca0b3")

        # pretty much begging OLX to give me what i want.
        while(len(details) == 4):
            driver.get(olxURL+links[i])
            req = driver.page_source
            soup = BeautifulSoup(req, "html.parser")
            details = soup.find_all("div", class_="b44ca0b3")
            count+=1
            print("TRY NO: " + str(count) + " Details Status: " + str(details))

        try:

            ad_id = links[i][-14:-5]
            carNum+=1
            print( "Car " + str(carNum) + ": " + str(ad_id))

            # Seller URL
            seller_field = soup.find("div", class_="_1075545d d059c029")
            try:
                seller_2 = seller_field.find_all('a')
            except AttributeError:
                continue
            
            seller_url = str(seller_2[0]['href'])

            # Location
            location = soup.find("span", class_="_8918c0a8").text

            # Storing each required detail in a variable.
            detailsString = ""

            for detail in details:
                detailsString = detailsString + str(detail.text) + '\n'

            # Finding Condition first, if "New" car is excluded.
            conditionIndex = detailsString.find('Condition')
            condition = detailsString[conditionIndex+9:]
            temp = condition.split('\n')
            condition = temp[0]
            if condition=="New":
                print("Excluded")
                continue
            
            # Only these 4 details' positions never change, no need to use find().
            brand = str(details[0].text)[5:]
            model = str(details[1].text)[5:]
            fuel_type = str(details[3].text)[9:]
            price = str(details[4].text)[5:]

            # Finding Year
            yearIndex = detailsString.find("Year")
            if(yearIndex==-1):
                year = ""
            else:
                year = detailsString[yearIndex+4:]
                temp = year.split('\n')
                year = temp[0]

            # Finding price type
            paymentIndex = detailsString.find("Payment Options")
            if(paymentIndex==-1):
                payment_option = ""
            else:
                payment_option = detailsString[paymentIndex+15:]
                temp = payment_option.split('\n')
                payment_option = temp[0]

            
            # Finding Body Type if available
            bodyTypeIndex = detailsString.find('Body Type')
            if (bodyTypeIndex==-1):
                body_type = ""
            else :
                body_type = detailsString[bodyTypeIndex+9:]
                temp = body_type.split('\n')
                body_type = temp[0]

            # Finding Color if Available
            colorIndex = detailsString.find('Color')
            if (colorIndex==-1):
                color = ""
            else:
                color = detailsString[colorIndex+5:]
                temp = color.split('\n')
                color = temp[0]
            
            # Engine Capacity Processing
            engineCapacityIndex = detailsString.find("Engine Capacity")
            if (engineCapacityIndex == -1):
                engine_capacity_to = ""
                engine_capacity_from = ""
            else:
                engine_capacity = detailsString[engineCapacityIndex+20:]
                temp = engine_capacity.split('\n')
                engine_capacity = temp[0]
                if (engine_capacity.find('-')!=-1):
                    ecr = engine_capacity.split(' - ')
                    engine_capacity_to = ecr[1]
                    engine_capacity_from = ecr[0]
                else :
                    engine_capacity_to = engine_capacity
                    engine_capacity_from = engine_capacity
                if (engine_capacity_from.find("More than 3000") != -1):
                    engine_capacity_to = "3000"
                    engine_capacity_from = "3000"

            # Finding Mileage
            kilometerIndex = detailsString.find("Kilometers")
            if (kilometerIndex==-1):
                kilometers_from = ""
                kilometers_to = ""
            else:
                kilometer_range = detailsString[kilometerIndex+10:]
                temp = kilometer_range.split('\n')
                kilometer_range = temp[0]

            # Processing Mileage
            if(kilometer_range.find("to") != -1):
                range_split = kilometer_range.split(' to ')
                kilometers_from = range_split[0]
                if ( len(range_split) > 1 ):
                    kilometers_to = range_split[1]
                else:
                    kilometers_to = kilometers_from
            else:
                kilometers_from = kilometer_range
                kilometers_to = kilometer_range
            if (kilometers_from.find("More than 200000") != -1):
                kilometers_from =  "200000"
                kilometers_to = "200000"

            # Finding Extra Features, storing in a separate CSV file.
            try:
                features_exist = False
                extraFeaturesSource = soup.find("div", class_="_27f9c8ac")
                extraFeatures = extraFeaturesSource.find_all("span", class_="_66b85548")
                features_exist = True
            except AttributeError:
                print("No Extra Features")
                features_exist = False
                pass

            if (features_exist):
                for feature in extraFeatures:
                    featureList = [ad_id, str(feature.text)]
                    with open("/Users/ramygad/college/Spring 2023/Database/data/features.csv", 'a', newline='') as outFeature:
                        writer = csv.writer(outFeature)
                        writer.writerow(featureList)


        # There's a Fiat that breaks my code, The exception handling is mainly for that one car...
        except IndexError:
            print("Excluded.")
            continue
        
        # Finding and Showing Phone number.

        try:
            driver.find_element(By.XPATH, "//span[text()=\"Show number\"]").click()
            driver.implicitly_wait(0.5)
            phone_number = str(driver.find_element(By.XPATH, "//span[@class=\"_45d98091 _2e82a662\"]").text)
        except NoSuchElementException:
            phone_number = ""

        # Finding car description

        try:
            description = str(driver.find_element(By.XPATH, "//div[@class=\"_0f86855a\"]").text)
        except NoSuchElementException:
            description = ""

        # finding listing date

        try:
            listing_date = str(driver.find_element(By.XPATH, "//div[@class=\"_1075545d e3cecb8b _5f872d11\"]/span[@class=\"_8918c0a8\"]/span[@aria-label=\"Creation date\"]").text)
        except NoSuchElementException:
            listing_date = ""

        # finding seller name
        
        try:
            seller_name = str(driver.find_element(By.XPATH, "//span[@class=\"_261203a9 _2e82a662\"]").text)
        except NoSuchElementException:
            seller_name = ""

        # Finding Join Date

        try:
            join_date = str(driver.find_element(By.XPATH, "//div[@class=\"_05330198\"]").text)
            join_date = join_date[13:]
        except NoSuchElementException:
            join_date = ""

        currentDetails=[]
        currentDetails.append(ad_id)
        currentDetails.append(brand)
        currentDetails.append(model)
        currentDetails.append(body_type)
        currentDetails.append(year)
        currentDetails.append(engine_capacity_from)
        currentDetails.append(engine_capacity_to)
        currentDetails.append(color)
        currentDetails.append(fuel_type)
        currentDetails.append(kilometers_from)
        currentDetails.append(kilometers_to)
        currentDetails.append(price)
        currentDetails.append(payment_option)
        currentDetails.append(location)
        currentDetails.append(listing_date)
        currentDetails.append(seller_url)
        currentDetails.append(phone_number)
        currentDetails.append(description)

        sellerDeets=[]

        if (seller_url not in all_sellers_url):
            all_sellers_url.append(seller_url)
            sellerDeets.append(seller_name)
            sellerDeets.append(phone_number)
            sellerDeets.append(seller_url)
            sellerDeets.append(join_date)
            with open("/Users/ramygad/college/Spring 2023/Database/data/sellers.csv", 'a', newline='') as sellerOut:
                writer = csv.writer(sellerOut)
                writer.writerow(sellerDeets)

        with open("/Users/ramygad/college/Spring 2023/Database/data/cars.csv", 'a', newline='') as outFile:
            writer = csv.writer(outFile)
            writer.writerow(currentDetails)

    links=[]

driver.quit()