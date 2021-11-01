
g_kanji_field = "Kanji"
g_radical_field = "Radical"

kanji_notes = {}
radical_notes = {}

def getField(field, note):
    fieldText = note[field]
    from anki.utils import stripHTML
    return stripHTML(fieldText) if fieldText else None

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == "Japanese Kanji":
        kanji_field_text = getField(g_kanji_field, note)
        radical_field_text = getField(g_radical_field, note)
        assert kanji_field_text, f"Cannot have an empty kanji field '{g_kanji_field}={kanji_field_text}'"

        if kanji_field_text == radical_field_text:
            assert radical_field_text not in radical_notes, f"Duplicated radical field found '{kanji_field_text}, {g_radical_field}={note}'"
            radical_notes[kanji_field_text] = note

        assert kanji_field_text not in kanji_notes, f"Duplicated kanji field found '{kanji_field_text}, {g_radical_field}={note}'"
        kanji_notes[kanji_field_text] = note

fields_to_fill = [
    ("Pinyin", "RadicalPinyin"),
    ("English", "RadicalEnglish"),
    ("EnglishAudio", "RadicalEnglishAudio"),
    ("ChineseSimplifiedAudio", "RadicalSound"),
]

for kanji_field_text, kanji_note in kanji_notes.items():
    for source_field, target_field in fields_to_fill:
        radical_field_text = getField(g_radical_field, kanji_note)

        if radical_field_text:
            radical_note = radical_notes[radical_field_text]
            source_field_text = radical_note[source_field]

            target_field_text = getField(target_field, kanji_note)
            if target_field_text:
                print(f"Skipping kanji '{kanji_field_text}[{target_field}]' because it is already filled!")
            else:
                print(f"Setting kanji '{kanji_field_text}[{target_field}]' with '{source_field}={source_field_text}'")
                kanji_note[target_field] = source_field_text
                kanji_note.flush()

print("Successfully completed...")
