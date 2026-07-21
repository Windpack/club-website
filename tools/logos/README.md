# Company logos for the sponsorship packet

Drop logo files here to replace the text placeholders on the "Where our members go"
page of `assets/pdfs/sponsors.pdf`, then re-run:

```
python tools/make_sponsors_pdf.py
```

## Naming

The filename must match the slug in the `COMPANIES` list in
`tools/make_sponsors_pdf.py`:

| Company       | Expected file           |
| ------------- | ----------------------- |
| GE Vernova    | `ge-vernova.png`        |
| SAS Institute | `sas-institute.png`     |

If a file is missing, the script draws the company name as clean type instead,
so the packet always builds.

## Adding another company

Add a line to `COMPANIES` in `tools/make_sponsors_pdf.py`:

```python
COMPANIES = [
    ("GE Vernova",    "ge-vernova"),
    ("SAS Institute", "sas-institute"),
    ("New Company",   "new-company"),      # add here
]
```

Then drop `new-company.png` in this folder. `OPEN_SLOTS` just below controls how
many empty "Room to grow" tiles are shown, so lower it by one as the list fills up.

## Image tips

- **PNG with a transparent background** works best, since tiles are white.
- Around 600px on the long edge is plenty; the tiles render about 150pt wide.
- Use each company's official logo file. Most have a press or brand-assets page.
  Check their brand guidelines before publishing, as some ask that you get
  permission before showing their mark alongside your organization.
