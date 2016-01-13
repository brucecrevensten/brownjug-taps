import mechanize
from lxml import etree
from StringIO import StringIO
from brewerydb import *
import os
import falcon
import json

findButtonName = 'dnn$ctr1234$ViewController$StoreLocatorGoogleMaps$btnFind'
url = 'http://www.brownjugalaska.net/Beer/Growler-Bar'
zipInputName = 'dnn$ctr1234$ViewController$StoreLocatorGoogleMaps$txtSearchByPostalCode'
xpathRoot = '//*[@id="dnn_ctr1234_ViewController_StoreLocatorGoogleMaps_dlStoreList_dlBOTList_0"]'

if 'BREWERY_DB_API_KEY' in os.environ:
	BreweryDb.configure(os.environ['BREWERY_DB_API_KEY'])

def fetch_beers():

	beers = []

	if 'BROWN_JUG_ENV' in os.environ and os.environ['BROWN_JUG_ENV'] == 'test':
		# For testing
		print "Running against test file (jug.html)..."
		myfile = open('jug.html', 'r')
		response = StringIO(myfile.read())
	else:
		print "Fetching from Brown Jug web site..."
		# For reals
		br = mechanize.Browser()
		br.open(url)
		br.form = list(br.forms())[0]
		br.form[zipInputName] = '99712'
		br.method = "POST"
		response = br.submit(findButtonName)

	parser = etree.HTMLParser()
	tree = etree.parse(response, parser)
	result = etree.tostring(tree.getroot(), pretty_print=True, method="html")
	r = tree.xpath(xpathRoot + '/span/table//td[2]/div')

	for beer in r:
		beerInfo = {}
		parts = list(beer.itertext())
		beerInfo['name'] = parts[2].strip()
		beerInfo['brewery'] = parts[4].strip()

		beerApiInfo = BreweryDb.beers({'name':beerInfo['name'],'withBreweries':'Y'})
		if 'totalResults' in beerApiInfo and beerApiInfo['totalResults'] == 1:
			thisBeer = beerApiInfo['data'][0]
			try:
				print thisBeer
				if 'description' in thisBeer:
					beerInfo['description'] = thisBeer['description']
				beerInfo['style'] = thisBeer['style']['name']
				beerInfo['styleDescription'] = thisBeer['style']['description']
			except:
				print thisBeer

		beers.append(beerInfo)

	return beers

class TapsResource:
	def on_get(self, req, resp):
		resp.status = falcon.HTTP_200
		beers = fetch_beers()
		resp.body = json.dumps(beers)

app = falcon.API()
taps = TapsResource()
app.add_route('/taps', taps)
