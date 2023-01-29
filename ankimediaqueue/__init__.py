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

from aqt import gui_hooks, CallingFunction
from aqt.webview import AnkiWebView
from aqt.webview import WebContent

from aqt.qt import (
    qtmajor,
    qtminor,
)

from aqt import mw
mw.addonManager.setWebExports(__name__, r"web/ankimedia.js")

from anki.cards import Card


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


def on_ankimediaqueue(web_content: AnkiWebView, location: str):
    print(f'location old {location}, web {web_content}.')

    if location in ('autoplay-preview', 'autoplay-show', 'autoplay-render'):
        web_content.eval("ankimedia.autoplay = false;")

    elif location in ('toggle-pause',):
        web_content.eval("ankimedia.togglePause();")

    elif location in ('reset-preview', 'reset-redraw', 'reset-next', 'reset-sides'):
        web_content.eval("ankimedia._reset();")

    elif location in ('reset_skip-render',):
        web_content.eval("ankimedia._reset({skip_front_reset: true});")

    elif location in ('skip-preview', 'skip-replay', 'skip-render_answer', 'skip-render_end', 'skip-sides'):
        web_content.eval("ankimedia.skip_front = true;")

    elif location in ('replay-replay', 'replay-audio'):
        web_content.eval("ankimedia.replay();")

    else:
        print(f'ankimediaqueue, invalid location {location}, web {web_content}.')


def on_webview_will_set_content(web_content: WebContent, context: Any):
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.insert(0, f"/_addons/{addon_package}/web/ankimedia.js")


def on_webview_did_init(web_content: WebContent, location: CallingFunction):
    # print(f'on_webview_did_init {location}, web {web_content}.')

    if location in (CallingFunction.CLAYOUT, CallingFunction.PREVIWER, CallingFunction.MAIN_WINDOW):
        enable_javascript_playback(web_content)
    else:
        print(f'ankimediaqueue, invalid location {location}, web {web_content}.')


def on_card_will_show_state(text: str, card: Card, kind: str, web_content: WebContent, skip_front: bool, has_autoplayed: bool):
    print(f'on_card_will_show_state skip_front {skip_front}, autoplay {card.autoplay()}, has_autoplayed {has_autoplayed}, web {web_content}.')

    if skip_front:
        web_content.eval("ankimedia.skip_front = true;")

    if not has_autoplayed:
        web_content.eval(f"ankimedia._reset({{skip_front_reset: {'true' if skip_front else 'false'}}});")

    if not card.autoplay():
        web_content.eval("ankimedia.autoplay = false;")

    return text


def on_audio_will_toggle(web_content: WebContent):
    print(f'on_audio_will_toggle web {web_content}.')
    web_content.eval("ankimedia.togglePause();")


gui_hooks.will_show_web.append(on_ankimediaqueue)
gui_hooks.webview_did_init.append(on_webview_did_init)
gui_hooks.card_will_show_state.append(on_card_will_show_state)
gui_hooks.audio_will_toggle.append(on_audio_will_toggle)
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
