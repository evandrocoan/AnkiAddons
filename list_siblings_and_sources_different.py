
def getField(field, note):
    fieldText = note[field]
    from anki.utils import stripHTML
    return stripHTML(fieldText) if fieldText else None


for nid, in mw.col.db.execute(f"select id from notes"):
    note = mw.col.getNote(nid)
    note_type = note.note_type()

    if note_type["name"] == "Katakana to Hiragana":
        source = getField("Source", note)
        sibling = getField("Sibling", note)

        if source and sibling:
            if source != sibling:
                katakana = getField("Katakana", note)
                print(f"nid {nid}, katakana {katakana}, source {source}, sibling {sibling}")

"""
nid 1296499600849, katakana サ, source チ, sibling サ
nid 1296499677355, katakana ニ, source ミ, sibling ニ
nid 1296499913861, katakana ガ, source カ, sibling ガ
nid 1296499920030, katakana ギ, source キ, sibling ギ
nid 1296499928430, katakana グ, source ク, sibling グ
nid 1296499933243, katakana ゲ, source ケ, sibling ゲ
nid 1296499939214, katakana ゴ, source コ, sibling ゴ
nid 1296499957667, katakana ザ, source チ, sibling ザ
nid 1296499965528, katakana ジ, source シ, sibling ジ
nid 1296499973122, katakana ズ, source ス, sibling ズ
nid 1296499992092, katakana ゼ, source セ, sibling ゼ
nid 1296499999858, katakana ゾ, source ソ, sibling ゾ
nid 1296500033334, katakana ダ, source タ, sibling ダ
nid 1296500042315, katakana ヂ, source チ, sibling ヂ
nid 1296500050753, katakana ヅ, source ツ, sibling ヅ
nid 1296500057732, katakana デ, source テ, sibling デ
nid 1296500064788, katakana ド, source ト, sibling ド
nid 1296500081195, katakana ビ, source ヒ, sibling ビ
nid 1296500089417, katakana ブ, source フ, sibling ブ
nid 1296500095343, katakana ベ, source ヘ, sibling ベ
nid 1296500100431, katakana ボ, source ホ, sibling ボ
nid 1296500113619, katakana ピ, source ヒ, sibling ピ
nid 1296500119840, katakana プ, source フ, sibling プ
nid 1296500126571, katakana ペ, source ヘ, sibling ペ
nid 1296500146577, katakana ポ, source ホ, sibling ポ
nid 1296500160982, katakana キャ, source キ, sibling キャ
nid 1296500167403, katakana キュ, source キ, sibling キュ
nid 1296500172543, katakana キョ, source キ, sibling キョ
nid 1296500178327, katakana ギャ, source キ, sibling ギャ
nid 1296500184696, katakana ギュ, source キ, sibling ギュ
nid 1296500197303, katakana ギョ, source キ, sibling ギョ
nid 1296500205671, katakana シャ, source シ, sibling シャ
nid 1296500244673, katakana シュ, source シ, sibling シュ
nid 1296500254517, katakana ショ, source シ, sibling ショ
nid 1296500261361, katakana ジャ, source シ, sibling ジャ
nid 1296500270086, katakana ジュ, source シ, sibling ジュ
nid 1296500275740, katakana ジョ, source シ, sibling ジョ
nid 1296500284747, katakana チャ, source チ, sibling チャ
nid 1296500289898, katakana チュ, source チ, sibling チュ
nid 1296500295104, katakana チョ, source チ, sibling チョ
nid 1296500302862, katakana ニャ, source ニ, sibling ニャ
nid 1296500308388, katakana ニュ, source ニ, sibling ニュ
nid 1296500314342, katakana ニョ, source ニ, sibling ニョ
nid 1296500322401, katakana ヒャ, source ヒ, sibling ヒャ
nid 1296500330622, katakana ヒュ, source ヒ, sibling ヒュ
nid 1296500337043, katakana ヒョ, source ヒ, sibling ヒョ
nid 1296500349466, katakana ビャ, source ヒ, sibling ビャ
nid 1296500359621, katakana ビュ, source ヒ, sibling ビュ
nid 1296500367567, katakana ビョ, source ヒ, sibling ビョ
nid 1296500374131, katakana ピャ, source ヒ, sibling ピャ
nid 1296500380355, katakana ピュ, source ヒ, sibling ピュ
nid 1296500387455, katakana ピョ, source ヒ, sibling ピョ
nid 1296500396567, katakana ミャ, source ミ, sibling ミャ
nid 1296500403449, katakana ミュ, source ミ, sibling ミュ
nid 1296500409403, katakana ミョ, source ミ, sibling ミョ
nid 1296500415421, katakana リャ, source リ, sibling リャ
nid 1296500424476, katakana リュ, source リ, sibling リュ
nid 1296500442164, katakana リョ, source リ, sibling リョ

"""
