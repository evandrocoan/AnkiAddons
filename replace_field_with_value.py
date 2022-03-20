import datetime; print(datetime.datetime.now())

for name, did in mw.col.db.execute(f"select name, id from decks"):
    print(f"Deck name {name}, did {did}.")

# AllMyDecksRootLanguagesJapaneseKana (Katakana/Hiragana)
source_deck_did = 1582942327697

target_field = "BottomButtons"

target_note_type_name = "Katakana to Hiragana"

value_to_add = \
r"""
<input id="mainsymbolkatakanabutton" type="button" value="(hiragana)" onclick="$('#mainsymbol').text('リャ');
    if(audio !== undefined &amp;&amp; !audio.paused) audio.pause();
    audio = new Audio('_ATTS Katakana(google en-us).mp3');
    audio.playbackRate = 1.4;
    audio.play();
    $('#questionsymbol').text('リャ');
    $('#questionsymbolname').text('Katakana');
    $('#answersymbol').text('Katakana');
    $('#mainsymbolkatakanabutton').hide();
    $('#mainsymbolhiraganabutton').show();">

<input id="mainsymbolhiraganabutton" type="button" style="display: none;" value="(katakana)" onclick="$('#mainsymbol').text('りゃ');
    if(audio !== undefined &amp;&amp; !audio.paused) audio.pause();
    audio = new Audio('_ATTS Hiragana(google en-us).mp3');
    audio.playbackRate = 1.4;
    audio.play();
    $('#questionsymbol').text('りゃ');
    $('#questionsymbolname').text('Hiragana');
    $('#answersymbol').text('Hiragana');
    $('#mainsymbolhiraganabutton').hide();
    $('#mainsymbolkatakanabutton').show();">

<details class="drawingposition" open="">
<summary>Drawing...</summary>
<img src="_table_how_to_draw_hiragana.svg" alt="How to draw Hiragana?">
</details>

<script>
function tryinput(event)  {
    if( $('#try').val() )
    {
        if( $('#try').val() != $('#get').val() ) {
            $('#try').css({'background-color': 'red'});
        }
        else {
            $('#try').css({'background-color': '#0f0'});
        }
    }
    else {
        $('#try').css({'background-color': 'white'});
    }
}
$('#try').on('compositionstart', tryinput);
$('#try').on('compositionend', tryinput);
$('#try').on('compositionupdate', tryinput);
$('#try').on('change', tryinput);
$('#try').on('keyup', tryinput);
$('#try').on('keydown', tryinput);
</script>
"""

for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == target_note_type_name:
        print(f"Changing note type {note.id}...")
        cards = note.cards()
        first_card = cards[0]
        deck_id = first_card.did

        if deck_id == source_deck_did:
            print(f"Changing deck {note.id}...")
            note[target_field] = value_to_add
            note.flush()
