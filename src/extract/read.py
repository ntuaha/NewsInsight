# -*- coding: utf-8 -*- 



#import re

#處理掉unicode 和 str 在ascii上的問題
import sys 
#import os
import psycopg2
#import datetime
#import calendar
#import csv
#import math
#from time import mktime as mktime
import cookielib, urllib2,urllib
from lxml import html


reload(sys) 
sys.setdefaultencoding('utf8') 

class READSITE:
	address = None
	content = None
	cj = None
	opener = None
	def __init__(self,website):
		self.address = website

	def listLink(self):
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		#self.opener.addheaders = [('Host', 'news.cnyes.com')]
		#self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36')]
		r = self.opener.open(self.address)
		self.content = r.read()		
		r.close()
		#print content

	def parse(self):
		page = html.fromstring(self.content)
		i = 0
		for link in page.xpath('//*[@id="container"]//*[@class="list_1 bd_dbottom"]//li/a'):
			i=i+1
			print "%d Name: %s URL: %s"%(i,link.text,link.get("href"))
			l = urllib.quote(link.get("href").encode('utf-8'),safe=':/?=')			
			self.read(l)


	def read(self,address):			
		try:
			print address
			r = self.opener.open(address)
			
			page = html.fromstring(r.read())		
			r.close()
			
			#for title in page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/h1'):
			#	print title.text
			title = page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/h1')[0].text
			print title
			#(author,time) = page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/span[@class="info"]')[0].text.split("　　")
			info = page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/span[@class="info"]')[0].text
			#print author
			#print time
			print info
			article = page.xpath('//*[@id="newsText"]/p')
			fulltext =''
			for a in article:
				if a.text is not None:
					fulltext = fulltext + "\n"+a.text
			print "title:%s\n gg:%s\n article:\n%s\n"%(title,info,fulltext)
			print "\n\n\n"
		except Exception as e:
			print e

if __name__ == '__main__':
	worker = READSITE('http://news.cnyes.com/tw_bank/list.shtml')
	worker.listLink()
	worker.parse()

