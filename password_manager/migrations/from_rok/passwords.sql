with pwd_src as (
	select
		id,
		not completed as active,
		name as title,
		store_username as login,
		store_value as value,
		created as create_date,
		info
	from task_task 
	where app_store = 4
)
, pwd_split as (
	select
		id,
		string_to_table(info, chr(10)) as info
	from pwd_src 
)
, pwd_agg as (
	select
		id,
		concat('<div data-oe-version="1.2">', string_agg(info, '</div><div>'), '</div>') as info
	from pwd_split 
	where length(info) > 0
	group by
		id
)
, pwd as (
	select
		p.id,
		p.active,
		p.title,
		p.login,
		p.value,
		p.create_date,
		a.info
	from pwd_src p 
	left join pwd_agg a
		on p.id = a.id
)
, pwd_grp as (
	select
		tg.group_id as category_id,
		concat('All',
			case when g4.id is null then '' else concat(' / ', g4.name) end,
			case when g3.id is null then '' else concat(' / ', g3.name) end,
			case when g2.id is null then '' else concat(' / ', g2.name) end,
			case when g1.id is null then '' else concat(' / ', g1.name) end) as category_name,
		pwd.*
	from pwd
	left join task_taskgroup tg
		on pwd.id = tg.task_id
	left join task_group g1
		on tg.group_id = g1.id
	left join task_group g2
		on g1.node_id = g2.id
	left join task_group g3
		on g2.node_id = g3.id
	left join task_group g4
		on g3.node_id = g4.id
)
, grp as (
	select distinct category_id, category_name
	from pwd_grp
	where category_id is not null
	order by category_name
)
select * from pwd_grp
-- select * from grp
