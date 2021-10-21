
for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

source_deck = {}
source_deck_did = 1624247053854  # All in One Kanji

field_to_index = "Kanji"

duplicated_deck = {}
note_ids_to_remove = set()

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == "Japanese Kanji":
        index_field = note[field_to_index]
        cards = note.cards()
        first_card = cards[0]
        deck_id = first_card.did

        if deck_id == source_deck_did:
            if index_field not in source_deck:
                print(f'Adding source deck {index_field}')
                source_deck[index_field] = note

            elif index_field not in duplicated_deck:
                print(f'Adding target deck {index_field}')
                duplicated_deck[index_field] = note

            else:
                raise RuntimeError(f"Invalid deck '{deck_id}' found!")

for index_field, duplicated_note in duplicated_deck.items():
    source_note = source_deck[index_field]

    for field, duplicated_value in duplicated_note.items():
            source_value = source_note[field]

            if source_value.strip() != duplicated_value.strip():
                print(f"Appending {field} = {source_note.id} + {duplicated_note.id} -> {repr(source_value)} + {repr(duplicated_value)}")
                source_note[field] = source_value + duplicated_value
                source_note.flush()
            else:
                print(f"Skipping equal field {field} = {source_note.id} -> {repr(source_value)}")

    print(f"Adding for removal {duplicated_note[field_to_index]} -> {duplicated_note.id}")
    note_ids_to_remove.add(duplicated_note.id)

mw.col.remove_notes(note_ids_to_remove)

