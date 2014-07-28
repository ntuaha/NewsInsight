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

#自己的libaray
from MYDB import *
from READSITE import *

reload(sys) 
sys.setdefaultencoding('utf8') 


def mainprocess(d):
	d_s = d.strftime("%Y%m%d")
	worker = READSITE('../../link.info')
	worker.getFullNews(d)





def runCrawler(year,month,day,signal):
	source = 'cnyes'
	check_dt = datetime.datetime(year,month,day)
	check_dt_s = check_dt.strftime("%Y-%m-%d")

	
	if ahaDB.isRawNewsExist(check_dt_s,source) == True:
	#if False == True:
		#print "NEXT"
		print "%s 已完成"%check_dt_s
		#pass
	else:
		#print "GOGO"
		ahaDB.insertStartInfo(check_dt_s,source)
		mainprocess(check_dt)
		if ahaDB.insertEndInfo(check_dt_s,source) == True:
			print " ====> %s 完成"%check_dt
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
	start_dt = datetime.datetime(2014,01,01)
	end_dt = datetime.datetime(2014,02,01)- datetime.timedelta(days=1)
	#end_dt = datetime.datetime(2014,06,01)
	init = start_dt
	#e = datetime.date.today() - datetime.timedelta(days=1)
	#end_dt = datetime.datetime(int(e.strftime("%Y")),int(e.strftime("%m")),int(e.strftime("%d")))
	#end_dt = datetime.datetime(int(e.strftime("%Y")),int(e.strftime("%m")),int(e.strftime("%d")))
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
