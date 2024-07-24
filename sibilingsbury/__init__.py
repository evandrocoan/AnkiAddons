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

import functools
import random
import time
from datetime import datetime, timedelta
from heapq import *
from typing import Any, Callable, cast

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

from datetime import datetime, timedelta
from itertools import zip_longest
from anki.utils import strip_html

from anki.decks import DeckConfigDict, DeckDict, DeckId
from typing import Any, Callable, cast

from anki.utils import stripHTML
from anki.consts import QUEUE_TYPE_REV
from anki.consts import QUEUE_TYPE_NEW

from aqt import gui_hooks
from aqt.webview import AnkiWebView
from aqt.webview import WebContent
from aqt.webview import AnkiWebViewKind

from aqt.qt import (
    qtmajor,
    qtminor,
)

from anki.cards import Card


def debug(*args, **kwargs):
    # print(*args, **kwargs)
    pass

from anki.scheduler.v1 import Scheduler as SchedulerV1
from anki.scheduler.v2 import Scheduler as SchedulerV2
from anki.scheduler.v3 import Scheduler as SchedulerV3


def getCardV2(self):
    """Pop the next card from the queue. None if finished."""
    self._checkDay()
    if not self._haveQueues:
        self.reset()
    while True:
        card = self._getCard()
        if not card:
            break
        # https://anki.tenderapp.com/discussions/beta-testing/1850-cards-marked-as-buried-are-being-scheduled
        if card.queue > -1:
            timespacing = 7
            self.rebuildSourcesCache(timespacing)

            if self.skipEmptyCards:
                if (
                    self.col.tr.card_template_rendering_empty_front()
                    in card.question()
                ):
                    self.bury_cards([card.id], manual=False)
                    # print(f"{datetime.now()}     Skipping card {card.id}/{card.nid} with empty front.")
                    if card.queue == QUEUE_TYPE_NEW:
                        if self._newDids:
                            self._newDids.pop(0)  # avoid burring the whole deck
                        self._reset_counts()
                    continue

            note = self.noteNotes.get(card.nid)
            source_field = self.getSource(note)
            sibling_field = self.getSibling(note)
            # print(f"{datetime.now()} getting source card {card.id}, {source_field}/{sibling_field}...")

            # Only enable siblings burring if there is a source field set
            if self._burySiblingsOnAnswer and sibling_field:
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
                            # print(f"{datetime.now()}     Skipping card {card.id}/{card.nid} "
                            #         f"for the sibling {cid}, {cid_index:2} < {card_index:2}, "
                            #         f"{card.template()['name']}, {source_field}/{sibling_field}.")
                            review_next_card = True
                            break

                    # this happens when the templates sorting is changed, then, review by the new sorting first!
                    # if a card.queue is QUEUE_TYPE_NEW, it will never be inside self.cardDueReviewToday or self.cardDueReviewInNextDays!
                    if (
                        card.queue == QUEUE_TYPE_NEW
                        and card_index < cid_index
                        and cid in self.cardDueReviewToday
                    ):
                        # print(f"{datetime.now()}     Pushing new card first even if it has a sibling being studied these days.")
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

                        # print(f"{datetime.now()} Analyzing {actual_period:2}/{int(actual_period > timespacing):2}, "
                        #         f"card {card.id}/{card.nid} for sibling {cid} in {timespacing} days: "
                        #         f"{card.template()['name']}, {source_field}/{sibling_field}.")

                        # this would fail if a card is scheduled today to be due in 13 days because
                        # after 7 days this is going to skip any siblings of this card,
                        # but it will not skip this card siblings from tomorrow up to 6 days.
                        if actual_period > timespacing:
                            continue

                        review_next_card = True
                        # print(f"{datetime.now()}     Skipping card because it does has a sibling being studied in these days.")
                        break

                if review_next_card:
                    # set all siblings to the same day so they card template ordering is preserved
                    next_available_start_date = min(max(timespacing - actual_period, 1) + 1, 8)
                    self.set_due_date([card.id], f"{next_available_start_date}")
                    self.bury_cards([card.id], manual=False)
                    if card.queue == QUEUE_TYPE_NEW:
                        self._reset_counts()
                        self._resetNew()
                    continue

            if self._burySiblingsOnAnswer and source_field:
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
                                # print(f"{datetime.now()} Skipping new card {card.id}/{card.nid} "
                                #         f"by source for the sibling pending review "
                                #         f"{cid}, {card.template()['name']}, {source_field}/{sibling_field}.")
                                self.set_due_date([card.id], "1-7")
                                self.bury_cards([card.id], manual=False)
                                self._reset_counts()
                                self._resetNew()
                                review_next_card = True
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
                    # print(f"{datetime.now()} Burying siblings from card {card.id}/{card.nid} by source "
                    #     f"{queue_type:2}, {source_field}/{sibling_field}, {burySet}.")
                    self.set_due_date(burySet, "1-7")
                    self.bury_cards(burySet, manual=False)

                if has_new_card_buried:
                    self._reset_counts()
                    self._resetNew()
            break
    if card:
        if not self._burySiblingsOnAnswer:
            self._burySiblings(card)
        card.start_timer()
        return card
    return None


@staticmethod
def tryGetV2(field, note):
    if field in note:
        return note[field]
    return None

@classmethod
def getSourceV2(cls, note):
    if note is None:
        return None

    source = cls.tryGet("Source", note) or cls.tryGet("source", note)
    return strip_html(source) if source else None

@classmethod
def getSiblingV2(cls, note):
    if note is None:
        return None

    source = cls.tryGet("Sibling", note) or cls.tryGet("sibling", note)
    return strip_html(source) if source else None

@staticmethod
def combineListAlternatingV2(*iterators):
    # https://stackoverflow.com/questions/3678869/pythonic-way-to-combine-two-lists-in-an-alternating-fashion
    # merge("abc", "lmn1234", "xyz9", [None])
    # ['a', 'l', 'x', None, 'b', 'm', 'y', 'c', 'n', 'z', '1', '9', '2', '3', '4']
    return [
        element
        for inner_list in zip_longest(*iterators, fillvalue=object)
        for element in inner_list
        if element is not object
    ]

def rebuildSourcesCacheV2(self, timespacing):
    # rebuilds the cache if Anki stayed open over night
    if not hasattr(self, "cardSourceIds") or self.cardSourceIdsTime < self.today:
        self.cardSourceIdsTime = self.today
        self.cardSourceIds = {}
        self.cardSiblingIds = {}
        self.cardQueuesType = {}

        self.noteNotes = {}

        self.cardDueReviewToday = set()
        self.cardDueReviewInNextDays = {}
        self.cardDueReviewsInLastDays = {}

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

        timenow = datetime.now()
        timedaysago = timenow - timedelta(days=timespacing)
        timenowid = int(timenow.timestamp() * 1000)
        timedaysagoid = int(timedaysago.timestamp() * 1000)
        creation_timestamp = datetime.fromtimestamp(
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
            review_date = datetime.fromtimestamp(seconds / 1000)
            delta = review_date - creation_timestamp
            self.cardDueReviewsInLastDays[cid] = delta.days

        for cid, due in self.col.db.execute(
            f"select id, due from cards where "
            f"queue in ({QUEUE_TYPE_LRN},{QUEUE_TYPE_REV},{QUEUE_TYPE_DAY_LEARN_RELEARN},{QUEUE_TYPE_PREVIEW}) "
            f"and due <= {self.today + timespacing} and due >= {self.today}"
        ):
            self.cardDueReviewInNextDays[cid] = due

@functools.lru_cache(maxsize=1)
def cached_deck_due_treeV2(self, deck_id: DeckId, cache_life: int = 0):
    del cache_life  # shut pylint up
    return self.deck_due_tree(deck_id)

@staticmethod
def get_ttl_hashV2(seconds: float):
    """Return the same value withing `seconds` time period
    https://stackoverflow.com/questions/31771286/python-in-memory-cache-with-time-to-live"""
    if not seconds:
        return None
    return round(time.time() / seconds)

def _reset_countsV2(self) -> None:
    node = self.cached_deck_due_tree(
        self._current_deck_id, cache_life=self.get_ttl_hash(30)
    )
    if not node:
        # current deck points to a missing deck
        self.newCount = 0
        self.revCount = 0
        self._immediate_learn_count = 0
    else:
        self.newCount = node.new_count
        self.revCount = node.review_count
        self._immediate_learn_count = node.learn_count

def _fillNewV2(self, recursing: bool = False) -> bool:
    if self._newQueue:
        return True
    if not self.newCount:
        return False
    while self._newDids:
        did = self._newDids[0]
        lim = min(
            self.queueLimit,
            self._deckNewLimit(did, cache_life=self.get_ttl_hash(30)),
        )
        if lim:
            # fill the queue with the current did
            self._newQueue = self.col.db.list(
                f"""
            select id from cards where did = ? and queue = {QUEUE_TYPE_NEW} order by due,ord limit ?""",
                did,
                lim,
            )
            if self._newQueue:
                self._newQueue.reverse()
                return True
        # nothing left in the deck; move to next
        self._newDids.pop(0)
    else:
        return False

@functools.lru_cache(maxsize=1024)
def _deckNewLimitV2(
    self,
    did: DeckId,
    fn: Callable[[DeckDict], int] = None,
    cache_life: int = 0,
) -> int:
    del cache_life  # shut pylint up
    if not fn:
        fn = self._deckNewLimitSingle
    sel = self.col.decks.get(did)
    lim = -1
    # for the deck and each of its parents
    for g in [sel] + self.col.decks.parents(did):
        rem = fn(g)
        if lim == -1:
            lim = rem
        else:
            lim = min(rem, lim)
    return lim

def _daysLateV2(self, card: Card) -> int:
    "Number of days later than scheduled."
    due = card.odue if card.odid else card.due
    delay = max(0, self.today - due)
    lastIvl = (
        card.lastIvl
        if hasattr(card, "lastIvl")
        else (card.ivl if hasattr(card, "ivl") else 5)
    )
    lastIvl = lastIvl if lastIvl > 0 else 3
    # print(f'{card.id} Default delay {delay}, Fixed delay {lastIvl}, Using new {lastIvl < delay}.')
    if lastIvl < delay:
        delay = lastIvl
    return delay


SchedulerV2.getCard = getCardV2
SchedulerV2.tryGet = tryGetV2
SchedulerV2.getSource = getSourceV2
SchedulerV2.getSibling = getSiblingV2
SchedulerV2.combineListAlternating = combineListAlternatingV2
SchedulerV2.rebuildSourcesCache = rebuildSourcesCacheV2
SchedulerV2.skipEmptyCards = False
SchedulerV2.cached_deck_due_tree = cached_deck_due_treeV2
SchedulerV2.get_ttl_hash = get_ttl_hashV2
SchedulerV2._reset_counts = _reset_countsV2
SchedulerV2._fillNew = _fillNewV2
SchedulerV2._deckNewLimit = _deckNewLimitV2
SchedulerV2._daysLate = _daysLateV2


