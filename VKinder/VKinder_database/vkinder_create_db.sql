create database vkinder;

create user vkinder with password 'ZAQxsw654123!';
alter role vkinder superuser createdb createrole inherit login;

alter database vkinder owner to vkinder;