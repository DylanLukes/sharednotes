-- name: create-tables#
create table if not exists shared_notes
(
    title      TEXT      not null primary key,
    content    TEXT      not null,

    created_at TIMESTAMP not null default current_timestamp,
    updated_at TIMESTAMP not null default current_timestamp
);

-- name: create-triggers#
-- Deletes the old note if the new one is newer before an insert occurs.
-- This maintains the invariant that there is only one note per title.
create trigger if not exists shared_notes_upsert_newer
    before insert
    on shared_notes
    for each row
    when (new.updated_at < ( select updated_at
                             from shared_notes
                             where title = new.title ))
begin
    select raise(abort, 'conflict: new note is older than existing note');
end;

-- name: get-note^
select *
from shared_notes
where title = :title;

-- name: put-note<!
insert into shared_notes (title, content, updated_at)
values (:title, :content, :updated_at)
on conflict (title) do update set content    = :content,
                                  updated_at = :updated_at;

-- name: delete-note!
delete
from shared_notes
where title = :title;