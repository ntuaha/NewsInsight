# -*- coding: utf-8 -*- 



import re

#處理掉unicode 和 str 在ascii上的問題
import sys 
import os
import psycopg2
import datetime
#import calendar
#import csv
#import math
#from time import mktime as mktime
import cookielib, urllib2,urllib
from lxml import html,etree
import StringIO


reload(sys) 
sys.setdefaultencoding('utf8') 





class READSITE:
	content = None
	cj = None
	opener = None

	database=""
	user=""
	password=""
	host=""
	port=""
	conn = None
	table = "cnyes"
	cur = None
	EMPTYNEWS = ("","","","","","")


	def __init__(self,filepath):
		f = open(filepath,'r')
		self.database = f.readline()[:-1]
		self.user = f.readline()[:-1]
		self.password = f.readline()[:-1]
		self.host = f.readline()[:-1]
		self.port =f.readline()[:-1]
		f.close()

	#建立更新資料庫
	def rebuildTable(self,sql):
		print '執行重建Table'
		os.system('psql -d %s -f %s'%(self.database,sql))



	def getFullNews(self,d):
		#self.cj = cookielib.CookieJar()
		#self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		#self.opener.addheaders = [('Host', 'news.cnyes.com')]
		#self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36')]




		
		self.startDB()
		self.cur = self.conn.cursor()	
		# History Page's example
		# http://news.cnyes.com/rollnews/2014-07-01.htm

		url = 'http://news.cnyes.com/Ajax.aspx?Module=GetRollNews'
		value = urllib.urlencode( {'date' : d.strftime("%Y%m%d")})

		response = urllib2.build_opener().open(url,value)
		the_page = response.read()
		response.close()		
		page = etree.parse(StringIO.StringIO(the_page))
		total =  len(page.xpath('/NewDataSet/Table1'))

		n = 0 
		for link in page.xpath('/NewDataSet/Table1'):
			n += 1
			#if n<=1236:
			#	continue
			print "\r%s  [%d /%d](%3.0f%%)"%(d.strftime("%Y-%m-%d"),n,total,n/float(total)*100),
			sys.stdout.flush()
  			#print str(etree.dump(link))
  			title_obj = link.xpath('./NEWSTITLE')[0].text
  			if title_obj is None:
  				continue
  			else:
				title = title_obj.replace(u"'", u"''")
			ll = 'http://news.cnyes.com'+link.xpath('./SNewsSavePath')[0].text
			typ = link.xpath('./ClassCName')[0].text
			time = d.strftime("%Y-%m-%d")+" "+link.xpath('./NewsTime')[0].text

			result = self.read(ll)
			if result != self.EMPTYNEWS:
				(author,datetime,title2,info,fulltext,source) = result
				self.insertDB((ll,typ,title,info,fulltext,author,time,source))
			#break

		self.cur.close()
		self.endDB()







	def readLink(self,address):
		#self.cj = cookielib.CookieJar()
		#self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		#self.opener.addheaders = [('Host', 'news.cnyes.com')]
		#self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36')]
		print address
		r = self.opener.open(address)
		self.content = r.read()		
		r.close()
		self.parse()


	#啟用DB
	def startDB(self):
		self.conn = psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)

	#結束DB
	def endDB(self):	
		self.conn.close()

	def insertDB(self,data):

		data = (self.table,) + data
		sql = "INSERT INTO %s (link,type,title,info,content,author,datetime,source) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s');"%(data)
		#print sql
		#try:
		self.cur.execute(sql)
		self.conn.commit()
		#except Exception as e:
		#	print e


	#讀入單頁資訊
	def read(self,address):			
		try:
			r = urllib2.build_opener().open(address)
		except urllib2.URLError:
			print "URLError=>address: %s"%address
			return self.EMPTYNEWS

		page = html.fromstring(r.read().decode('utf-8'))				
		r.close()
		#處理頁面錯誤問題
		if len(page.xpath('//*[@id="form1"]//center/h2'))!=0:		
			return self.EMPTYNEWS
		
		#extract title from content
		title = page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/h1')[0].text
		#extract info from content
		info = page.xpath('//*[@class="newsContent bg_newsPage_Lblue"]/span[@class="info"]')[0].text
		#print info
		
		#extract datetime from info
		year,month,day,hour,mins = re.match(".*(\d{4})-(\d{2})-(\d{2})\W*(\d{2}):(\d{2})", info,re.U).group(1,2,3,4,5)
		datetime = "%s-%s-%s %s:%s"%(year,month,day,hour,mins)
		#print "info: "+ info

		#extract author from info
		if re.match(u"鉅亨網新聞中心",info,re.U) is not None:
			author = "新聞中心"
		elif re.match(u"鉅亨台北資料中心",info,re.U) is not None:
			author = "台北資料中心"
		elif re.match(u"鉅亨網\W+.+",info,re.U) is not None:
			author = ""
		elif re.match(u".+記者(\w+)\W+.+",info,re.U) is not None:
			author = re.match(u".+記者(\w+)\W+.+",info,re.U).group(1)
		elif re.match(u".+編譯(\w+)\W+.+",info,re.U) is not None:
			author = re.match(u".+網編譯(\w+)\W+.+",info,re.U).group(1)
		elif re.match(u"鉅亨網(\w+)\W+.+",info,re.U) is not None:
			author = re.match(u"鉅亨網(\w+)\W+.+",info,re.U).group(1)
		elif re.match(u"(\w+)\W+.+",info,re.U) is not None:			
			author = re.match(u"(\w+)\W+.+",info,re.U).group(1)
		#print "author:%s "%author

		#extract source from info 
		source = ""
		pattern = re.match(u".+\W+\(來源：(.+)\)\W+.+",info,re.U) 
		if pattern is not None:
			source = pattern.group(1)
		#print "source: "+source
		
		#extract fulltext from content
		article = page.xpath('//*[@id="newsText"]/p')
		fulltext =''
		text = []
		for a in article:
			if a.text is not None:
				text.append(a.text)
		fulltext = "\n".join(text).replace(u"'", u"''")


		return (author,datetime,title,info,fulltext,source)
