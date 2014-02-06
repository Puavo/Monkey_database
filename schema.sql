drop table if exists entries;
create table entries (
  id integer auto increment,
  name text not null,
  age integer not null,
  mail text primary key,
  friend integer default 0,
  text text,
  best text,
  foreign key(best) references entries(mail) on update cascade on delete set null
);

drop table if exists friends;
create table friends (
  mail1 text not null,
  mail2 text not null,
  foreign key(mail1) references entries(mail) on update cascade on delete cascade,
  foreign key(mail2) references entries(mail) on update cascade on delete cascade,
  primary key (mail1, mail2)
);
