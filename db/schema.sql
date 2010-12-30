drop table if exists users;
create table users (
  id integer primary key autoincrement,
  username string not null,
  password string not null
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
  amount string not null
);