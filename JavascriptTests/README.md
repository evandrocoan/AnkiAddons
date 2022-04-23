# Anki Media Queue

Use `> npm test -- reviewer-exceptions.test.ts` to run a single test file

1. `npm run build`
1. `npm run test`
   1. `chcp 936`
   1. https://stackoverflow.com/questions/39551549/q-how-do-you-display-chinese-characters-in-command-prompt/52355476
1. `npm install --no-optional`

Use this inside a test to pause its execution, allowing you to open the chrome console
and while keeping the express server running: chrome://inspect/#devices
```js
jest.setTimeout(2000000000);

(async () => await page.setDefaultTimeout(2000000000))();
(async () => await page.setDefaultNavigationTimeout(2000000000))();
debugger; await new Promise(function(resolve) {});
```

### License

```
/* Copyright: Evandro Coan
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html */
```
