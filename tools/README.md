# Site editor

`site-editor.html` edits the text on the website (`docs/`) without touching code. It is a single file with no install, and it isn't published (only `docs/` goes on GitHub Pages).

## Edit

1. Double-click `tools/site-editor.html` to open it in Chrome or Edge.
2. Click **Open docs folder**, choose the repo's `docs` folder and allow editing.
3. Change any text. The preview on the right updates as you type:
   - **Site text**: tagline, feedback and discussion lines, how to install, disclaimer, license, footer, section titles, track captions.
   - **One section per machine**: name, version, description, demo label, the 8 parameter lines, the Note box (one note per paragraph), track counts and the download row texts.
   - HTML is allowed in the text (`<a href="...">`, `<b>`, `<code>`).
4. Click **Review & save**. It lists every change; **Save** writes `docs/site-text.js` and `docs/machines.js` and bumps the `?v=` version tags in `docs/index.html`, so browsers load the new text straight away.

Firefox or Safari: use **…or pick docs folder** and choose the repo's `docs` folder (the browser may say it will "upload" the files; nothing leaves your computer). Or use **…or pick files** and choose `site-text.js`, `machines.js` and `index.html` from `docs`, all together or one at a time; the editor says which ones it still needs. Saving downloads the changed files; copy them into `docs/`, replacing the old ones.

## Publish

From the repo folder:

```
git add docs
git commit -m "Update site text"
git pull --rebase origin main
git push origin main
```

The site updates about a minute after the push.
