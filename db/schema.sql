drop table if exists users;
create table users (
  id integer primary key autoincrement,
  name string not null,
  associated_user_id integer,
  is_private integer not null,
  username string,
  password string
);

drop table if exists income_categories;
create table income_categories (
  id integer primary key autoincrement,
  user_id integer not null,
  name string not null
);

drop table if exists income;
create table income (
  id integer primary key autoincrement,
  user_id integer not null,
  date integer not null,
  category_id integer not null,
  description string not null,
  account_id integer not null,
  amount string not null
);

drop table if exists expense_categories;
create table expense_categories (
  id integer primary key autoincrement,
  user_id integer not null,
  name string not null
);

drop table if exists expenses;
create table expenses (
  id integer primary key autoincrement,
  user_id integer not null,
  date integer not null,
  category_id integer not null,
  description string not null,
  account_id integer not null,
  amount string not null
);

drop table if exists accounts;
create table accounts (
  id integer primary key autoincrement,
  user_id integer not null,
  name string not null,
  balance string not null
);

drop table if exists account_transfers;
create table account_transfers (
  id integer primary key autoincrement,
  user_id integer not null,
  date integer not null,
  from_id integer not null,
  to_id integer not null,
  amount integer not null
);