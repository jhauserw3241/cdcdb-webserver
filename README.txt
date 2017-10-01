foobar == a module. ex: people, events, or inventory

index: main page. list of all foobars
show: main page for a single foobar
edit: generates and returns form for editing a single foobar
update: takes the user - filled form from edit and updates DB
new: generate and returns form for creating a single foobar
create: takes the user - filled form from new and inserts into DB
delete: deletes a single foobar


two underscores before a function denotes its an internal("private" in C + +
                                                          terms) function that shouldn't be called outside of the class

__can_VERB returns Ture or False depending on whether the given session is
allowed to VERB. Sometimes takes an id as well, which is the id of the target
resource

__db_DBVERB_ * will DBVERB(probably one of select, insert, update, delete
                           based on context) the given type of resource

__create_ * is a "sub function" of create and will call __db_insert_ * as needed

__update_ * is a "sub function" of update and will call __db_ * _ * as needed

__validate * takes form data and returns a validated copy of it and any errors in
an array of errors. "validated" means the output data dictionary SHOULD have all
possible fields, and unspecified / empty ones SHOULD be None. The array of errors
has length of zero when there were no errors. The caller MUST NOT touch the DB
if len(errs) is not zero. For resources that have sub types, the sub - type's
validate MUST call the generic's validate. For example, a meeting is a type of
event. __validate_meeting MUST call __validate_event and pass on all data / errors
it gets from __validate_event. The generic type MAY be called 'generic' instead
of, in this example, 'event'.

Even if a validate function doesn't seem to do anything other than manually
copying a dict key - by - key, it's at least converting from an immutable dict to a
dict.
