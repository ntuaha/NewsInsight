create temporary table A as select sum(case when content like '%人民幣%' then 1 else 0 end ) as Score,'CNY' as Currency,date_trunc('day',datetime) as Data_Dt from cnYes group by Data_Dt,Currency;
insert into feature (data_dt,currency,score)  (select data_dt,currency,score from A order by data_dt);
create temporary table B as select sum(case when content like '%美金%' or content like '%美元%' then 1 else 0 end ) as Score,'USD' as Currency,date_trunc('day',datetime) as Data_Dt from cnYes group by Data_Dt,Currency;
insert into feature (data_dt,currency,score)  (select data_dt,currency,score from B order by data_Dt);
