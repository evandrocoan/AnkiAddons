import datetime; print(datetime.datetime.now())

target_field = 'Front'

for nid, in mw.col.db.execute(f"select id from notes where id = 1637706916492"):
    note = mw.col.getNote(nid)
    print(f"Changing deck {note.id} from '{note[target_field]}'...")

    note[target_field] = "Changed"
    note.flush()

    print(f"After changing deck {note.id} with '{note[target_field]}'...")
    break
