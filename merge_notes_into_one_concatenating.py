
for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

source_deck = {}
source_deck_did = 1624247054777  # 1_Kanji Radical

target_deck = {}
target_deck_did = 1624247053854  # All in One Kanji

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    field_to_index = "Kanji"
    note_type = note.note_type()

    if note_type["name"] == "Japanese Kanji":
        index_field = note[field_to_index]
        cards = note.cards()
        first_card = cards[0]
        deck_id = first_card.did

        if deck_id == source_deck_did:
            print(f'Adding source deck {index_field}')
            source_deck[index_field] = note

        elif deck_id == target_deck_did:
            print(f'Adding target deck {index_field}')
            target_deck[index_field] = note

        else:
            raise RuntimeError(f"Invalid deck '{deck_id}' found!")

for index_field, source_note in source_deck.items():
    if index_field in target_deck:
        target_note = target_deck[index_field]

        for field, source_value in source_note.items():
                target_value = target_note[field]

                if target_value.strip() != source_value.strip():
                    print(f"Appending {field} -> {repr(target_value)} + {repr(source_value)}")
                    target_note[field] = target_value + source_value
                    target_note.flush()

                else:
                    print(f"Skipping equal field {field} -> {repr(target_value)}")
    else:
        print(f"Skipping missing index_field {index_field}...")
