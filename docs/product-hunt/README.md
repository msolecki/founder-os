# Founder OS — Product Hunt launch kit

Everything in this directory is ready to paste or upload, but nothing here
publishes itself. The founder submits the listing, uploads the assets, records
the real activation run, and posts the maker comment.

## Submission order

1. Copy the fields from [`listing.md`](listing.md).
2. Upload the thumbnail and four gallery images in the order below.
3. Record the uncut flow from [`demo-script.md`](demo-script.md).
4. Paste [`maker-comment.md`](maker-comment.md) as the first comment.
5. Use [`activation-study.md`](activation-study.md) only for consented test
   participants. Never paste workspace contents into it.

## Asset inventory

| Asset | Dimensions | Reviewable source | Description |
|---|---:|---|---|
| `thumbnail-240.png` | 240×240 | [`sources/thumbnail-240.svg`](sources/thumbnail-240.svg) | Alt text: Founder OS F/OS mark in cream, lime and orange on a dark square. |
| `gallery-01-outcome.png` | 1270×760 | [`sources/gallery-01-outcome.svg`](sources/gallery-01-outcome.svg) | Alt text: Founder OS daily brief naming one priority and one explicit trade. |
| `gallery-02-onboarding.png` | 1270×760 | [`sources/gallery-02-onboarding.svg`](sources/gallery-02-onboarding.svg) | Alt text: Four onboarding groups leading from an empty folder to a valid first brief. |
| `gallery-03-trust.png` | 1270×760 | [`sources/gallery-03-trust.svg`](sources/gallery-03-trust.svg) | Alt text: Four Founder OS trust boundaries: local Markdown, ownership, provenance, and no sending or payments. |
| `gallery-04-operating-loop.png` | 1270×760 | [`sources/gallery-04-operating-loop.svg`](sources/gallery-04-operating-loop.svg) | Alt text: Founder OS loop from daily brief through committed work and Friday review to the next brief, with inbox notes feeding forward. |

The SVG files are the reviewed visual sources. The PNG files are deterministic
renders of those sources, not generated screenshots of a fictional successful
installation.

## Submission checklist

- [ ] Product name is exactly `Founder OS`.
- [ ] Tagline is 60 characters or fewer.
- [ ] Description is 260 characters or fewer.
- [ ] No shortened or tracked primary URL.
- [ ] At most three precise topics are selected.
- [ ] Thumbnail is exactly 240×240.
- [ ] Gallery images are exactly 1270×760 and uploaded in numbered order.
- [ ] Every uploaded image has the matching alt text above.
- [ ] Demo shows the public install commands and one real, uncut activation.
- [ ] Any failure remains visible; no mocked completion is presented as real.
- [ ] Maker comment asks for activation feedback, not ranking manipulation.
- [ ] Participant notes contain consented IDs and operational fields only.

## Rebuild and verify

On macOS, render each reviewed SVG source to its matching PNG, then run the
contract:

```bash
SWIFT_MODULECACHE_PATH=/tmp/founder-os-swift-cache \
CLANG_MODULE_CACHE_PATH=/tmp/founder-os-clang-cache \
swift docs/product-hunt/render-assets.swift
python3 -m unittest tests.test_docs_workflows.ProductHuntLaunchKitContractTest
```

The contract reads PNG headers directly with the Python standard library. It
also checks required files, dimensions, copy limits, source paths and alt text.
