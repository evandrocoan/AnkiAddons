# Jisho.org Support for Anki

import os, re, json, requests, urllib.request, urllib.parse

from aqt import gui_hooks
from aqt import mw
from aqt.qt import qconnect
from aqt.editor import Editor
from aqt.utils import showInfo
from anki.utils import strip_html
from anki.media import media_paths_from_col_path


# config
config = mw.addonManager.getConfig(__name__)


# editor_will_show_context_menu hook
def on_context_menu(editor_webview, menu):
    #
    editor: Editor = editor_webview.editor
    current_field: Optional[int] = editor.currentField

    if current_field is not None:
        for field_index, field_name in enumerate(mw.col.models.fieldNames(editor.note.model())):
            if field_index == current_field and (field_name == config['field_name_expression'] or field_name == config['field_name_meaning']):
                search = strip_html(mw.col.media.strip(editor.note[field_name]))
                if search:
                    action = menu.addAction(_(f"Jisho Automatic Card Generation"))
                    qconnect(action.triggered, lambda: fill_note_fields_using_jisho(editor, search))
                    

# fill_note_fields_using jisho.org with given search term
def fill_note_fields_using_jisho(editor: Editor, search):
    # 
    jisho_search_api_url = 'http://jisho.org/api/v1/search/words?keyword='
    
    # make url conform to ascii
    encoded_url = jisho_search_api_url + urllib.parse.quote(search.encode('utf8'))
    try:
        response = urllib.request.urlopen(encoded_url).read()
        parsed_json = json.loads(response)
    except IOError:
        showInfo("You must have an active internet connection to use automatic card generation.")
        try_clear_all_fields(editor.note)
        return False

    # exit if nothing useful came back
    try: 
        api_status_code = parsed_json['meta']['status']
        if api_status_code != 200:
            showInfo(f"api_status_code HTTPError {str(api_status_code)}")
            try_clear_all_fields(editor.note)
            return False
        has_data = parsed_json['data'][0]
    except IndexError:
        showInfo(f"Jisho.org returned no data for '{search}'")
        try_clear_all_fields(editor.note)
        return False
    
    slug = ""
    is_common: Optional[bool] = None
    slug_tags = []
    jlpt = []
    
    japanese = []
    japanese_word = ""
    japanese_reading = ""
    
    senses = []
    english_definitions = []
    parts_of_speech = []
    tags = []
    restrictions = []
    see_also = []
    antonyms = []
    info = []
    
    # Get slug
    try:
        slug = parsed_json['data'][0]['slug']
    except (IndexError, KeyError):
        pass
        
    # Get is_common
    try:
        is_common = parsed_json['data'][0]['is_common']
    except (IndexError, KeyError):
        pass
        
    # Get slug_tags
    try:
        slug_tags = parsed_json['data'][0]['tags']
    except (IndexError, KeyError):
        pass
        
    # Get jlpt
    try:
        jlpt = parsed_json['data'][0]['jlpt']
    except (IndexError, KeyError):
        pass 

        
     # Get japanese
    try:
        japanese = parsed_json['data'][0]['japanese']
    except (IndexError, KeyError):
        pass
        
    # Get japanese_word
    try:
        japanese_word = parsed_json['data'][0]['japanese'][0]['word']
    except (IndexError, KeyError):
        pass
        
    # Get japanese_reading
    try:
        japanese_reading = parsed_json['data'][0]['japanese'][0]['reading']
    except (IndexError, KeyError):
        pass
    
    
    # Get senses
    try:
        senses = parsed_json['data'][0]['senses']
    except (IndexError, KeyError):
        pass
        
    for sense in senses:
        english_definitions.append(sense['english_definitions'])
        parts_of_speech.append(sense['parts_of_speech'])
        tags.append(sense['tags'])
        restrictions.append(sense['restrictions'])
        see_also.append(sense['see_also'])
        antonyms.append(sense['antonyms'])
        info.append(sense['info'])
    
    # clear fields before we fill them 
    # so that multiple searches on the same card don't contain partial data from previous searches
    try_clear_all_fields(editor.note) 
    
    # fill fields
    # field_name_expression, field_name_jisho_reading
    try_set_field(editor.note, config['field_name_expression'], japanese_word)
    try_set_field(editor.note, config['field_name_jisho_reading'], japanese_reading)
    # field_name_other_expression, field_name_other_jisho_reading
    try:
        for index, other in enumerate(japanese):
            if index > 0:
                suffix = str(index - 1) if index - 1 > 0 else ""
                try_set_field(editor.note, config['field_name_other_expression'] + suffix, other['word'])
                try_set_field(editor.note, config['field_name_other_jisho_reading'] + suffix, other['reading'])
    except KeyError:
        pass

    try_set_field(editor.note, config['field_json_info'], str(parsed_json['data']))

    # field_name_meaning
    try_set_all_field(editor.note, config['field_name_meaning'], english_definitions)
    # field_name_part_of_speech
    try_set_all_field(editor.note, config['field_name_part_of_speech'], parts_of_speech)
    # field_name_tags
    try_set_all_field(editor.note, config['field_name_tags'], tags)    
    # field_name_restrictions
    try_set_all_field(editor.note, config['field_name_restrictions'], restrictions)    
    # field_name_see_also
    try_set_all_field(editor.note, config['field_name_see_also'], see_also)    
    # field_name_antonyms
    try_set_all_field(editor.note, config['field_name_antonyms'], antonyms)
    # field_name_info
    try_set_all_field(editor.note, config['field_name_info'], info)

    
    if config['field_name_sound'] in editor.note:
        # download_audio
        audio_url = try_get_audio_url(search)
        if audio_url is not None:
            result = try_download_audio(audio_url, japanese_reading)
            if result == True:
                try_set_sound_field(editor.note, config['field_name_sound'], japanese_reading)
    
    # refresh
    editor.loadNote()


# try_set_field 'field_name' to given value
def try_set_field(note, field_name, value):
    #
    if len(value) > 0:
        try:
            note[field_name] = value
        except KeyError:
            pass

# try_set_all_fields with 'field_name' to given values in value_list
def try_set_all_field(note, field_name, value_list):
    #
    for index, value in enumerate(value_list):
        suffix = str(index) if index > 0 else ""
        try_set_field(note, field_name + suffix, ', '.join(value))

# try_clear_field 'field_name'
def try_clear_field(note, field_name):
    #
    try:
        note[field_name] = ""
    except KeyError:
        pass


# try_clear_all_fields
def try_clear_all_fields(note):
    #
    try_clear_field(note, config['field_name_expression'])
    try_clear_field(note, config['field_name_reading'])
    try_clear_field(note, config['field_name_jisho_reading'])
    try_clear_field(note, config['field_name_sound'])
    for i in range(10):
        suffix = str(i) if i > 0 else ""        
        try_clear_field(note, config['field_name_meaning'] + suffix)
        try_clear_field(note, config['field_name_part_of_speech'] + suffix)
        try_clear_field(note, config['field_name_tags'] + suffix)
        try_clear_field(note, config['field_name_restrictions'] + suffix)
        try_clear_field(note, config['field_name_see_also'] + suffix)
        try_clear_field(note, config['field_name_antonyms'] + suffix)
        try_clear_field(note, config['field_name_info'] + suffix)
        try_clear_field(note, config['field_name_other_expression'] + suffix)
        try_clear_field(note, config['field_name_other_jisho_reading'] + suffix)


# try_get_audio_url
def try_get_audio_url(search):
    #
    try:
        jisho_search_url = 'https://jisho.org/search/'
        result = requests.get(jisho_search_url + urllib.parse.quote(search.encode('utf8')))
        result.raise_for_status()
        audio_url = re.search(r'(//[a-zA-Z0-9]+\.cloudfront.net/audio(?:_ogg)?/[a-zA-Z0-9]+\.(?:mp3|ogg))', result.text)
        if audio_url:
            return 'https:' + audio_url.group(0)
        return None
    except requests.exceptions.HTTPError:
        showInfo(f"try_get_audio_url HTTPError {str(result.status_code)}")
        pass

# try_download_audio from audio_url to collection.media folder using desired_name as filename
def try_download_audio(audio_url, desired_name):
    #    
    media_dir = media_paths_from_col_path(mw.col.path)[0]
    path_to_file = os.path.join(media_dir, os.path.basename(desired_name + '.mp3'))
    if os.path.isfile(path_to_file):
        # file already exists
        return True;
    try:
        result = requests.get(audio_url, stream=True)
        result.raise_for_status()
        with open(path_to_file, 'wb') as file:
            for chunk in result:
                file.write(chunk)
        return True
    except requests.exceptions.HTTPError:
        showInfo(f"try_download_audio HTTPError {str(result.status_code)}")
        pass
    return False


# try_set_sound_field
def try_set_sound_field(note, field_name, value):
    #
    try:
        note[field_name] = f"[sound:{value}.mp3]"
    except KeyError:
        pass


# editor_will_show_context_menu hook
gui_hooks.editor_will_show_context_menu.append(on_context_menu)
