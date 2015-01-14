# -*- coding: utf-8 -*-

import re
import sys
import os
import psycopg2
import cookielib, urllib2,urllib
from lxml import html,etree
import lxml
import StringIO
import datetime
import json
#處理掉unicode 和 str 在ascii上的問題
reload(sys)
sys.setdefaultencoding('utf8')

from pymongo import ASCENDING, DESCENDING
#aha's library
from WEB import WEB
from RAW_DB import RAW_DB



class PTT_DB(RAW_DB):
  db = "ptt"
  table = "loan"
  def __init__(self,path):
    RAW_DB.__init__(self,path,self.db)
    self.table = self.db[self.table]

  def isExistNews(self,record):
    if self.table.find({'link':record['link']}).count()>0:
      return True
    else:
      return False

  def bulkInsertNews(self,news):
    insert_data = []
    for n in news:
      if self.isExistNews(n) ==False:
        insert_data.append(n)
        #print n
      else:
        print "%s"% (n["link"])
    count = len(insert_data)
    if count >0:
      self.table.insert(insert_data)
      #Build index
      #self.table.create_index([("link", DESCENDING), ("Title", ASCENDING)])
    #Insert to LOG
    self.db["log"].insert({"crawler_dt":datetime.datetime.now(),"modified_record":count,"source":"ptt_loan"})
    return count


class PTT_LOAN:
  def __init__(self):
    self.web = WEB()

  def getRawData(self,url):
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'over18=1'))
    response = opener.open(url)
    the_page = response.read()
    response.close()
    return the_page



  def fetchListDOM(self,url):
    the_page = self.getRawData(url)
    # 將網頁轉成結構化資料
    parser = etree.HTMLParser()
    root = etree.parse(StringIO.StringIO(the_page),parser)
    # 抓指定位置的連結

    link = root.xpath(u".//div[contains(@class, 'btn-group pull-right')]//a[contains(text(),'‹ 上頁')]/@href")
    if link is not None:
      return [root.xpath(".//*[contains(@class, 'r-ent')]"),"https://www.ptt.cc"+link[0]]
    else:
      return [root.xpath(".//*[contains(@class, 'r-ent')]"),None]

  def fetchListPage(self,url):
    print url
    rows,prev = self.fetchListDOM(url)
    rows_cnt = len(rows)
    links = []
    for row in rows:
      datum = {}
      datum['author'] = row.xpath(".//*[contains(@class, 'author')]")[0].text.strip()
      if datum['author'] =='-':
        continue
      temp = row.xpath(".//*[contains(@class, 'title')]/a")[0].text.strip()
      print "title: %s"%temp
      #猜是主文
      m = re.match(u"\[(\w+)\](.*)",temp,re.U)
      if m is not None:
        datum['category'] = m.group(1).strip()
        datum['title'] = m.group(2).strip()
        datum['article_leader']= 1
      else:
        #猜是回文
        m = re.match(u"Re:.*\[(\w+)\](.*)",temp,re.U)
        if m is not None:
          datum['category'] = m.group(1).strip()
          datum['title'] = m.group(2).strip()
          datum['article_leader']= 0
        else:
          datum['title'] = temp
      datum['link'] = "https://www.ptt.cc"+row.xpath(".//*[contains(@class, 'title')]/a/@href")[0]
      month,day = map(int,rows[0].xpath(".//*[contains(@class, 'date')]")[0].text.strip().split("/"))
      if datetime.datetime.now().month < month:
        year = datetime.datetime.now().year-1
      else:
        year = datetime.datetime.now().year
      datum['date'] = datetime.datetime(year,month,day)
      datum['author'] = row.xpath(".//*[contains(@class, 'author')]")[0].text.strip()

      nrec = row.xpath(".//*[contains(@class, 'nrec')]/span//text()")
      if len(nrec)>0:
        datum['nrec'] = int(nrec[0].strip())
      else:
        datum['nrec'] = 0
      mark = row.xpath(".//*[contains(@class, 'mark')]//text()")
      if len(mark)>0:
        datum['mark'] = mark[0].strip()
      links.append(datum)

    return (links,prev)


  def fetchContent(self,url):
      print url
      the_page = self.getRawData(url)
      parser = etree.HTMLParser()
      root = etree.parse(StringIO.StringIO(the_page),parser)
      datum = {}
      #作者與心情
      temp = root.xpath(u'.//div[@class="article-metaline" and span[@class="article-meta-tag"]="作者"]/span[@class="article-meta-value"]/text()')
      datum['author']=""
      datum['mood']=""
      if temp is not None:
        m = re.match(u"(\w+) \((.*)\)",temp[0].strip(),re.U)
        datum['author'] = m.group(1).strip()
        datum['mood'] = m.group(2).strip()

      #article time
      temp = root.xpath(u'.//div[@class="article-metaline" and span[@class="article-meta-tag"]="時間"]/span[@class="article-meta-value"]/text()')
      datum['edittime'] = []
      if temp is not None:
        datum['edittime'].append(datetime.datetime.strptime(temp[0].strip(),'%a %b %d %H:%M:%S %Y'))


      #push
      pushs = root.xpath(".//div[@class='push']")
      datum['pushs'] = []
      if pushs is not None:
        for push in pushs:
          p = {}
          tag = push.xpath('.//span[contains(@class,"push-tag")]//text()')[0].strip()
          if tag =='推':
            p['tag'] = 1
          elif tag =='噓':
            p['tag'] = -1
          else:
            p['tag'] =0
          p['user'] = push.xpath('.//span[contains(@class,"push-userid")]//text()')[0].strip()
          p['content'] = push.xpath('.//span[contains(@class,"push-content")]//text()')[0].replace(": ","").strip()


          ipdatetime = push.xpath('.//span[contains(@class,"push-ipdatetime")]//text()')[0].strip()
          # push-time
          m = re.match(u"(\d{2}/\d{2} \d{2}:\d{2})",ipdatetime,re.U)
          if m is not None:
            p['time'] = datetime.datetime.strptime(m.group(1),'%m/%d %H:%M')
          # push-ip
          m = re.match(u"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",ipdatetime,re.U)
          if m is not None:
            p['ip'] = m.group(1)
          datum['pushs'].append(p)

      #content && footer
      datum['author_ip'] = []
      datum['content'] = []
      contents = root.xpath(".//div[@id='main-content']/node()[not(@class='article-metaline' or @class='article-metaline-right' or @class='push')]")
      for content in contents:
        color = ""
        text = ""
        if type(content) == lxml.etree._Element:
          #link
          if len(content.xpath("./@href"))>0:
            datum['content'].append({'color':'','text':content.xpath("./@href")[0].strip()})
            continue

          c_class = content.xpath("./@class")
          if c_class is not None:
            c_class = c_class[0].strip()
          else:
            c_class =''

          text = content.xpath("./text()")
          if text is not None:
            text = text[0].strip()
          else:
            text = ''

          #可能是結尾
          if c_class =='f2':
            #跳過
            m = re.match(u"※ 文章網址:",text,re.U)
            if m is not None:
              continue
            #找發文IP
            m = re.match(u"※ 發信站: 批踢踢實業坊\(ptt.cc\), 來自: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",text,re.U)
            if m is not None:
              datum['author_ip'].append(m.group(1))
              continue
            m = re.match(u"※ 編輯: \w+ \((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\), (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})",text,re.U)
            if m is not None:
              datum['author_ip'].append(m.group(1))
              datum['edittime'].append(datetime.datetime.strptime(m.group(2),'%m/%d/%Y %H:%M:%S'))
              continue
          elif c_class=='hl':
            m = re.match(u"◆ From: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",text,re.U)
            if m is not None:
              datum['author_ip'].append(m.group(1))
              continue
          #都不是就放出
          datum['content'].append({'color':c_class,'text':text})

        elif type(content) == lxml.etree._ElementUnicodeResult or type(content) == lxml.etree._ElementStringResult:
          datum['content'].append({'color':'','text':content.replace("\n\n","\n").strip()})
        else:
          raise 'ERROR TYPE'

      return datum


  def fetchData(self,time,limit=0):
    total_links = []
    jump = False
    url = 'https://www.ptt.cc/bbs/Loan/index.html'
    count = 0
    page = 0
    while 1:
      links,url = self.fetchListPage(url)
      print "url: "+url
      if url is None:
        break

      i = 0
      for l in links:
        i = i+1
        count = count+1
        #太早的新聞出現
        print page
        if i==1 and l['date'] <time and page>0:
          print i
          print l['date']
          print time
          print page
          jump = True
        else:

          d = self.fetchContent(l['link'])
          for key,value in d.iteritems():
            l[key] = value
#            print "%s,%s"%(key,value)
          total_links.append(l)


      if jump == True or (limit>0 and count>=limit):
        break
      else:
        page = page+1
    return total_links



def show(rows):
  for post in posts:
    print "=============="
    for k,v in post.iteritems():
      if k!='content' and k!='pushs':
        print '%s:%s'%(k,v)
      elif k=='content':
        for c in v:
          print "%s:%s"%(c['color'],c['text'])
      elif k=='pushs':
        for c in v:
          print "%s:%s:%s:%s"%(c['user'],c['ip'],c['tag'],c['content'])


if __name__ =="__main__":
  ptt = PTT_LOAN()
  db = PTT_DB(os.path.dirname(__file__)+"/mongodb.inf")
  now = datetime.datetime.now()
  t = datetime.datetime(now.year,now.month,now.day) - datetime.timedelta(days=1)
  print t
  if len(sys.argv)>1:
    limit = int(sys.argv[1])
  else:
    limit = 0
  posts = ptt.fetchData(t,limit)



  #Append News
  print db.bulkInsertNews(posts)

