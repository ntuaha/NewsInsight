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

class MYDB:
	database=""
	user=""
	password=""
	host=""
	port=""
	conn = None
	cur = None
	def __init__(self,filepath):
		f = open(filepath,'r')
		self.database = f.readline()[:-1]
		self.user = f.readline()[:-1]
		self.password = f.readline()[:-1]
		self.host = f.readline()[:-1]
		self.port =f.readline()[:-1]
		f.close()
		self.startDB()
	#啟用DB
	def startDB(self):
		self.conn = psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)
		self.cur = self.conn.cursor()	

	def isRawNewsExist(self,t,s):
		sql = "SELECT count(*) from crawler_record where data_dt='%s' and source='%s' and end_time is not NULL"%(t,s)
		#print sql
		self.cur.execute(sql)
		rows = self.cur.fetchall()
		if rows[0][0] >0:
			return True
		else:
			return False

	def insertStartInfo(self,t,s):
		# Clear OLD
		sql = "DELETE from crawler_record where data_dt='%s' and source='%s';"%(t,s)
		self.cur.execute(sql)
		self.conn.commit()
		sql = "DELETE from %s where date_trunc('day',datetime) = '%s';"%(s,t)
		self.cur.execute(sql)
		self.conn.commit()
		# Insert Info
		sql  = "INSERT INTO crawler_record (source,data_dt,start_time) VALUES ('%s','%s',NOW())"%(s,t)
		self.cur.execute(sql)
		self.conn.commit()

	def insertEndInfo(self,t,s):
		sql  = "SELECT count(*) from %s where date_trunc('day',datetime) = '%s';"%(s,t)
		self.cur.execute(sql)
		data_num  = self.cur.fetchall()[0][0]
		if data_num !=0:
			sql  = "UPDATE crawler_record SET end_time=NOW(),newscount = %d ,process_time = NOW()-start_time, avg_speed = date_trunc('sec',NOW()-start_time)/%d  where data_dt='%s' and source='%s';"%(data_num,data_num,t,s)
		else:
			sql = "UPDATE crawler_record SET end_time=NOW(),newscount = %d ,process_time = NOW()-start_time  where data_dt='%s' and source='%s';"%(data_num,t,s)
		#print sql
		self.cur.execute(sql)
		self.conn.commit()
		#sendtoFB(t,data_num,speed)


		return True
	def sendtoFB(self,year,month,source):
		sql = "SELECT sum(newscount),sum(extract(epoch from avg_speed))/sum(newscount) from crawler_record where date_trunc('month',data_dt)='%04d-%02d-01' and source='%s';"%(year,month,source)
		#print sql
		self.cur.execute(sql)
		(data_num,speed)  = self.cur.fetchall()[0]
		sendtoFB("%04d年%02d月"%(year,month),data_num,speed)





	#結束DB
	def endDB(self):	
		self.conn.close()


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
			print "\r%s  [%d /%d](%3.0f%%)"%(d.strftime("%Y-%m-%d"),n,total,n/float(total)*100),
			sys.stdout.flush()
  
			title = link.xpath('./NEWSTITLE')[0].text
			ll = 'http://news.cnyes.com'+link.xpath('./SNewsSavePath')[0].text
			typ = link.xpath('./ClassCName')[0].text
			time = d.strftime("%Y-%m-%d")+" "+link.xpath('./NewsTime')[0].text

			result = self.read(ll)
			if result != self.EMPTYNEWS:
				(author,datetime,title,info,fulltext,source) = result
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
		#try:
		#print address
		#r = self.opener.open(address)	
		r = urllib2.build_opener().open(address)



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
	#	print fulltext
		#print "title:%s\n gg:%s\n article:\n%s\n"%(title,info,fulltext)
		#print "\n\n\n"

		#return infromation in the page
		return (author,datetime,title,info,fulltext,source)
		#except Exception as e:
		#	print e
		

def mainprocess(d):
	d_s = d.strftime("%Y%m%d")
	worker = READSITE('../../link.info')
	worker.getFullNews(d)


def sendtoFB(d,num,speed):
	Title = "完成"
	Result = "成功"
	print num
	print speed
	Detail = "%s 新聞資料獲得，得到%d筆,每筆約花%.02f秒"%(d,num,speed)
	api = '688430041191592'; 
	api_secret = '6bb097ca9fe10f1bca0c1c320232eba2';
	callback_website = 'https://github.com/ntuaha/TWFS/';
	picture_url_tick = 'http://www.iconarchive.com/icons/pixelmixer/basic/64/tick-icon.png';
	facebook_id = '100000185149998';
	cmd = os.popen("/usr/bin/curl -F grant_type=client_credentials -F client_id=%s -F client_secret=%s -k https://graph.facebook.com/oauth/access_token"%(api,api_secret))
	k = cmd.read()
	access_token = k.split("=")[1] 
	work = "/usr/bin/curl -F 'access_token=%s' -F 'message=%s' -F 'name=%s' -F 'picture=%s' -F 'caption=%s' -k https://graph.facebook.com/%s/feed"%(access_token,Detail,Title,picture_url_tick,Result,facebook_id)
	#print work
	cmd = os.popen(work)



def runCrawler(year,month,day,signal):
	source = 'cnyes'
	check_dt = datetime.datetime(year,month,day)
	check_dt_s = check_dt.strftime("%Y-%m-%d")

	
	if ahaDB.isRawNewsExist(check_dt_s,source) == True:
	#if False == True:
		#print "NEXT"
		pass
	else:
		#print "GOGO"
		ahaDB.insertStartInfo(check_dt_s,source)
		mainprocess(check_dt)
		if ahaDB.insertEndInfo(check_dt_s,source) == True:
			#print "GOOD %s"%check_dt
			if signal==True:
				ahaDB.sendtoFB(year,month,source)
			else:
				pass


if __name__ == '__main__':
	#http://news.cnyes.com/tw_bank/sonews_2014010120140708_1.htm
	#for month in xrange(1,7):
	#type_list =  ["INDEX","fx_liveanal","macro"]
	#type_list =  ["macro"]
	#rebuildTable = True
	rebuildTable = False

# 確認時間
	ahaDB = MYDB('../../link.info')
	start_dt = datetime.datetime(2014,07,01)
	init = start_dt
	e = datetime.date.today() - datetime.timedelta(days=1)
	end_dt = datetime.datetime(int(e.strftime("%Y")),int(e.strftime("%m")),int(e.strftime("%d")))
	#print end_dt.strftime("%Y-%m-%d")
	#end_dt = datetime.datetime(2014,07,26)
	sendFinalSignal = False
	while init<=end_dt:
	#while 2<1:
		if init==end_dt:
			sendFinalSignal=True
			#pass

		year = int(init.strftime("%Y"))
		month = int(init.strftime("%m"))
		day = int(init.strftime("%d"))
		runCrawler(year,month,day,sendFinalSignal)
		init = init + datetime.timedelta(days=1)
	ahaDB.endDB()

'''
	for item in type_list:
		print item
		start_dt =  datetime.datetime(2014,4,23)
		init_dt = start_dt
		end_dt = datetime.datetime(2014,6,30)
		
		while (start_dt <= end_dt ):
			start_dt_s = start_dt.strftime("%Y%m%d")
			end_dt_s = (start_dt+datetime.timedelta(days=6)).strftime("%Y%m%d")
			
			#print start_dt
			#print 'http://news.cnyes.com/tw_bank/sonews_%s%s_1.htm'%(start_dt,end_dt)
			#print 'http://news.cnyes.com/fx_liveanal/sonews_%s%s_1.htm'%(start_dt_s,start_dt_s)
			print 'http://news.cnyes.com/%s/sonews_%s%s_1.htm'%(item,start_dt_s,end_dt_s)
			worker = READSITE('http://news.cnyes.com/%s/sonews_%s%s_1.htm'%(item,start_dt_s,end_dt_s),'../../link.info')
			if rebuildTable == True:
				worker.rebuildTable('../../sql/cnYes.sql')
				rebuildTable = False
			worker.listLink()
			start_dt  = start_dt+datetime.timedelta(days=7)
			#worker.parse()
'''
