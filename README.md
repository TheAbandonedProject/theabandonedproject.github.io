# Publication image host (TEMPLATE, not yet created or published)

This folder is the exact content of the small **public** repository that would serve approved, metadata-stripped newsletter images over HTTPS from GitHub Pages. Nothing here has been pushed anywhere. Creating the repo needs Kelly's approval of the architecture in `docs/IMAGE_HOSTING_OPTIONS.md`.

**Everything committed here is public. Never commit originals, coordinates, story names, or private notes.** Originals live only in the private Google Drive folder tree.

- `i/` holds the images, named `<slug>-<10 hex of the file's own SHA-256>.jpg`. The name is a hash of the content, so a file cannot be edited in place; a replacement gets a new name and therefore a new URL.
- `manifest.json` lists each image with its alt text and caption. It is in the repository but is **not** published on the site.
- `verify_images.py` (standard library only) is the gate: it refuses anything with EXIF/GPS/XMP/IPTC/ICC/comment data, any name/hash mismatch, any file over 600 KB, and any file not listed. The deploy workflow runs it before publishing, and the publish script runs it before committing.
- `.github/workflows/deploy.yml` deploys only `i/` and `robots.txt` if the gate passes. `robots.txt` asks search engines not to index the host.

## Publishing one approved derivative (after approval of the architecture)
`python tools/publish_derivative.py --repo-dir <clone of this repo> DERIVATIVE.jpg --alt "..." [--caption "..."] [--push]`
Dry run by default: it verifies, copies, updates the manifest and commits locally; `--push` sends it. The public URL is `https://<owner>.github.io/<repo>/i/<file>`.

## Replacing or removing an image
Replace: publish the new derivative (new name, new URL), update the issue HTML, then remove the old file and its manifest entry in a commit. Remove: delete the file and its manifest entry and push; the next deploy (about a minute) drops it from the site and the CDN cache expires within minutes. Images already referenced by sent emails should stay up: removing them breaks those emails. The file remains in git history (it was already public and metadata-free); a full purge needs a history rewrite and a request to GitHub support.
