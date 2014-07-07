NewsInsight
===========

尋找新聞中間隱藏的訊息

## 執行流程


0. 建立爬蟲目標位置

	```bash
	$ psql -d library -f ./sql/links.sql
	```

1. 建立資料表，讀入新聞資訊

	```bash
	$ python ./src/extract/read.py 
	```
2. 建立資料表，準備做分析資料表,可已經擁有特定字詞的字串寫入

	```bash
	$ psql -d library -f ./sql/feature.sql
	$ psql -d library -f ./sql/findfeature.sql
	```	

## 資料格式

請參考[Google doc](https://docs.google.com/spreadsheets/d/1crRBz8PG_0RyFh1MZCBON4ipndSpBlNzzWxc8BN9zO0/edit?usp=sharing)

## 授權

本專案試用 MIT 授權
