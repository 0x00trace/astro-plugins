-- The monthly totals query filters entries by account.
create index entries_account_id on entries (account_id);
