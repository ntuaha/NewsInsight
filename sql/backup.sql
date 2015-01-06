\copy (select * from cnyes where date_trunc('month',datetime)='2014-07-01') to '/home/aha/Project/NewsInsight/data/backup/201407.csv' WITH CSV HEADER;
\copy (select * from cnyes where date_trunc('month',datetime)='2014-08-01') to '/home/aha/Project/NewsInsight/data/backup/201408.csv' WITH CSV HEADER;
\copy (select * from cnyes where date_trunc('month',datetime)='2014-09-01') to '/home/aha/Project/NewsInsight/data/backup/201409.csv' WITH CSV HEADER;
\copy (select * from cnyes where date_trunc('month',datetime)='2014-10-01') to '/home/aha/Project/NewsInsight/data/backup/201410.csv' WITH CSV HEADER;
\copy (select * from cnyes where date_trunc('month',datetime)='2014-11-01') to '/home/aha/Project/NewsInsight/data/backup/201411.csv' WITH CSV HEADER;
\copy (select * from cnyes where date_trunc('month',datetime)='2014-12-01') to '/home/aha/Project/NewsInsight/data/backup/201412.csv' WITH CSV HEADER;
