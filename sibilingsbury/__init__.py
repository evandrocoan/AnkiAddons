# -*- coding: utf-8 -*-

"""
Copyright 2024 @ Evandro Coan
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

from __future__ import annotations
from anki import hooks

import functools
import time
import datetime
import timeit

datetime_now = datetime.datetime.now

import random
from heapq import *

import anki  # pylint: disable=unused-import
import anki.collection
from anki import hooks, scheduler_pb2
from anki._legacy import deprecated
from anki.cards import Card, CardId
from anki.consts import *
from anki.decks import DeckConfigDict, DeckDict, DeckId
from anki.lang import FormatTimeSpan
from anki.scheduler.legacy import SchedulerBaseWithLegacy
from anki.utils import ids2str, int_time

from itertools import zip_longest
from anki.utils import strip_html

from typing import Any, Callable, cast

from anki.utils import stripHTML
from anki.consts import QUEUE_TYPE_REV
from anki.consts import QUEUE_TYPE_NEW

import aqt
from aqt import gui_hooks
from aqt.webview import AnkiWebView
from aqt.webview import WebContent
from aqt.webview import AnkiWebViewKind

from aqt.utils import (
    show_warning,
)

from aqt.qt import (
    qtmajor,
    qtminor,
    QAction,
    qconnect,
)


def debug(*args, **kwargs):
    # print(*args, **kwargs)
    pass

from anki.scheduler.v3 import Scheduler as SchedulerV3

config = aqt.mw.addonManager.getConfig(__name__)
if config is None:
    print(f"WARNING: Missing configuration file from addon {__name__}.")
    config = {}

__version__ = "1.1.0"
timespacing = config.get("CardsBuryRange", 7)


def get_queued_cards(
    self,
    *,
    fetch_limit: int = 1,
    intraday_learning_only: bool = False,
) -> QueuedCards:
    "Returns zero or more pending cards, and the remaining counts. Idempotent."

    while True:
        try:
            if self.autoBurySourceCards:
                if not hasattr(self, "cardSourceIds") or self.cardSourceIdsTime < self.today:
                    self.buildSourcesCache(timespacing)

                queued_cards, \
                no_new_cards, \
                cards_source_buried, \
                cards_sibling_buried, \
                cards_empty_buried, \
                to_reschedule \
                = self.get_queued_cards_internal(
                    fetch_limit=fetch_limit,
                    intraday_learning_only=intraday_learning_only,
                    card_fetch_index=0,
                    timespacing=timespacing,
                )
            else:
                queued_cards = self.col._backend.get_queued_cards(
                    fetch_limit=fetch_limit,
                    intraday_learning_only=intraday_learning_only,
                )

            queued_card = queued_cards.cards[0]

        except IndexError:
            return queued_cards

        card = Card(self.col)
        card._load_from_backend_card(queued_card.card)

        if self.skipEmptyCards:
            if (
                self.col.tr.card_template_rendering_empty_front()
                in card.question()
            ):
                self.bury_cards([card.id], manual=False)
                debug(f"{datetime_now()}     Skipping card {card.id}/{card.nid} with empty front.")
                continue
        break

    return queued_cards


def bury_all_siblings_queued_cards(self) -> None:
    card_fetch_index=0
    total_cards_source_buried = 0
    total_cards_sibling_buried = 0
    total_cards_empty_buried = 0
    cards_to_reschedule = []
    start_time = timeit.default_timer()

    aqt.mw.taskman.run_on_main(
        lambda: aqt.mw.progress.start(label="Creating source cache...")
    )
    self.buildSourcesCache(timespacing)

    while True:
        queued_cards, \
        no_new_cards, \
        cards_source_buried, \
        cards_sibling_buried, \
        cards_empty_buried, \
        to_reschedule \
        = self.get_queued_cards_internal(
            fetch_limit=card_fetch_index+1,
            intraday_learning_only=False,
            card_fetch_index=card_fetch_index,
            timespacing=timespacing,
        )
        card_fetch_index += 1
        total_cards_source_buried += cards_source_buried
        total_cards_sibling_buried += cards_sibling_buried
        total_cards_empty_buried += cards_empty_buried
        cards_to_reschedule.extend(to_reschedule)

        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label="Burying cards...",
                max=len(self.cardDueReviewToday),
                value=total_cards_source_buried + total_cards_sibling_buried + total_cards_empty_buried + card_fetch_index,
            )
        )

        # print(f"total_cards_source_buried {total_cards_source_buried}, total_cards_sibling_buried {total_cards_sibling_buried}, total_cards_empty_buried {total_cards_empty_buried}, card_fetch_index {card_fetch_index},")
        if no_new_cards:
            break

    # Cannot reschedule just in 7 days because it will mess up with ordering
    # It is required to to some smart calculation to scheduled them in 20 or 100 days
    # accordingly, but still not enough because the current card may still being studied in 20 or 100 days
    # therefore should not be possible to reschedule them never.
    # for card_id, days_range in cards_to_reschedule:
    #     self.set_due_date([card_id], days_range)

    def end():
        end_time = timeit.default_timer()
        elapsed = datetime.timedelta(seconds=end_time-start_time)
        buryAllSiblingsQueuedCards.setText(f"Bury all siblings cards (already run, {'on' if aqt.mw.col.sched.autoBurySourceCards else 'off'})")
        mesage = f"Buried {total_cards_source_buried} source, {total_cards_sibling_buried} sibling, " \
            f"{total_cards_empty_buried} empty, remaining {card_fetch_index - 1} cards " \
            f"after {str(elapsed)[:-7]} seconds."
        print(mesage)
        show_warning(mesage)

    aqt.mw.taskman.run_on_main( lambda: aqt.mw.progress.finish() )
    time.sleep(1)  # avoid progress.finish() closing the show_warning() some times
    aqt.mw.taskman.run_on_main( lambda: end() )


def get_queued_cards_internal(
    self,
    fetch_limit,
    intraday_learning_only,
    card_fetch_index,
    timespacing,
):
    "Returns zero or more pending cards, and the remaining counts. Idempotent."
    cards_source_buried = 0
    cards_empty_buried = 0
    cards_sibling_buried = 0
    to_reschedule = set()
    while True:
        try:
            queued_cards = self.col._backend.get_queued_cards(
                fetch_limit=fetch_limit,
                intraday_learning_only=intraday_learning_only,
            )
            queued_card = queued_cards.cards[card_fetch_index]
        except IndexError:
            print(f"{datetime_now()} No more new cards, fetch_limit={fetch_limit}, "
                f"intraday_learning_only={intraday_learning_only}, "
                f"card_fetch_index={card_fetch_index}, "
                f"timespacing={timespacing}, "
                f"cards_source_buried={cards_source_buried}, "
                f"cards_empty_buried={cards_empty_buried}, "
                f"cards_sibling_buried={cards_sibling_buried}, "
                f"to_reschedule={to_reschedule}."
            )

            return (
                queued_cards,
                True,
                cards_source_buried,
                cards_sibling_buried,
                cards_empty_buried,
                to_reschedule,
            )

        card = Card(self.col)
        card._load_from_backend_card(queued_card.card)

        if self.skipEmptyCards:
            if (
                self.col.tr.card_template_rendering_empty_front()
                in card.question()
            ):
                self.bury_cards([card.id], manual=False)
                cards_empty_buried += 1
                debug(f"{datetime_now()}     Skipping card {card.id}/{card.nid} with empty front.")
                continue

        note = self.noteNotes.get(card.nid)
        source_field = self.getSource(note)
        sibling_field = self.getSibling(note)
        debug(f"{datetime_now()} getting source card {card.id}, {source_field}/{sibling_field}...")

        # Only enable siblings burring if there is a source field set
        if sibling_field:
            review_next_card = False
            siblings = self.cardSiblingIds[sibling_field]
            card_index = siblings.index(card.id)
            actual_period = 0

            # only allow the user to see the next sibling card if timespacing days have passed since the last sibling
            # this allows the user to focus in the current card and only see the next one,
            # if he successfully remembered the current card for timespacing days at least.
            # between concurrent siblings just today, check if there is a sibling with highest priority!
            for cid_index, cid in enumerate(siblings):
                if card.id == cid:
                    continue

                # should I really focus on this cid?
                # review the card.id if it is due today and it has more priority than cid!
                if cid_index < card_index:
                    # check if this is one of the first card reviewed and prioritise it!
                    # break here if it detected that this card is the highest priority, this would allow
                    # this card to be first reviewed and it will be the only one because the siblings source
                    # burying will bury the other siblings.
                    # but do not break if it is detected to not be the one with highest priority scheduled for today!
                    if cid in self.cardDueReviewToday:
                        debug(f"{datetime_now()}     Skipping card {card.id}/{card.nid} "
                                f"for the sibling {cid}, {cid_index:2} < {card_index:2}, "
                                f"{card.template()['name']}, {source_field}/{sibling_field}.")
                        review_next_card = True
                        break

                # this happens when the templates sorting is changed, then, review by the new sorting first!
                # if a card.queue is QUEUE_TYPE_NEW, it will never be inside self.cardDueReviewToday or self.cardDueReviewInNextDays!
                if (
                    card.queue == QUEUE_TYPE_NEW
                    and card_index < cid_index
                    and cid in self.cardDueReviewToday
                ):
                    debug(f"{datetime_now()}     Pushing new card first even if it has a sibling being studied these days.")
                    break

                # blocks the actual card if it is detected a sibling scheduled in 7 days period.
                # notice: if a card is inside self.cardDueReviewInNextDays, it may be inside self.cardDueReviewToday!
                if (
                    cid in self.cardDueReviewsInLastDays
                    and cid in self.cardDueReviewInNextDays
                ):
                    actual_period = abs(
                        self.cardDueReviewInNextDays[cid]
                        - self.cardDueReviewsInLastDays[cid]
                    )

                    debug(f"{datetime_now()} Analyzing {actual_period:2}/{int(actual_period > timespacing):2}, "
                            f"card {card.id}/{card.nid} for sibling {cid} in {timespacing} days: "
                            f"{card.template()['name']}, {source_field}/{sibling_field}.")

                    # this would fail if a card is scheduled today to be due in 13 days because
                    # after 7 days this is going to skip any siblings of this card,
                    # but it will not skip this card siblings from tomorrow up to 6 days.
                    if actual_period > timespacing:
                        continue

                    review_next_card = True
                    debug(f"{datetime_now()}     Skipping card because it does has a sibling being studied in these days.")
                    break

            if review_next_card:
                # set all siblings to the same day so they card template ordering is preserved
                next_available_start_date = min(max(timespacing - actual_period, 1) + 1, 8)
                to_reschedule.add((card.id, f"{next_available_start_date}"))
                self.bury_cards([card.id], manual=False)
                cards_sibling_buried += 1
                continue

        if source_field:
            # bury related sources
            burySet = set()
            has_new_card_buried = False
            sources = self.cardSourceIds[source_field]

            # skip new card if it has a sibling waiting for review,
            # because reviewing already know content is more important
            # than adding more things cluttering knowledge
            if card.queue == QUEUE_TYPE_NEW:
                review_next_card = False
                card_index = sources.index((card.id, QUEUE_TYPE_NEW))

                for cid_index, (cid, _) in enumerate(sources):
                    # this happens when the templates sorting is changed, then, review by the new sorting first!
                    if cid_index < card_index:
                        # if a card.queue is QUEUE_TYPE_NEW, it will never be inside self.cardDueReviewToday!
                        if cid in self.cardDueReviewToday:
                            debug(f"{datetime_now()} Skipping new card {card.id}/{card.nid} "
                                    f"by source for the sibling pending review "
                                    f"{cid}, {card.template()['name']}, {source_field}/{sibling_field}.")
                            to_reschedule.add((card.id, "1-7"))
                            self.bury_cards([card.id], manual=False)
                            review_next_card = True
                            cards_source_buried += 1
                            break
                    else:
                        break

                if review_next_card:
                    continue

            for cid, queue_type in sources:
                if cid != card.id:
                    burySet.add(cid)
                    if queue_type == QUEUE_TYPE_NEW:
                        has_new_card_buried = True

            if burySet:
                debug(f"{datetime_now()} Burying siblings from card {card.id}/{card.nid} by source "
                    f"{queue_type:2}, {source_field}/{sibling_field}, {burySet}.")
                to_reschedule.update([(card_id, "1-7") for card_id in burySet])
                self.bury_cards(burySet, manual=False)
                cards_source_buried += 1
        break

    return (
        queued_cards,
        False,
        cards_source_buried,
        cards_sibling_buried,
        cards_empty_buried,
        to_reschedule,
    )


@staticmethod
def tryGet(field, note):
    if field in note:
        return note[field]
    return None


@classmethod
def getSource(cls, note):
    if note is None:
        return None

    source = cls.tryGet("Source", note) or cls.tryGet("source", note)
    return strip_html(source) if source else None


@classmethod
def getSibling(cls, note):
    if note is None:
        return None

    source = cls.tryGet("Sibling", note) or cls.tryGet("sibling", note)
    return strip_html(source) if source else None


@staticmethod
def combineListAlternating(*iterators):
    # https://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
    # merge("abc", "lmn1234", "xyz9", [None])
    # ['a', 'l', 'x', None, 'b', 'm', 'y', 'c', 'n', 'z', '1', '9', '2', '3', '4']
    return [
        element
        for inner_list in zip_longest(*iterators, fillvalue=object)
        for element in inner_list
        if element is not object
    ]


def buildSourcesCache(self, timespacing):
    self.cardSourceIdsTime = self.today
    self.cardSourceIds = {}
    self.cardSiblingIds = {}
    self.cardQueuesType = {}

    self.noteNotes = {}

    self.cardDueReviewToday = set()
    self.cardDueReviewInNextDays = {}
    self.cardDueReviewsInLastDays = {}

    print(f"{datetime_now()} Building source cache...  timespacing={timespacing}.")

    for cid, queue in self.col.db.execute(f"select id, queue from cards"):
        self.cardQueuesType[cid] = queue

    for (nid,) in self.col.db.execute(f"select id from notes order by mid,id"):
        note = self.col.get_note(nid)
        source = self.getSource(note)
        sibling = self.getSibling(note)

        if source or sibling:
            card_ids = note.card_ids()
            self.noteNotes[nid] = note

        if sibling:
            if sibling in self.cardSiblingIds:
                self.cardSiblingIds[sibling].append(card_ids)
            else:
                self.cardSiblingIds[sibling] = [card_ids]

        if source:
            for cid in card_ids:
                queue_type = self.cardQueuesType[cid]
                if source in self.cardSourceIds:
                    self.cardSourceIds[source].append((cid, queue_type))
                else:
                    self.cardSourceIds[source] = [(cid, queue_type)]

    # this would be a problem for note types with 15 or more cards each, then,
    # intermix items from different note types to not put all cards from other notes at the bottom,
    # this way a card of each note type is studied from each step instead of all from a single note.
    for sibling, list_of_lists in self.cardSiblingIds.items():
        self.cardSiblingIds[sibling] = self.combineListAlternating(
            *list_of_lists
        )

    timenow = datetime_now()
    timedaysago = timenow - datetime.timedelta(days=timespacing)
    timenowid = int(timenow.timestamp() * 1000)
    timedaysagoid = int(timedaysago.timestamp() * 1000)
    creation_timestamp = datetime.datetime.fromtimestamp(
        self.col.db.scalar("select crt from col")
    )

    for (cid,) in self.col.db.execute(
        f"select id from cards where "
        f"queue in ({QUEUE_TYPE_LRN},{QUEUE_TYPE_REV},{QUEUE_TYPE_DAY_LEARN_RELEARN},{QUEUE_TYPE_PREVIEW}) "
        f"and due <= {self.today}"
    ):
        self.cardDueReviewToday.add(cid)

    for seconds, cid, in self.col.db.execute(
        f"select id, cid from revlog where "
        f"id > {timedaysagoid} and id < {timenowid}"
    ):
        review_date = datetime.datetime.fromtimestamp(seconds / 1000)
        delta = review_date - creation_timestamp
        self.cardDueReviewsInLastDays[cid] = delta.days

    for cid, due in self.col.db.execute(
        f"select id, due from cards where "
        f"queue in ({QUEUE_TYPE_LRN},{QUEUE_TYPE_REV},{QUEUE_TYPE_DAY_LEARN_RELEARN},{QUEUE_TYPE_PREVIEW}) "
        f"and due <= {self.today + timespacing} and due >= {self.today}"
    ):
        self.cardDueReviewInNextDays[cid] = due

    print(f"{datetime_now()} Built source cache.")


SchedulerV3.get_queued_cards = get_queued_cards
SchedulerV3.get_queued_cards_internal = get_queued_cards_internal
SchedulerV3.bury_all_siblings_queued_cards = bury_all_siblings_queued_cards
SchedulerV3.tryGet = tryGet
SchedulerV3.getSource = getSource
SchedulerV3.getSibling = getSibling
SchedulerV3.combineListAlternating = combineListAlternating
SchedulerV3.buildSourcesCache = buildSourcesCache
SchedulerV3.skipEmptyCards = config.get("AutoSkipEmptyCards", False)
SchedulerV3.autoBurySourceCards = config.get("AutoBurySourceCards", False)


def toggleSkipEmptyCardsMenu() -> None:
    aqt.mw.col.sched.skipEmptyCards = not aqt.mw.col.sched.skipEmptyCards
    toggleSkipEmptyCards.setText(f"Toggle skip empty cards ({'on' if aqt.mw.col.sched.skipEmptyCards else 'off'})")

toggleSkipEmptyCards = QAction(aqt.mw)
aqt.mw.form.menuTools.addAction(toggleSkipEmptyCards)
toggleSkipEmptyCards.setText(f"Toggle skip empty cards ({'on' if SchedulerV3.skipEmptyCards else 'off'})")
qconnect(toggleSkipEmptyCards.triggered, toggleSkipEmptyCardsMenu)


def buryAllSiblingsQueuedCardsMenu() -> None:
    aqt.mw.col.sched.autoBurySourceCards = not aqt.mw.col.sched.autoBurySourceCards
    aqt.mw.taskman.run_in_background(aqt.mw.col.sched.bury_all_siblings_queued_cards)
    aqt.mw.reset()

buryAllSiblingsQueuedCards = QAction(aqt.mw)
aqt.mw.form.menuTools.addAction(buryAllSiblingsQueuedCards)
buryAllSiblingsQueuedCards.setText(f"Bury all siblings cards ({'on' if SchedulerV3.autoBurySourceCards else 'off'})")
qconnect(buryAllSiblingsQueuedCards.triggered, buryAllSiblingsQueuedCardsMenu)
