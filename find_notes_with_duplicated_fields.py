
for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

source_deck_did = 1624247053854  # All in One Kanji

source_field = "Kanji"
target_field = "Kanji Radical"

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == "Japanese Kanji":
        cards = note.cards()
        first_card = cards[0]
        deck_id = first_card.did

        if deck_id == source_deck_did:
            source_value = note[source_field]
            target_value = note[target_field]

            if source_value.strip() == target_value.strip():
                print(f'Adding tag to {note.id} -> {source_value}')
                note.add_tag('japanese_radical_from_old_kanji_radical')
                note.flush()
