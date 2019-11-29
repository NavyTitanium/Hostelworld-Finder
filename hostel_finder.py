import requests
import operator
import json
from prettytable import PrettyTable
from collections import Counter
import datetime
import threading
import queue

stopwords=["i","me","my","myself","we","our","ours","ourselves","you","you're","you've","you'll","you'd","your","yours","yourself","yourselves","he","him","place",
"his","himself","she","she's","her","hers","herself","it","it's","its","itself","they","them","their","theirs","themselves","what","which","who","whom","this","get",
"that","that'll","these","those","am","is","are","was","were","be","been","being","have","has","had","having","do","does","did","doing","a","an","the","and","two",
"but","if","or","because","as","until","while","of","at","by","for","with","about","against","between","into","through","during","before","after","above","below",
"to","from","up","down","in","out","on","off","over","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each",
"few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","don't","should","also",
"should've","now","d","ll","m","o","re","ve","y","ain","aren","aren't","couldn","couldn't","didn","didn't","doesn","doesn't","hadn","hadn't","hasn","hasn't","one","stay"
"haven","haven't","isn","isn't","ma","mightn","mightn't","mustn","mustn't","needn","needn't","shan","shan't","shouldn","shouldn't","wasn","wasn't","weren","-","room",
"weren't","won","won't","wouldn","wouldn't'","ok","all","us","want","don'","told","again.",",","ok.","got",",i","even","hostel","hostel.","hotel","hi","could","bit"]

currency="USD"
language="en"
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
common_words_listed=8
number_of_threads=15
comments_pages=6

class Hostel:
	def __init__(self,name, rating, city, review, id,distance):
		self.name = name
		self.rating = rating
		self.city= city
		self.review= review
		self.id=id
		self.distance=distance
		self.male=0
		self.female=0
		self.array_nationality=[]
		self.array_common=[]
	def get_id(self):
		return self.id
	def get_name(self):
		return self.name
	def get_distance(self):
		return self.distance
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

# Fills the result table
def display(hostels):
	results=PrettyTable()
	results.field_names = ["Hostel name","Rating (/10)", "Number of reviews", "Distance","City", "Male","Female", "Nationality", "Common words"]
	for h in hostels:
		frequent_nationality = Counter(h.get_nat()).most_common(4)
		frequent_words = Counter(h.get_common_words()).most_common(common_words_listed)
		nat=""
		words=""
		for x in frequent_nationality:
			nat=nat + (str(x[0]) + "(" + str(x[1])+"), ")
		for y in frequent_words:
			words=words+str(y[0])+", "

		results.add_row([h.get_name(),h.get_rating(),h.get_review(),h.get_distance(),h.get_city(),h.get_male(),h.get_female(),nat,words])
		
	print(results.get_string(sort_key=operator.itemgetter(3, 0), sortby="Number of reviews"))

# Returns the comment minus any words in the stopwords list
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

# Fetch the reviews for each hostels
def get_reviews(q):
	while not q.empty():
		hostel=q.get()
		id=hostel.get_id()
		
		# Get the first review page 
		url="https://www.hostelworld.com/properties/" + str(id)  + "/reviews?sort=newest&allLanguages=False&page=1&monthCount=12"
		r = requests.get(url, headers={ "user-agent": user_agent })
		response=r.json()

		if(len(response)>0):
			try:
				# Verify if there's more than 1 page available for the reviews of that hostel
				pages=response["pagination"]["numberOfPages"]
				if(pages>0):
					reviews=response["reviews"]
					process_reviews(reviews,hostel)
					
					# Fetch the next review pages until the end or until we hit 'comments_pages' (6 by default)
					for i in range(2,pages+1):
						if i > comments_pages:
							break
						url="https://www.hostelworld.com/properties/" + str(id)  + "/reviews?sort=newest&allLanguages=False&page="+str(i)+"&monthCount=12"
						r = requests.get(url, headers={ "user-agent": user_agent })
						response=r.json()
						if(len(response)>0):
							reviews=response["reviews"]
							process_reviews(reviews,hostel)
			except IndexError:
				print("No comments available for hostel ID " + str(id))

		q.task_done()

# Validates the date given by the user
def validate_date(date_text):
	try:
		datetime.datetime.strptime(date_text, '%Y-%m-%d')
	except ValueError:
		raise ValueError("Incorrect data format, should be YYYY-MM-DD")

# Returns the city ID given a city name, based on hostelworld' API
def get_city_id(city):
	url="https://www.hostelworld.com/find/autocomplete?term="+city
	r = requests.get(url, headers={ "user-agent": user_agent })
	response=r.json()
	if(len(response)>0):
		try:
			for x in response:
				cityid=x["id"]
				label=x["label"]
				
				# Just get the first result returned
				return cityid,label
		except:
			print("Destination not found")
			exit(0)
	else:
		print("Destination not found. Problem contacting the server")
		exit(0)

# Take user inputs and build the initial request URL	
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
	print(url)
	return response
	
def main():
	# Get the list of hostels for a destination
	response=build_request()
	if(len(response)>0):
		try:
			#Get the number of hostels returned by the API
			properties=response["properties"]
			print(str(len(properties)) + " hostels found")
			hostels=[]
			for x in properties:
				name=x["name"]
				rating=x["averageRating"]/10
				city=x["cityName"]
				review=x["numReviews"]
				distance=x["distance"]
				id=x["id"]
				
				# Instantiate an Hostel object and appending it to an array 
				hostels.append(Hostel(name,rating,city,review,id,distance))

			print("Fetching the last "+ str(comments_pages) +" pages of reviews for each hostels...")
			
			# Puts hostel objects into a queue, for processing in threads
			q = queue.Queue()
			threads=[]
			for hostel in hostels:
				q.put(hostel)
			
			# Start the threads to fetch the reviews faster
			for i in range(number_of_threads):
				t=threading.Thread(target=get_reviews, args=(q,))
				threads.append(t)
				t.start()
			
			# Waits for all of the reviews to be fetched and processed
			q.join()
			for z in threads:
				z.join()
		
			# Display the results
			display(hostels)

		except IndexError:
			print("No hostels available")
	else:
		print("Something went wrong")


if __name__ == '__main__':
    main()
