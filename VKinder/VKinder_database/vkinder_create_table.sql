create table if not exists user_search_settings (
	vk_user integer not null unique primary key,
	bdate integer,
	sex integer,
	city text,
	relation integer);
	
create table if not exists like_table (
	id serial primary key,
	vk_user integer not null references user_search_settings(vk_user),
	like_user integer not null);
	
create table if not exists dislike_table (
	id serial primary key,
	vk_user integer not null references user_search_settings(vk_user),
	dislike_user integer not null);

create table if not exists match_table (
	id serial primary key,
	vk_user1 integer not null references user_search_settings(vk_user),
	vk_user2 integer not null references user_search_settings(vk_user));