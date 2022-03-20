import datetime; print(datetime.datetime.now())

import re
field_fixer_regex = re.compile(r'<\s*br\s*\/?\s*>.*')

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    field_to_fix = "Kanji"

    if note.note_type()["name"] == "Japanese Kanji":
        original_field = note[field_to_fix]
        fixed_field = field_fixer_regex.sub("", original_field)
        print(f"Before {original_field} -> {fixed_field}")
        note[field_to_fix] = fixed_field
        note.flush()
