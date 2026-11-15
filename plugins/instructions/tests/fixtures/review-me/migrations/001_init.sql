create table accounts (id serial primary key, name text not null);
create table entries (
  id serial primary key,
  account_id integer not null references accounts (id),
  amount_cents integer not null,
  booked_on date not null
);
