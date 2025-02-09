import datetime; print(datetime.datetime.now())

for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

import re
bad_notes = []
field_fixer_regex = re.compile(r'[^\w\s\-\+]', re.IGNORECASE)

target_note_type_name = "English - Irregular Verbs"
target_sentence_field = "VerbExample"
target_audio_field = "VerbExampleAudio"

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.get_note(nid)
    note_type = note.note_type()

    if note_type["name"] == target_note_type_name:
        # print(f"Checking note type {note.id}...")
        example = note[target_sentence_field]
        example = field_fixer_regex.sub('', example)
        if example[0:50] not in note[target_audio_field]:
            bad_notes.append(note.id)
            print(f"Note {len(bad_notes)} {note.id}, is inconsistent:\n>>|{example}|, \n>>|{note[target_audio_field]}|.")

print("Bad notes:", end='\n')
for bad in bad_notes:
    print(f"nid:{bad} or ", end='')

print("", end='\n')
