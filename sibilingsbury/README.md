# Source Siblings Bury

Addon for scheduler V3 only.
Depending on how many cards are scheduled for today,
and if FSRS scheduler enabled,
it may take several minutes to complete the cards burring.
Anki addons are only for Desktop but not Android or Anki Web,
But you can use desktop to run the bury command with this addon,
and sync the buried cards with other devices or Anki Web and study there.

## How it works

If a card has the field `Source`,
them any card which also has a `Source` field and is scheduled for today,
is buried.

If a card has the field `Sibling`,
them any card which also has a `Sibling` field and is scheduled for today,
is buried if there are any "sibling" card scheduled from today up to 7 days.

Basically,
cards with the same `Source` field are buried until the next day,
while cards with the same `Sibling` field are buried for 7 days.
`Source` bury is useful for cards that you just do not want to see on the same day.
`Sibling` bury is useful for cards that you do not like to see in the same week.

This does not interfere with Anki builtin sibling bury features,
it only works for cards which have a not empty `Source` or `Sibling` fields.
It will consider a card "sibling" from another if both cards have a `Source` or `Sibling` field
with the same contents.

## How to use

No cards are buried automatically.
On the main Anki window,
go to the menu `Tools -> Bury all siblings cards`.
This will bury all siblings cards.
Now you can sync with other devices and the buried cards will be propagated,
then you can study in other devices with does not support Anki Addons.
You can undo this plugin action by clicking on `Unbury` button,
at the Anki deck review (at the bottom of the page,
where there is the `Study Now` button).

It also has the option `Tools -> Toggle skip empty cards`,
to also bury all cards which have a empty front.
It is useful when you leave unfinished cards with empty fronts.
For exemple, given the following front:
```
{{^IsThisReviewed}}
Question...
{{/IsThisReviewed}}
```
This card will be empty less the "flag" field `IsThisReviewed` has no text on it.

## License

Source Siblings Bury is free and open-source software. The add-on code that runs within
Anki is released under the [GNU GPL v3](LICENSE.txt).
