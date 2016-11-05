foobar == a module. ex: people, events, or inventory

index: main page. list of all foobars
show: main page for a single foobar
edit: generates and returns form for editing a single foobar
update: takes the user-filled form from edit and updates DB
new: generate and returns form for creating a single foobar
create: takes the user-filled form from new and inserts into DB
delete: deletes a single foobar




two underscores before a function denotes its an internal ("private" in C++
terms) function that shouldn't be called outside of the class

__can_VERB returns Ture or False depending on whether the given session is
allowed to VERB. Sometimes takes an id as well, which is the id of the target
resource

__db_DBVERB_* will DBVERB (probably one of select, insert, update, delete
based on context) the given type of resource

__create_* is a "sub function" of create and will call __db_insert_* as needed

__update_* is a "sub function" of update and will call __db_*_* as needed
