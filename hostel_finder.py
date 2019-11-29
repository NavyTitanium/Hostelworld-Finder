import requests
import operator
import json
from prettytable import PrettyTable
from collections import Counter
import datetime

stopwords=["i","me","my","myself","we","our","ours","ourselves","you","you're","you've","you'll","you'd","your","yours","yourself","yourselves","he","him",
"his","himself","she","she's","her","hers","herself","it","it's","its","itself","they","them","their","theirs","themselves","what","which","who","whom","this",
"that","that'll","these","those","am","is","are","was","were","be","been","being","have","has","had","having","do","does","did","doing","a","an","the","and",
"but","if","or","because","as","until","while","of","at","by","for","with","about","against","between","into","through","during","before","after","above","below",
"to","from","up","down","in","out","on","off","over","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each",
"few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","don't","should",
"should've","now","d","ll","m","o","re","ve","y","ain","aren","aren't","couldn","couldn't","didn","didn't","doesn","doesn't","hadn","hadn't","hasn","hasn't",
"haven","haven't","isn","isn't","ma","mightn","mightn't","mustn","mustn't","needn","needn't","shan","shan't","shouldn","shouldn't","wasn","wasn't","weren",
"weren't","won","won't","wouldn","wouldn't'","ok","all","us","want","don'","told","again.",",","ok.","got",",i","even"]

currency="USD"
language="en"
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

class Hostel:
	def __init__(self,name, rating, city, review, id):
		self.name = name
		self.rating = rating
		self.city= city
		self.review= review
		self.id=id

		self.male=0
		self.female=0
		self.array_nationality=[]
		self.array_common=[]

	def get_id(self):
		return self.id
	def get_name(self):
		return self.name
	def get_rating(self):
		return self.rating
	def get_city(self):
		return self.city
	def get_review(self):
		return self.review
	def get_common_words(self):
		return self.array_common
	def set_common_words(self,common):
		self.array_common.append(common)
	def get_female(self):
		return self.female
	def set_gender(self,gender):
		if(gender=="FEMALE"):
			self.female+=1
		elif(gender=="MALE"):
			self.male+=1
	def get_male(self):
		return self.male
	def get_nat(self):
		return self.array_nationality
	def set_nat(self,nat):
		self.array_nationality.append(nat)

def display(hostels):
	results=PrettyTable()
	results.field_names = ["Hostel name","Rating (/10)", "Number of reviews","City", "Male","Female", "Nationality", "Common words"]
	for h in hostels:
		frequent_nationality = Counter(h.get_nat()).most_common(4)
		frequent_words = Counter(h.get_common_words()).most_common(9)
		nat=""
		words=""
		for x in frequent_nationality:
			nat=nat + (str(x[0]) + "(" + str(x[1])+"), ")
		for y in frequent_words:
			words=words+str(y[0])+", "
		results.add_row([h.get_name(),h.get_rating(),h.get_review(),h.get_city(),h.get_male(),h.get_female(),nat,words])		
	print(results.get_string(sort_key=operator.itemgetter(3, 0), sortby="Number of reviews"))


def filter_words(comment):
	filteredArray = list(filter(lambda x : x.lower() not in stopwords and not x.isdigit(), comment))
	return filteredArray

def process_reviews(reviews,hostel):
	for x in reviews:
		gender =x["reviewer"]["gender"]
		nationality=(x["reviewer"]["nationality"])
		array=filter_words(x["notes"].split())

		hostel.set_gender(gender)
		hostel.set_nat(nationality)
	
		for words in array:
			hostel.set_common_words(words)

def get_reviews(id,hostel):
	url="https://www.hostelworld.com/properties/" + str(id)  + "/reviews?sort=newest&allLanguages=False&page=1&monthCount=12"
	r = requests.get(url, headers={ "user-agent": user_agent })
	response=r.json()

	if(len(response)>0):
		try:
			pages=response["pagination"]["numberOfPages"]
			if(pages>0):
				reviews=response["reviews"]
				process_reviews(reviews,hostel)
				current=0
				for x in range(pages-1):
					if(current<5 and pages>1):
						url="https://www.hostelworld.com/properties/" + str(id)  + "/reviews?sort=newest&allLanguages=False&page="+str(x+2)+"&monthCount=12"
						r = requests.get(url, headers={ "user-agent": user_agent })
						response=r.json()
						current+=1
						if(len(response)>0):
							reviews=response["reviews"]
							process_reviews(reviews,hostel)			
		except IndexError:
		        print("No comments available for hostel ID " + str(id))

def validate_date(date_text):
	try:
		datetime.datetime.strptime(date_text, '%Y-%m-%d')
	except ValueError:
		raise ValueError("Incorrect data format, should be YYYY-MM-DD")
	
def get_city_id(city):
	url="https://www.hostelworld.com/find/autocomplete?term="+city
	r = requests.get(url, headers={ "user-agent": user_agent })
	response=r.json()
	if(len(response)>0):
		try:
			for x in response:
				cityid=x["id"]
				label=x["label"]
				return cityid,label
		except:
			print("Destination not found")
			exit(0)
	else:
		print("Destination not found. Problem contacting the server")
		exit(0)
	
def build_request():
	
	city = input("Destination city:")
	cityid,label=get_city_id(city.strip())
	arrival = input("Arrival date (YYYY-MM-DD):")
	validate_date(arrival.strip())
	departure = input("Departure date (YYYY-MM-DD):")
	validate_date(departure.strip())
	
	try:
		guests = input("Number of guests:")
		val = int(guests)
	except ValueError:
		raise ValueError("Number of guest invalid")
		exit(0)

	url="https://www.hostelworld.com/city/list-properties?cityId="+cityid+"&currency="+ currency +"&language="+language+"&arrival="+arrival+"&departure="+departure+"&numberOfGuests="+guests
	r = requests.get(url, headers={ "user-agent": user_agent })
	response=r.json()
	
	print("Trip to " + str(label) + " for " + str(guests) + " guests. Arrival: " + str(arrival) + " Departure: "+ str(departure))
	
	return response
	
def main():
	response=build_request()
	if(len(response)>0):
		try:
			properties=response["properties"]
			print(str(len(properties)) + " hostels found")
			hostels=[]
			for x in properties:
				name=x["name"]
				rating=x["averageRating"]/10
				city=x["cityName"]
				review=x["numReviews"]
				id=x["id"]
				hostels.append(Hostel(name,rating,city,review,id))
				
			for hostel in hostels:
				get_reviews(hostel.get_id(),hostel)
		
			display(hostels)
		except IndexError:
			print("No hostels available")
	else:
		print("Something went wrong")


if __name__ == '__main__':
    main()
