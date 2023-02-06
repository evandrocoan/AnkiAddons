# -*- coding: utf-8 -*-

"""
Copyright 2023 @ Evandro Coan
Anki Addon to bury related siblings sources

Redistributions of source code must retain the above
copyright notice, this list of conditions and the
following disclaimer.

Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials
provided with the distribution.

Neither the name Evandro Coan nor the names of any
contributors may be used to endorse or promote products
derived from this software without specific prior written
permission.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or ( at
your option ) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import aqt

from typing import Any

from aqt import gui_hooks
from aqt.webview import AnkiWebView
from aqt.webview import WebContent
from aqt.webview import WebviewDidInitContext

from aqt.qt import (
    qtmajor,
    qtminor,
)

from aqt import mw
mw.addonManager.setWebExports(__name__, r"web/ankimedia.js")

from anki.cards import Card
g_previewer = None
g_reviewer = None
g_clayout = None


def enable_javascript_playback(web: AnkiWebView) -> None:
    page_settings = web._page.settings()

    if qtmajor > 5 and qtminor > 1:
        page_settings.setAttribute(
            aqt.PyQt6.QtWebEngineCore.QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
            False,
        )
    elif qtmajor == 5 and qtminor >= 11:
        page_settings.setAttribute(
            aqt.QWebEngineSettings.PlaybackRequiresUserGesture, False  # type: ignore
        )


def webview_will_set_content(web_content: WebContent, context: Any):
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.insert(0, f"/_addons/{addon_package}/web/ankimedia.js")


def webview_did_init(web_content: WebContent, location: WebviewDidInitContext):
    print(f'webview_did_init {location}, web {web_content}.')

    if location in (WebviewDidInitContext.CLAYOUT, WebviewDidInitContext.PREVIWER, WebviewDidInitContext.MAIN_WINDOW):
        enable_javascript_playback(web_content)
    else:
        print(f'ankimediaqueue, invalid location {location}, web {web_content}.')


def card_will_show(text: str, card: Card, kind: str):
    print(f'card_will_show autoplay {card.autoplay()}, kind {kind}.')
    global g_previewer
    global g_reviewer
    global g_clayout

    if kind.startswith('preview'):
        if not g_previewer:
            print(f'card_will_show error: global g_previewer not defined {g_previewer}.')
            return text
        web_content: WebContent = g_previewer._web
        skip_front: bool = not g_previewer._show_both_sides and g_previewer._state == "answer"
        has_autoplayed: bool = False

    elif kind == 'reviewQuestion':
        if not g_reviewer:
            print(f'card_will_show error: global g_reviewer not defined {g_reviewer}.')
            return text
        web_content: WebContent = g_reviewer.web
        skip_front: bool = False
        has_autoplayed: bool = False

    elif kind == 'reviewAnswer':
        if not g_reviewer:
            print(f'card_will_show error: global g_reviewer not defined {g_reviewer}.')
            return text
        web_content: WebContent = g_reviewer.web
        skip_front: bool = True
        has_autoplayed: bool = False

    elif kind == 'clayoutQuestion':
        if not g_clayout:
            print(f'card_will_show error: global g_clayout not defined {g_clayout}.')
            return text
        web_content: WebContent = g_clayout.preview_web
        skip_front: bool = False
        has_autoplayed: bool = g_clayout.have_autoplayed

    elif kind == 'clayoutAnswer':
        if not g_clayout:
            print(f'card_will_show error: global g_clayout not defined {g_clayout}.')
            return text
        web_content: WebContent = g_clayout.preview_web
        skip_front: bool = True
        has_autoplayed: bool = g_clayout.have_autoplayed

    else:
        print(f'card_will_show unknown type kind {kind}.')

    enable_javascript_playback(web_content)

    if skip_front:
        web_content.eval("ankimedia.skip_front = true;")

    if not has_autoplayed:
        web_content.eval(f"ankimedia._reset({{skip_front_reset: {'true' if skip_front else 'false'}}});")

    if not card.autoplay():
        web_content.eval("ankimedia.autoplay = false;")

    return text


def previewer_did_init(previewer: aqt.browser.previewer.Previewer):
    print(f'previewer_did_init web {previewer}.')
    global g_previewer
    g_previewer = previewer


def reviewer_did_init(reviewer: aqt.reviewer.Reviewer):
    print(f'reviewer_did_init web {reviewer}.')
    global g_reviewer
    g_reviewer = reviewer


def card_layout_will_show(clayout: aqt.clayout.CardLayout):
    print(f'card_layout_will_show web {clayout}.')
    global g_clayout
    g_clayout = clayout


def audio_will_toggle(web_content: WebContent):
    print(f'audio_will_toggle web {web_content}.')
    web_content.eval("ankimedia.togglePause();")


def audio_will_replay(web_content: WebContent, card: Card, state: str):
    print(f'audio_will_replay state {state}, replay_question_audio_on_answer_side {card.replay_question_audio_on_answer_side()}, web {web_content}.')
    enable_javascript_playback(web_content)

    if state == "answer" and not card.replay_question_audio_on_answer_side():
        web_content.eval("ankimedia.skip_front = true;")

    web_content.eval("ankimedia.replay();")


def show_both_sides_will_toggle(web_content: WebContent,  card: Card, state: str, toggle: bool):
    print(f'show_both_sides_will_toggle state {state}, toggle {toggle}, web {web_content}.')
    web_content.eval("ankimedia._reset();")

    if state == "question" and toggle:
        web_content.eval("ankimedia.skip_front = true;")


gui_hooks.webview_did_init.append(webview_did_init)
gui_hooks.card_will_show.append(card_will_show)
gui_hooks.audio_will_toggle.append(audio_will_toggle)
gui_hooks.previewer_did_init.append(previewer_did_init)
gui_hooks.reviewer_did_init.append(reviewer_did_init)
gui_hooks.card_layout_will_show.append(card_layout_will_show)
gui_hooks.audio_will_replay.append(audio_will_replay)
gui_hooks.show_both_sides_will_toggle.append(show_both_sides_will_toggle)
gui_hooks.webview_will_set_content.append(webview_will_set_content)
