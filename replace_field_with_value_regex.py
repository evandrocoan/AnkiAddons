import re
import datetime; print(datetime.datetime.now())

for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

# Kana (Katakana/Hiragana)
source_deck_did = 1624247053854

target_field = "Onyomi"

target_note_type_name = "Japanese Kanji"

value_replace = r""

replace_search = re.compile(r"""^なし""")

condition_field = r"EnglishAudio"
condition_search = re.compile(r"""\]\[""")

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == target_note_type_name:
        # print(f"Changing note type {note.id}...")
        cards = note.cards()
        first_card = cards[0]
        deck_id = first_card.did

        if deck_id == source_deck_did:
            old_text = note[target_field]
            condition_text = note[condition_field]

            condition_match = condition_search.search(condition_text)
            if not condition_match:
                # print(f"Skipping note {note.id} '{old_text}' -> '{condition_text}'...")
                continue

            replace_match = replace_search.search(old_text)
            if replace_match:
                new_text = replace_search.sub(value_replace, old_text)
                print(f"Changing note {note.id} '{old_text}' -> '{replace_match.group(0)}' -> '{new_text}'...")
                note[target_field] = new_text
                note.flush()
