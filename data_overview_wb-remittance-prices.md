# World Bank Remittance Prices Worldwide

Published by the World Bank Group. A quarterly price survey of money-transfer services. This release of the file covers 372 country pairs, from the first quarter of 2011 to the third quarter of 2025.

This document has six sections. Section 1 explains what the data is and what industry it comes from. Section 2 lists examples of people who use data like this. Section 3 lists what is already known and already built, which is the floor your project has to clear. Section 4 is the download procedure. Section 5 is the column-by-column dictionary. Section 6 is the list of traps and of things the data does not contain.

Copy this file into your team's `project` folder, as the Module 3 handout asks. Everyone on the team should read sections 1 to 3 before the workshop. Role 3, Data fit, leans on sections 5 and 6. Role 5, Technical path, follows section 4 and records what came out.

**How much to trust this document.** It was written with AI assistance and then checked, claim by claim, against the sources linked throughout. Where a sentence links to a source, that source is the authority: if the two disagree, the source wins. Where a sentence has no link, it was either read directly from the data files or is a general statement that could not be tied to one source. Treat those as useful but unconfirmed, and check them before you rely on them in a deliverable. Anything that could not be confirmed at all was either removed or is marked "(unverified)". If you find a mistake, tell the professor so it can be fixed for every team.

---

## 1. Description and industry context

A **remittance** is money that a person working in one country sends to family in another country. A construction worker in Los Angeles sends 200 dollars to his mother in Guatemala. A nurse in London sends money to her brother in Lagos. The money almost always moves in small amounts, month after month, for years.

Sending that money is not free. The sender pays in two ways, and this data exists because the second way is easy to miss.

1. **The fee.** A visible charge, quoted up front. Send 200 dollars, pay 4.99 dollars.
2. **The exchange-rate margin.** The provider converts your dollars into the other country's currency at a rate it chooses. The wholesale rate that big banks trade at with each other is called the **interbank rate**, and it is the rate you see if you type "USD to MXN" into a search engine. Providers give you a worse rate than that and keep the difference. If the interbank rate is 18.00 pesos per dollar and the provider gives you 17.46, the provider has quietly taken 3 percent, on top of any fee.

**Remittance Prices Worldwide**, or **RPW**, is the World Bank's answer to that. The [About page](https://remittanceprices.worldbank.org/about-remittance-prices-worldwide) says RPW is managed by the World Bank's Payment Systems Development Group, part of its Finance Competitiveness and Innovation Global Practice, and that FXC Intelligence provides the underlying data. The [methodology page](https://remittanceprices.worldbank.org/methodology) says data are collected two ways: "by researchers posing as customers and contacting firms within each corridor", and "in an automated way from APIs and websites of different RSPs". For every service the survey records the transfer fee, the exchange rate the provider applied, the margin against the interbank rate, the speed, the payment instrument, the access point and how the receiver collects. Every service is priced at two amounts: the local-currency equivalent of 200 US dollars and of 500 US dollars.

**One row is one firm's service, in one country pair, as priced in one quarterly round.** For example, one row in the 2025 Q3 round is MoneyGram's United States to Mexico service that is funded by credit card over the internet, collected in cash, and available in under an hour, at a total cost of 7.02 percent. The same firm shows up several times in the same country pair and quarter, because one firm usually offers several services that differ in how you pay, where you start, how fast it lands and how the money is handed over.

A country pair is called a **corridor**: United States to Mexico is one corridor, Australia to Fiji is another. Read from the workbook, this release covers 372 corridors, built from 49 sending countries and 105 receiving countries, holds 253,960 priced quotes, and names 713 firms in the modern sheet and 637 in the older one. The publisher's own pages quote different corridor counts for the live survey, so use the file's numbers for the file and the publisher's for the survey. The catalog record gives the update schedule as March, June, September and December, and its current version, labeled Q3 2025, was last modified in May 2026, so the published file lags the quarter it describes.

### Who is in this industry

The firms in this file fall into a few kinds, and the file labels each one.

- **Money Transfer Operators**, usually shortened to **MTO**. A company whose whole business is moving money across borders. Western Union, MoneyGram and Ria carry the most quotes in this file; the publisher's [September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) names Wise, Remitly, WorldRemit, InstaReM and Xoom as the digital-only MTOs in its digital-only index. MTOs are 165,547 of the 204,469 modern rows.
- **Banks.** They offer international transfers, and in this file they are the expensive end: the median cost of sending the 200-dollar equivalent through a bank is 8.20 percent, against 4.75 percent through an MTO.
- **Post offices.** The methodology page says the survey covers "the Post Office when available" alongside MTOs and banks, and the report treats post offices as one of its four provider types.
- **Mobile operators.** Phone companies that run a **mobile wallet**, meaning money held as a balance on a phone rather than in a bank account. These are the cheapest services in the file, with a median of 2.69 percent, but there are only 1,037 such rows, and the report cautions that mobile operators are less than 1 percent of its sample.

Two things separate the modern services from the old ones. The first is the **access point**, meaning where the sender starts the transaction: at an agent's counter in a shop, at a bank branch, over the phone, or on the internet. The share of quotes that involve the internet rose from 30.4 percent in the second quarter of 2016 to 67.6 percent in the third quarter of 2025. The second is the **pickup method**, meaning how the receiver gets the money: cash over a counter, a deposit into a bank account, or a mobile wallet.

### Why people fight over these numbers

Remittances are one of the largest sources of foreign money for many poor countries, and every percentage point of cost is money that does not reach a household. In 2015 the United Nations adopted [Sustainable Development Goal target 10.c](https://sdgs.un.org/goals/goal10): "By 2030, reduce to less than 3 per cent the transaction costs of migrant remittances and eliminate remittance corridors with costs higher than 5 per cent." The UN's [indicator metadata for 10.c.1](https://unstats.un.org/sdgs/metadata/files/Metadata-10-0C-01.pdf) names the World Bank as custodian and this database as the source that is "published on a quarterly basis by the World Bank in the Remittance Prices Worldwide (RPW) database". That is why this survey is published and watched. It is also why the numbers get argued about: a country's central bank, a provider's marketing department and an advocacy group can all read the same corridor differently.

The transparency question sits underneath all of it. On 3,361 modern rows the provider would not tell the surveyor what exchange rate it would apply. The file records those rows with a `transparent` flag set to `no`, and stores the exchange-rate margin as a literal zero. That zero does not mean the service was free. It means nobody knows what it cost. The UN's [indicator metadata](https://unstats.un.org/sdgs/metadata/files/Metadata-10-0C-01.pdf) defines a transparent service as one whose cost can be split into transfer fee and foreign exchange margin, and says the headline global average is computed over transparent services only.

One more thing to know before you read a single row. The World Bank does not survey every provider. The [methodology page](https://remittanceprices.worldbank.org/methodology) says firms are "selected to cover the maximum remittance market share possible, aiming at a minimum aggregated market share of 80 percent" in each corridor. So the file is a deliberate sample of the larger players, and a small currency-exchange shop, an informal network or a cryptocurrency route will not appear. A firm's first appearance in the file marks the day the World Bank moved it into the survey, not the day it opened for business: the report explains that new services sit in a "prospects index" first and are moved into the main analysis later.

For a cohort based in Los Angeles, the United States matters more than any other sender here: 29,542 rows, 42 corridors and 89 firms send from the United States. The busiest of those by quote count are the Philippines, India, Mexico, El Salvador and Colombia.

---

## 2. Possible stakeholders and decisions (illustrative examples only)

The bullets below are illustrative examples only. They were generated with AI help to show the shape an audience statement can take with this data. They are not the professor's suggestions, not a list to choose from, and not necessarily good choices: a named organization may not make this decision the way the bullet implies, and a decision that reads well here may not survive contact with the data. Treat each one as a hypothesis to test, in the sense the Module 3 handout uses, and expect your team to find, check and defend its own audience.

- **A pricing manager at [Remitly](https://www.remitly.com/), a money transfer company, must decide whether to cut the advertised fee or improve the exchange rate on the United States to Philippines service next quarter.** The `cc1 lcu fee` and `cc1 fx margin` columns split the price into those two halves for every rival firm in the same corridor and quarter.
- **A payments supervisor at [Bangko Sentral ng Pilipinas](https://www.bsp.gov.ph/), the central bank of the Philippines, which registers and supervises remittance and transfer companies, must decide whether to require licensed providers to publish their exchange rate before a customer commits.** The `transparent` flag and the `Standard Note` column show which firms and corridors did not disclose a rate, and how often.
- **A program officer at the International Fund for Agricultural Development, the United Nations agency that runs the [Financing Facility for Remittances](https://www.ifad.org/en/remittances/financing-facility-for-remittances), must decide which three corridors to put a cost-reduction program into next year.** Averaging `cc1 total cost %` by `corridor` and `period` gives a comparable cost series for all 372 corridors over 37 quarters.
- **A product lead at [Safaricom](https://www.safaricom.co.ke/), which runs the M-PESA mobile wallet in Kenya, must decide whether to open a wallet payout route in a new receiving country.** The `pickup method` and `receiving network coverage` columns show which providers already pay into wallets there and what they charge.
- **An equity analyst at [T. Rowe Price](https://www.troweprice.com/), an asset manager with a large buy-side equity research team, covering the publicly traded Western Union must decide whether to change the rating before the next earnings call.** The `firm` column names a company on every row, so a firm's quoted prices can be tracked across its corridors over 37 quarters.
- **A campaign researcher at [CHIRLA](https://www.chirla.org/), the Coalition for Humane Immigrant Rights, a Los Angeles immigrant rights organization, must decide which corridor to run a "know what you really pay" campaign on.** Filtering `source_code` to USA and comparing `cc1 total cost %` across the `access point` values shows where the gap between a counter and a website is widest.
- **A data journalist at the [Los Angeles Times](https://www.latimes.com/), whose [data and graphics desk](https://github.com/datadesk) publishes its own analysis code, must decide whether "remittance fees are finally falling" is a story that holds up.** The 37 quarters of `period` support a trend, and the notes in section 6 explain why a raw trend can mislead.
- **A partnerships officer at [Self-Help Federal Credit Union](https://www.self-helpfcu.org/), a California credit union with a large immigrant membership, must decide whether to route members to a transfer provider and which one.** Every quote carries a named `firm`, a `speed actual` category and a total cost, for the specific corridors the membership actually uses.

---

## 3. What is already well known and demonstrated

> Your project is judged on how far it goes beyond what is listed here. Reproducing these is a fine way to
> learn the data, but it earns little credit on its own, and a build that hiring managers have seen many
> times is a weak portfolio piece. Read this list as the floor, not as a menu.

### (a) Findings people already know

- The global average cost of sending 200 US dollars stays far above the 3 percent target. The [publisher's September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) puts the Global Average at 6.36 percent in the third quarter of 2025, down from 6.49 percent in the first quarter of 2025, and says it has stayed below 7.00 percent since the first quarter of 2019.
- Banks are the expensive end. The same report says banks "have been firmly above the Global Average, whereas MTOs and mobile operators have remained below", and records banks at 14.99 percent in the third quarter of 2025. The publisher tracks four provider types, not three: banks, money transfer operators, mobile operators and post offices. In this file the median cost of the 200-dollar basket is 8.20 percent through a bank, 4.75 percent through an MTO and 2.69 percent through a mobile operator.
- Sub-Saharan Africa is the most expensive region to send money into. The report records it at 8.46 percent in the third quarter of 2025, and names Middle East, North Africa, Afghanistan and Pakistan, not South Asia, as the lowest-cost receiving region that quarter at 5.11 percent.
- Cost expressed as a percentage is lower for the 500-dollar basket than for the 200-dollar basket, because a fixed fee spreads over more money. In this file the medians are 3.40 percent and 5.04 percent.
- Digital services are cheaper on average than services bought at a counter. The report's key findings give 4.59 percent for digital remittances against 7.30 percent for non-digital in the third quarter of 2025.
- Costs have drifted down slowly and remain far above the target. The report puts the decline at 3.31 percentage points since the first quarter of 2009, when the global average was 9.67 percent.
- A "zero fee" offer is not a free transfer. The cost moves into the exchange rate instead. In this file 15,258 rows charge a fee of exactly zero.
- Some providers refuse to disclose the exchange rate they will apply, and those services are left out of the published global average. The [catalog record](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide) states that "non-transparent services are not considered when calculating the global average total cost".

### (b) Analyses and tools that already exist

- [Remittance Prices Worldwide, Issue 54, September 2025](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf), the publisher's own quarterly report and annex tables. Global and G20 averages, the SmaRT indicator of the cheapest available services, the digital against non-digital headline, cost broken out by how the sender pays and how the receiver collects, and a progress tracker against the 3 percent target. Anything computed at the global or regional average level is already in here. This file comes with your download.
- The publisher's consumer-facing price lookup for a single corridor, one page per country pair, for example [United States to Mexico](https://remittanceprices.worldbank.org/corridor/United-States/Mexico).
- [RemitWatch](https://github.com/viji-saravanan/remittance-watch), an open-source project under the MIT license built on this workbook. Its README states that it turns 204,469 source rows into 408,938 quotes across 37 quarters, splits every total cost into the visible fee and the exchange-rate margin, ranks every provider on a corridor by total cost, and publishes it as free static JSON. The corridor JSON is live and needs no key.
- [Cross-Border Payment Cost Analyser](https://github.com/sarayurkotha/cross-border-payment-cost-analyser), open source under the MIT license, a two-script pipeline on this same workbook: the most expensive corridors, banks against money transfer operators using `firm_type`, a choropleth map of receiving countries shaded by cost, and an Excel workbook of tables and charts as the output.
- [Cross-Border Remittance Cost Corridor Analytics](https://github.com/Amon-Mugo/Cross-Border-Remittance-Cost-Corridor-Analytics), a data-loading pipeline for the modern sheet of the same workbook, with automated quality checks for duplicate rows, exchange-rate margins and the transparency flag. It has no README and no license file, so read the code.
- [Remittance Cost Report 2026](https://github.com/apex-digital-media/remittance-cost-report-2026), a small derived dataset of 95 rows over eight United States corridors comparing cryptocurrency transfer routes against traditional providers, using the third quarter of 2025 from this file as the traditional baseline.
- [remit-lens](https://github.com/gabrielmahia/remit-lens), a Streamlit price comparator for sending money to Kenya across seven providers, combining fees and exchange-rate spread into a "true cost" using daily European Central Bank reference rates. It is licensed CC BY-NC-ND 4.0, which forbids derivative works, so treat it as something to read rather than to build on.
- [PlainRemit](https://plainremit.com/), an ad-supported consumer website whose About page says it is built on two World Bank datasets, Remittance Prices Worldwide and the World Development Indicators. It publishes corridor cost rankings across 377 corridors, the cheapest operator per corridor, and a tracker against the 3 percent target.
- [Global Remittances and Migration Dataset (2000-2023)](https://www.kaggle.com/datasets/darwish1337/global-remittances-and-migration-dataset-2000-2023) on Kaggle, a country-by-year table of remittance and migration indicators that lists Remittance Prices Worldwide among its sources and includes a 52-corridor cost file, with five public notebooks. It is not the firm-level price file.
- [What Explains Remittance Fees? Panel Evidence](https://www.elibrary.imf.org/view/journals/001/2022/063/001.2022.issue-063-en.xml), International Monetary Fund Working Paper 2022/063 by Beck, Janfils and Kpodar, April 2022, which uses this kind of corridor-level fee data to model what predicts variation in remittance fees.

---

## 4. How to obtain the data

The official landing page is [Remittance Prices Worldwide](https://remittanceprices.worldbank.org). The catalog record that actually serves the files is [Remittance Prices Worldwide in the World Bank Data Catalog](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide), catalog number 0037898.

**License.** The catalog records this dataset as Public under a [Creative Commons Attribution 4.0 license](https://datacatalog.worldbank.org/public-licenses?fragment=cc), which means you may copy, adapt and publish it, including commercially, as long as you credit the source. The catalog record gives the citation as "Remittance Prices Worldwide, World Bank Group", and the publisher's [methodology page](https://remittanceprices.worldbank.org/methodology) says the data "are intended to serve as a snapshot of the cost of remittances on specific dates and time", that actual costs may vary, and that they "should not be used as a substitute for actual pricing information that consumers should obtain directly from service providers".

**Update cadence.** The catalog record gives the update frequency as quarterly and the update schedule as March, June, September and December. The version described here is labeled Q3 2025 in that record, which was last modified on 6 May 2026, so expect the published file to lag the quarter it describes by several months.

### Files to download

Sizes below are the `Content-Length` the server returned to a HEAD request on 5 September 2026.

| File name | Direct link | Format | Size | Rows and columns |
|---|---|---|---|---|
| `rpw_dataset_2011_2025_q3.xlsx` | [complete dataset](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095523/rpw_dataset_2011_2025_q3.xlsx) | Excel workbook, 6 sheets | 48.4 MB (50,762,620 bytes) | Sheet `Dataset (from Q2 2016)`: 204,469 x 42. Sheet `Dataset (up to Q1 2016)`: 49,491 x 41. Sheet `Countries`: 215 x 6. Three documentation sheets. |
| `RPW_main_report_and_annex_Q325.pdf` | [quarterly report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) | PDF | 3.1 MB (3,213,221 bytes) | Not a table. Issue 54, September 2025, main report plus annex tables. |

That is the whole dataset. There is nothing else to fetch and nothing is paginated.

Both routes below start the same way. Open Terminal on Mac or PowerShell on Windows and run these three lines, one at a time.

```
cd ~/dso576
git clone https://github.com/USC-DSO-576-PS/dataset_wb-remittance-prices.git
cd dataset_wb-remittance-prices
```

### Route A, browser

Use this if you would rather click than run a script.

First make the folder the files go into. Run this one line from inside `dataset_wb-remittance-prices`.

```
mkdir data
```

Then:

1. Open [Remittance Prices Worldwide](https://remittanceprices.worldbank.org) in your browser.
2. Click **DATA DOWNLOAD** in the navigation bar across the top of the page. That link does not download anything by itself. It opens the [Data download page](https://remittanceprices.worldbank.org/data-download), which carries a link to the catalog record for this dataset. You can also go to the catalog record directly: [Remittance Prices Worldwide in the World Bank Data Catalog](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide).
3. On the catalog page, stay on the **Overview** tab. The record lists five items. Three are tagged **DATABANK** and carry no file behind them: they are browsing views inside another World Bank site, so skip them.
4. Click **Remittance Prices Worldwide (Complete Dataset)**, the item tagged **EXCEL**, which the catalog page lists at 48.41 MB. The workbook downloads.
5. Click **Remittance Prices Worldwide (Quarterly Report)**, the item tagged **PDF**, listed at 3.06 MB. The report downloads.
6. Open your Downloads folder and drag both files into the `data` folder inside `dataset_wb-remittance-prices`.

**How long and how much space.** The two files together are about 51.5 MB. Leave about 200 MB free on disk, because converting the workbook to CSV later, which the next part of this section recommends, produces another 85 MB if you convert both sheets.

**If a click is blocked.** The `remittanceprices.worldbank.org` site sits behind a bot-check service. A normal browser passes it without noticing. A VPN, a locked-down campus network or an automated tool can trip it and get a "403 Forbidden" message or a checking-your-browser page. If that happens, go straight to the [World Bank Data Catalog record](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide), which does not have that check, and download from there. There is one more trap on the [Data download page](https://remittanceprices.worldbank.org/data-download): the paragraph of text on that page contains an inline link reading "download in MS Excel format", and that link points to an older release, `rpw_dataset_2011_2025_q1.xlsx`, which stops at the first quarter of 2025. Do not use it. Use the catalog page instead.

### Route B, script

This repository ships `download_data.py`. It uses nothing but the Python standard library, so there is nothing to install.

**If the script fails, use the browser.** Several World Bank hosts block requests that do not come from a real browser. `remittanceprices.worldbank.org` returns "403 Forbidden" to scripted requests, and the catalog interface the script calls can refuse a request from a campus network or a VPN. If `download_data.py` prints an HTTP error, a 403, a timeout, or "Could not reach the catalog API", that is not something to debug: open Route A above in your browser and download the same two files by hand, `rpw_dataset_2011_2025_q3.xlsx` and `RPW_main_report_and_annex_Q325.pdf`, then drag them into the `data` folder. Route A covers both files, steps 4 and 5, and the result is identical. The script exists to save clicks, not because the browser route is worse.

```
cd ~/dso576
git clone https://github.com/USC-DSO-576-PS/dataset_wb-remittance-prices.git
cd dataset_wb-remittance-prices
uv run python download_data.py
```

**Why the script needs an extra step.** The World Bank does not keep this workbook at a fixed web address. The file name and the folder holding it both change at every quarterly release. What stays fixed is the catalog number, 0037898. So the script first asks the World Bank Data Catalog interface for that record, reads back the list of files the record currently points at, picks the two it wants by name, and only then downloads them. That is why the script keeps working after the next quarterly release, while a hard-coded address would not.

**What it prints.**

```
Asking the World Bank Data Catalog for record 0037898 ...
Found 2 files to fetch.

rpw_dataset_2011_2025_q3.xlsx: server reports 48.4 MB
  saved 48.4 MB in 3.8 seconds
  checksum ok

RPW_main_report_and_annex_Q325.pdf: server reports 3.1 MB
  saved 3.1 MB in 0.7 seconds
  checksum ok

----
Downloaded 2, skipped 0, failed 0, 51.5 MB now in /Users/you/dso576/dataset_wb-remittance-prices/data
```

The seconds in that example are illustrative; how long the run takes depends on your connection. Run it a second time and it prints `already on disk with the right size, skipping` for both files instead of downloading again.

`checksum ok` means the file you received is byte-for-byte the file this repository was written against. If it prints `checksum differs (the publisher may have updated the file)`, that is not an error: it usually means a new quarter has been released, so your file is newer than the one described in section 5 and your row counts will be a little larger.

If instead it prints `download failed`, `server did not answer` or `Could not reach the catalog API`, the host has refused the script. Switch to Route A in the browser, as above.

If you only want to confirm that the addresses still work, without writing anything to disk, run this line instead.

```
uv run python download_data.py --check
```

### Opening the files

The two data sheets live in one Excel workbook, so the first job is to read them into pandas. Reading Excel needs an extra package called `openpyxl` alongside pandas. The command below adds both for that one run without installing anything permanently.

Create a file called `explore_rpw.py` next to `download_data.py`, paste in one of the snippets, and run:

```
uv run --with pandas --with openpyxl python explore_rpw.py
```

**The modern sheet, 2016 Q2 onwards.** Read `usecols="A:AP"`. Without it, pandas returns 47 columns rather than 42. The header row names only 42 columns, but the 6,470 rows of the 2025 Q3 round carry values in five further, unlabeled columns, `AQ` through `AU`: a year, and the sending and receiving country codes with a year appended. Pandas names those `Unnamed: 42` through `Unnamed: 46`. They are not part of the documented schema. Read every column as text with `dtype=str`, then convert the numbers you actually need; the file stores numbers as text and a few of them are not clean.

```
import pandas as pd

modern = pd.read_excel("data/rpw_dataset_2011_2025_q3.xlsx",
                       sheet_name="Dataset (from Q2 2016)",
                       usecols="A:AP",
                       dtype=str)
print(modern.shape)
modern["cost1"] = pd.to_numeric(modern["cc1 total cost %"], errors="coerce")
print(modern["cost1"].median())
print(modern["period"].nunique())
```

Expected output: `(204469, 42)`, then `5.04`, then `37`. This read is slow, so do not be alarmed by the wait.

**The legacy sheet, 2011 Q1 to 2016 Q1.** Same idea, but the sheet has 41 columns, so the range ends at `AO`.

```
import pandas as pd

legacy = pd.read_excel("data/rpw_dataset_2011_2025_q3.xlsx",
                       sheet_name="Dataset (up to Q1 2016)",
                       usecols="A:AO",
                       dtype=str)
print(legacy.shape)
print(legacy["period"].nunique())
```

Expected output: `(49491, 41)` and `17`. This one is quicker, because the sheet is a quarter of the size.

**The country lookup sheet.** It has a title line above the real header, so skip one row.

```
import pandas as pd

countries = pd.read_excel("data/rpw_dataset_2011_2025_q3.xlsx",
                          sheet_name="Countries",
                          skiprows=1,
                          dtype=str)
print(countries.shape)
print(countries.columns.tolist())
```

Expected output: `(215, 6)` and the six column names beginning with `ISO 3166-1 alpha-3 country code`.

**Do the Excel read once, then work from CSV.** Waiting on the Excel reader is painful when you are exploring. Convert each sheet to CSV one time and read the CSV afterwards; the same 204,469 rows come back far faster.

```
import pandas as pd

modern = pd.read_excel("data/rpw_dataset_2011_2025_q3.xlsx",
                       sheet_name="Dataset (from Q2 2016)",
                       usecols="A:AP",
                       dtype=str)
modern.to_csv("data/rpw_modern.csv", index=False, encoding="utf-8")
again = pd.read_csv("data/rpw_modern.csv", dtype=str)
print(again.shape)
```

Expected output: `(204469, 42)`. Write the CSV as UTF-8, as above, because country names include accented characters such as Côte d'Ivoire and Türkiye.

**The report PDF** opens in any PDF reader. Nothing needs unpacking: there are no `.zip` or other archive files in this dataset.

**Start before the download finishes.** The `sample/` folder in this repository already holds 20,000 rows of each data sheet as plain CSV, with every column, so the team can begin reading and filtering immediately.

**Do not commit the downloaded data to your team repository.** The Module 3 handout says so. The `data` folder in this repository is already listed in `.gitignore`, so git will leave it alone here.

---

## 5. Data dictionary

Column descriptions below follow the publisher's documentation: the `Legend` worksheet inside the workbook, which is the publisher's own one-line codebook for every column, and the [Remittance Prices Worldwide methodology page](https://remittanceprices.worldbank.org/methodology), which defines the survey concepts. Where that documentation gives no description, the entry is marked (inferred from the data). Every count, distinct value, median and range in this section was computed directly from the workbook in the 4 September 2026 download.

### Summary

Everything arrives as one Excel workbook, `rpw_dataset_2011_2025_q3.xlsx`, 48.4 MB, with six worksheets. Two hold the data; the other four are the publisher's own documentation and lookup tables.

| Sheet | Rows x columns | Size | What one row is | How it joins |
|---|---|---|---|---|
| `Dataset (from Q2 2016)` | 204,469 x 42 | 67 MB once written as CSV | One firm's service in one corridor in one quarterly round, 37 quarters from 2016 Q2 to 2025 Q3 | Stands alone. `source_code` and `destination_code` join to `Countries`. No key joins it to the legacy sheet. |
| `Dataset (up to Q1 2016)` | 49,491 x 41 | 18 MB once written as CSV | The same idea, 17 rounds from 2011 Q1 to 2016 Q1 | Same country joins. Its `id` numbering has nothing to do with the modern sheet's. |
| `Countries` | 215 x 6 | small | One country, with its World Bank region, income group, lending category and G8/G20 flag, as of 2025 Q3 | Join on `source_code` or `destination_code` |
| `Legend` | 36 x 2 | small | The publisher's one-line definition of each column | Documentation |
| `Methodology` | image only | small | An embedded picture with no readable cell text | Documentation |
| `Terms of Use` | 31 x 2 | small | Mostly a picture, plus four rows of text pointing at the World Bank terms | Documentation |

**Coverage.** 253,960 priced quotes in total. Time: 2011 Q1 to 2025 Q3, semiannual in 2011 and 2012, quarterly from 2013 onwards, with no 2025 Q2 round in the file. Geography: 372 corridors in the modern sheet from 49 sending countries into 105 receiving countries, and 310 corridors from 35 sending countries in the legacy sheet. Corridors are country pairs; there is no city, state or postcode anywhere in the file.

**The columns most projects turn on.** `corridor`, `period`, `firm`, `firm_type`, `access point`, `payment instrument`, `pickup method`, `speed actual`, `cc1 lcu fee`, `cc1 fx margin`, `cc1 total cost %`, `cc2 total cost %` and `transparent`.

**The two data sheets do not stack.** They share 36 column names, but several differences break a naive concatenation. The legacy sheet has `product` and `sending location` where the modern sheet has `payment instrument` and `access point`. The legacy sheet calls its main free-text column `note1` where the modern sheet calls it `Standard Note`, its coverage column `coverage` where the modern sheet calls it `receiving network coverage`, and its payout column `pick-up method` where the modern sheet drops the hyphen. And the income-group vocabulary changed, so the legacy sheet says "High income: OECD" and "High income: nonOECD" where the modern sheet says only "High income". Treat them as two tables you align on purpose, not as one file.

**What one row is, in detail.** In `Dataset (from Q2 2016)`, one row is one remittance service offered by one firm in one corridor as priced in one quarterly round. The same firm appears several times in the same corridor and quarter when it offers services that differ in how the sender pays, where the sender starts, how fast the money arrives or how the receiver collects. The row key is `id`, and it is unique: 204,469 distinct values on 204,469 rows. There is no shorter natural key. Grouping on period, corridor, firm, access point, payment instrument and speed still leaves 18,529 groups with more than one row, because services also differ on pickup method and network coverage. There are 183 groups of rows that are identical on all 41 columns other than `id`, covering 372 rows, so deduplicating on everything but `id` would drop 189 rows. In `Dataset (up to Q1 2016)` the idea is the same, with `product` in place of the payment-instrument and access-point pair, and `id` is very nearly unique: 49,486 distinct values on 49,491 rows, with five ids, 44140 through 44144, each used twice.

**How many rows per quarter, and why that is not a market signal.** Rows per quarter rise from 3,905 in 2016 Q2 to a peak of 7,608 in 2022 Q4, then settle near 6,500. That growth is the survey adding firms and corridors, not the market growing. Do not read a rising row count as a rising volume of money.

### `Dataset (from Q2 2016)`

204,469 rows, 42 columns, in file order. "Filled %" counts a cell as present when it is neither empty nor blank. Every value is stored as text; the numeric columns are decimal strings that parse cleanly except where noted.

| Column | Type | Filled % | Distinct | Example values | Meaning |
|---|---|---|---|---|---|
| `id` | integer as text | 100.00 | 204,469 | 620160001; 620160002 | The `Legend` sheet calls it the "id number applied to each service". Unique here. The leading digits look like they encode the survey round, but the publisher does not document the scheme, so treat it as an opaque key (inferred from the data). |
| `period` | text | 100.00 | 37 | 2016_2Q; 2025_3Q | Survey quarter, written as year, underscore, quarter, then the letter Q. Sorts correctly as text. `2025_2Q` does not exist. |
| `source_code` | text | 100.00 | 49 | USA; AGO | Three-letter ISO 3166-1 code of the sending country. |
| `source_name` | text | 100.00 | 51 | United States; Angola | Name of the sending country. 51 names for 49 codes: the file holds both "Czech Republic" and "Czechia", and both "Turkey" and "Türkiye", for the same codes. Group on the code, not the name. |
| `source_region` | text | 100.00 | 8 | ..; Sub-Saharan Africa | World Bank region of the sending country. `..` means "not applicable", which here mostly means a high-income country outside the Bank's regional groupings: 178,796 rows carry `..`. It is not a missing value. |
| `source_income` | text | 100.00 | 5 | High income; Upper middle income | World Bank income group of the sending country. High income 177,359; Upper middle income 20,484; Lower middle income 5,101; Low income 1,507; Lower income 18. "Lower income" is not one of the four groups on the World Bank's [country and lending groups page](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups), and nothing in the file says which group those 18 rows belong to. Run `.unique()` on this column, look at the rows carrying that value, and decide for yourself what to do with them. |
| `source_lending` | text | 100.00 | 4 | ..; IBRD | World Bank lending category of the sending country: `..` 175,978, IBRD 23,877, Blend 2,792, IDA 1,822. IBRD and IDA are the two lending arms of the World Bank; the category says which one, if either, lends to that country. |
| `source_G8G20` | text | 100.00 | 3 | G8/G20; G20; .. | Whether the sending country belongs to the G8 or G20 groups of large economies. G8/G20 106,770; `..` 71,450; G20 26,249. |
| `destination_code` | text | 100.00 | 105 | MEX; NAM | Three-letter code of the receiving country. |
| `destination_name` | text | 100.00 | 108 | Mexico; Namibia | Name of the receiving country. Again more names than codes; group on the code. |
| `destination_region` | text | 100.00 | 8 | East Asia & Pacific | World Bank region of the receiving country. Two spellings of the Middle East region coexist in this file: "Middle East & North Africa" on 17,831 rows and "Middle East, North Africa, Afghanistan & Pakistan" on 784. The second is the name the World Bank's current [country and lending groups page](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups) uses, so the file is part way through a renaming; the page does not date the change. |
| `destination_income` | text | 100.00 | 5 | Lower middle income | World Bank income group of the receiving country. Lower middle 113,072; Upper middle 59,862; Low 22,470; High 7,593; plus 1,472 rows of "Lower income", the same undocumented value as in `source_income`. |
| `destination_lending` | text | 100.00 | 4 | IBRD; IDA | Lending category of the receiving country: IBRD 125,743, IDA 53,347, Blend 22,243, `..` 3,136. |
| `destination_G8G20` | text | 100.00 | 2 | ..; G20 | G8/G20 membership of the receiving country: `..` 164,393, G20 40,076. No G8 member receives in this file. |
| `firm` | text | 100.00 | 713 | Western Union; Wise; Remitly | Name of the provider. Free text, not a code, and not normalized for capitalization: seven pairs of names differ only by capital letters, and "Transferwise" (1,155 rows) and "Wise" (3,821 rows) are the same company before and after a rename, which one `note2` value states outright. Normalize before counting firms. |
| `firm_type` | text | 100.00 | 11 | Money Transfer Operator; Bank | Category of provider. Money Transfer Operator 165,547; Bank 32,475; Money Transfer Operator / Post office 1,893; Post office 1,698; Bank / Money Transfer Operator 1,383; Mobile Operator 1,037; smaller hybrids below that. Capitalization and spacing around the slash vary, so "Post office" and "Post Office" appear as separate values. |
| `payment instrument` | text | 100.00 | 26 | Cash; Bank account transfer; Debit card | How the sender funds the transaction. New in 2016 Q2, replacing the legacy `product`, according to the workbook's `Legend` sheet. It can hold several values: a comma-separated list when one service accepts more than one, which is why there are 26 distinct strings over a handful of underlying categories. The methodology page lists four categories, cash, bank account transfer, debit credit and/or prepaid card, and mobile money; the file separates debit, credit and prepaid cards. Split on the comma before grouping. |
| `access point` | text | 100.00 | 22 | Internet; Agent; Bank branch | Where the sender starts the transaction. New in 2016 Q2, replacing the legacy `sending location`. Also comma-separated and multi-valued. Internet alone 99,969; Agent alone 69,702; Bank branch alone 13,385. This is the column that separates a digital service from a cash-counter service. |
| `speed actual` | text | 100.00 | 9 | Less than one hour; Next day | Time until the money is available to the receiver, standardized by the publisher into six categories since 2009: less than one hour, same day, next day, 2 days, 3-5 days, 6 days or more. Nine distinct strings appear: the six documented ones plus five stray rows, three of them "less than one hour" in lower case, one "Next Day", and one using an undocumented "1-3 days". |
| `cc1 lcu amount` | number as text | 100.00 | 65 | 200; 33000 | The amount actually sent at the first price point, in the sending country's local currency. Fixed per country since 2009, so it is a constant per currency and is **not** exactly 200 US dollars at today's rate. Range 65 to 324,500. |
| `cc1 denomination amount` | number as text | 100.00 | 2 | 200; 200.00 | The nominal dollar label of the first price point. Always 200. Two distinct strings only because 13,291 rows write it as "200.00". |
| `cc1 lcu code` | text | 100.00 | 43 | USD; AOA | Three-letter ISO 4217 code of the sending country's currency at the first price point. |
| `cc1 lcu fee` | number as text | 99.99 | 3,962 | 2900; 6.99 | The visible transfer fee at the first price point, in the sending country's currency. Median 6.24 in local units, maximum 246,420. 15,258 rows charge exactly zero, which is the "no fee" marketing offer whose cost sits in the exchange rate instead. |
| `cc1 lcu fx rate` | number as text | 99.99 | 80,136 | 0.084; 1 | The exchange rate the provider offered at the first price point. Exactly 1 means the service sends and pays out in the same currency, so there is no exchange at all. |
| `cc1 fx margin` | number as text | 99.99 | 2,948 | 7.49; 0 | Percentage difference between the provider's exchange rate and the interbank rate, at the first price point. Median 1.47, range -67.48 to 59.98. **A zero here is ambiguous**: it is a real zero for a same-currency service, and it is a placeholder for "not disclosed" whenever `transparent` is no. See the code table below. |
| `cc1 total cost %` | number as text | 99.99 | 4,673 | 16.28; 4.45 | Total cost at the first price point as a percentage of the amount sent. Median 5.04, range -58.92 to 307.20. It is the fee expressed as a percentage of `cc1 lcu amount` plus `cc1 fx margin`; that identity holds to within 0.02 points on 204,409 of the 204,446 rows where both sides can be computed. Negative values are real and come from promotional exchange rates, as one of the publisher's own standard notes says. |
| `cc2 lcu amount` | number as text | 100.00 | 72 | 500; 83000 | Amount sent at the second price point, local currency. Range 150 to 811,000. |
| `cc2 denomination amount` | number as text | 100.00 | 2 | 500; 500.00 | Nominal dollar label of the second price point. Always 500. |
| `cc2 lcu code` | text | 100.00 | 43 | USD; AOA | Currency code at the second price point. Identical to `cc1 lcu code` on all 204,469 rows, so it carries nothing new. |
| `cc2 lcu fee` | number as text | 99.49 | 4,572 | 5700; 9.99 | Visible transfer fee at the second price point, local currency. Median 8.00. Empty on 1,038 rows, of which 573 carry the standard note "Send limits on amount" and others an explicit cap such as "This service is available only for transfers up to MYR 1500" (17 rows), so the larger amount was not priced because the service does not allow a send that big. |
| `cc2 lcu fx rate` | number as text | 99.49 | 79,791 | 0.084; 1 | Provider exchange rate at the second price point. |
| `cc2 fx margin` | number as text | 99.49 | 2,935 | 7.49; 0 | Exchange rate margin at the second price point, with the same ambiguity as `cc1 fx margin`. Median 1.46. |
| `cc2 total cost %` | number as text | 99.49 | 3,490 | 14.36; 3.40 | Total cost at the second price point as a percentage. Median 3.40, range -60.81 to 125.91. Systematically lower than `cc1 total cost %` because the fixed fee spreads over a larger amount. |
| `inter lcu bank fx` | number as text | 100.00 | 52,576 | 0.0908; 1 | The interbank exchange rate on the day of collection. This is the benchmark both `fx margin` columns are measured against. |
| `transparent` | text | 100.00 | 3 | yes; Yes; no | Whether the provider disclosed the exchange rate it would apply, at the time of the survey. yes 187,991; Yes 13,117; no 3,361. Lower-case the value before filtering on it. |
| `Standard Note` | free text | 23.76 | 184 | "This RSP is not transparent…"; "LCU service" | The publisher's standardized caveat for the row. RSP means remittance service provider. The six most common notes are: an account is required for detailed price information (6,142 rows); the warning that a zero margin on a non-transparent service does not mean zero cost (3,000); the corridor sends and pays out in euro (2,685); a negative margin may be a promotion (2,239); LCU service, meaning local currency unit (2,204); USD service (1,617). Read this column before drawing any conclusion from a zero margin. |
| `note2` | free text | 0.14 | 37 | "Transferwise has changed its name to 'Wise'" | A second free-text note, filled on 288 rows. The workbook's `Legend` sheet documents it as "standard note 2: provides additional information on the service". Mostly corridor-level warnings that the money is paid out in a hard currency and the receiver may face a further conversion cost that is not in this data. |
| `receiving network coverage` | text | 100.00 | 4 | High; Medium; Low | How extensive the provider's payout network is in the receiving country, ranked since 2016 Q2 as high, medium or low. High 146,982; Medium 45,385; Low 12,090; plus 12 rows of lower-case "low". |
| `pickup location` | text | 43.46 | 16 | Agent; Bank branch; Home delivery | The methodology page says that when a transaction is disbursed in cash, the type of location where the money can be picked up is also recorded. Empty on 115,614 rows. A blank is not a reliable signal that the payout is not cash: 31,587 of those blank rows have `pickup method` = Cash, against 87,158 cash rows that do carry a location. Cross-tabulate the two columns before you read anything into a blank. |
| `pickup method` | text | 100.00 | 10 | Cash; Bank account; Mobile wallet | How the receiver gets the money. Cash 118,745; Bank account 72,594; Mobile wallet 9,207; Own or partner bank account 2,302; a further 1,210 written as "Bank account (same/partner bank)". Two spellings of the own-or-partner category coexist. |
| `date` | mixed | 100.00 | 878 | 11/May/2016; 2025-02-07T00:00:00 | The day the price was collected. **Two formats in one column.** 191,352 rows are text in day/abbreviated-month/year form; the 13,117 rows from the 2025 Q1 and 2025 Q3 rounds are real Excel dates and come out as ISO timestamps. Parse both. Span: 9 May 2016 to 10 September 2025. |
| `corridor` | text | 100.00 | 372 | USAMEX; AGONAM | `source_code` and `destination_code` glued together into six characters. Redundant, but convenient as a grouping key. |

### `Dataset (up to Q1 2016)`

49,491 rows, 41 columns. Columns that mean the same thing as in the modern sheet are described briefly; the ones that differ are described in full.

| Column | Type | Filled % | Distinct | Example values | Meaning |
|---|---|---|---|---|---|
| `id` | integer as text | 100.00 | 49,486 | 13123; 44140 | Row identifier. Five ids, 44140 through 44144, are each used twice. The numbering has nothing to do with the modern sheet's `id`. |
| `period` | text | 100.00 | 17 | 2011_1Q; 2016_1Q | Survey period. Semiannual in 2011 and 2012, quarterly from 2013. |
| `source_code` | text | 100.00 | 35 | AUS | Sending country code. |
| `source_name` | text | 100.00 | 35 | Australia | Sending country name. |
| `source_region` | text | 100.00 | 4 | .. | Region of the sending country. |
| `source_income` | text | 100.00 | 5 | High income: OECD | Income group of the sending country, **on the old vocabulary**: High income: OECD 38,722; High income: nonOECD 6,454; Upper middle income 3,224; Low income 978; Lower middle income 113. OECD is a club of mostly rich countries. These values do not line up with the modern sheet's five without a mapping you write yourself. |
| `source_lending` | text | 100.00 | 3 | .. | Lending category of the sending country. |
| `source_G8G20` | text | 100.00 | 3 | G20 | G8/G20 membership of the sending country. |
| `destination_code` | text | 100.00 | 105 | FJI | Receiving country code. |
| `destination_name` | text | 100.00 | 105 | Fiji | Receiving country name. |
| `destination_region` | text | 100.00 | 7 | East Asia & Pacific | Region of the receiving country. |
| `destination_income` | text | 100.00 | 6 | Upper middle income | Income group of the receiving country, old vocabulary. |
| `destination_lending` | text | 100.00 | 4 | IBRD | Lending category of the receiving country. |
| `destination_G8G20` | text | 100.00 | 2 | .. | G8/G20 membership of the receiving country. |
| `firm` | text | 100.00 | 637 | Coinstar; MoneyGram | Provider name. 440 of these names also appear in the modern sheet, so the two panels can be linked at the firm level once you normalize capitalization. |
| `firm_type` | text | 100.00 | 10 | Money Transfer Operator; Bank | Provider category. Includes "Credit Union" on 5 rows, a value that never appears in the modern sheet. |
| `product` | text | 100.00 | 37 | Cash to cash; Account to account | **Discontinued after 2016 Q1.** The old single-column description of the shape of the transaction, from a documented list of fourteen categories such as door to door, cash to cash, account to account (same bank), account to cash, credit or debit card service, prepaid card service, online service, mobile service, USD service, LCU service and EUR service. Comma-separated when a service offers several. Cash to cash 19,514; Account to account 9,441; Online service 7,671; Cash to account 3,176. There is no clean crosswalk to the modern `payment instrument` and `pickup method` pair, because `product` mixes funding, payout and currency in one field. 214 rows read "N/A". |
| `sending location` | text | 100.00 | 9 | at Branch; On-line; Not available | **Renamed to `access point` from 2016 Q2** and re-coded. at Branch 17,401; Not available 16,559; On-line 7,249; at Branch,Call Center 5,941. The 16,559 "Not available" rows are a third of the panel and sit entirely in the first six periods, 2011 Q1 to 2013 Q2, so read them as not recorded rather than as a real category (inferred from the data). |
| `speed actual` | text | 100.00 | 7 | Less than one hour; 3-5 days | Time to availability, the same six categories, plus 10 rows of "N/A". |
| `cc1 lcu amount` | number as text | 99.79 | 35 | 200 | Amount sent at the first price point, local currency. 103 rows are empty. |
| `cc1 denomination amount` | number as text | 99.84 | 4 | 200; 201; 202; 6 | Nominal dollar label. Almost always 200, but 5 rows read 201, 202 or 6. Those five are typing noise. |
| `cc1 lcu code` | text | 100.00 | 29 | AUD | Currency at the first price point. |
| `cc1 lcu fee` | number as text | 99.99 | 979 | 11; 12 | Visible fee, local currency. Median 10.00. |
| `cc1 lcu fx rate` | number as text | 100.00 | 17,462 | 1.77; 1 | Provider exchange rate. |
| `cc1 fx margin` | number as text | 100.00 | 1,615 | 3.29; 0 | Exchange rate margin, percent. Median 1.20, range -16.58 to 36.05. Same zero ambiguity as the modern sheet. |
| `cc1 total cost %` | number as text | 100.00 | 2,940 | 8.79 | Total cost at the first price point, percent. Median 6.68, range -8.97 to 75.00. |
| `cc2 lcu amount` | number as text | 100.00 | 39 | 500 | Amount sent at the second price point. |
| `cc2 denomination amount` | number as text | 99.84 | 3 | 500; 501; 502 | Nominal dollar label of the second price point. |
| `cc2 lcu code` | text | 99.99 | 29 | AUD | Currency at the second price point. |
| `cc2 lcu fee` | number as text | 99.58 | 1,058 | 10; 12 | Visible fee at the second price point. |
| `cc2 lcu fx rate` | number as text | 99.41 | 17,408 | 1.77 | Provider exchange rate at the second price point. |
| `cc2 fx margin` | number as text | 99.62 | 1,620 | 3.29 | Exchange rate margin at the second price point. |
| `cc2 total cost %` | number as text | 99.62 | 2,022 | 5.29 | Total cost at the second price point, percent. Median 4.29, range -13.42 to 42.65. |
| `inter lcu bank fx` | number as text | 100.00 | 3,879 | 1.83024 | Interbank exchange rate on the day of collection. |
| `transparent` | text | 100.00 | 2 | yes; no | Whether the provider disclosed the exchange rate. yes 45,434; no 4,057. Consistently lower case in this sheet. |
| `note1` | free text | 36.36 | 117 | "This RSP is not transparent…" | **Renamed to `Standard Note` from 2016 Q2.** The same standardized caveats, filled far more often here, on 36 percent of rows against 24 percent in the modern sheet. |
| `note2` | free text | 11.56 | 142 | "In this corridor all RSPs send and pay out in EUR…" | Second free-text note. |
| `coverage` | text | 99.96 | 6 | Nationwide; Major cities | **Renamed to `receiving network coverage` from 2016 Q2 and re-coded.** Old five-value scale: Nationwide 46,632; Major cities 1,094; Main city 850; Urban only 616; Rural only 279; plus 2 rows of "N/A" and 18 blanks. It does not map cleanly onto the modern high, medium, low scale. |
| `pick-up method` | text | 81.03 | 31 | Cash; Bank Account | The modern `pickup method` under an older and dirtier vocabulary: 31 distinct strings, including comma-separated combinations, mixed capitalization and one typing error, "Bank Acciunt". Empty on 9,388 rows. Note the hyphen in the column name here, which the modern sheet drops. |
| `date` | text | 100.00 | 125 | 24/Jan/2011 | Day of collection, all in day/abbreviated-month/year text form in this sheet. Span 20 January 2011 to 9 March 2016. |
| `corridor` | text | 100.00 | 310 | AUSFJI | Sending code glued to receiving code. |

### `Countries`

A title line, then a header row, then 215 country rows. Read it with `skiprows=1`. The columns, in order, are: ISO 3166-1 alpha-3 country code; country name; region; income group; lending category; G8/G20 flag. Values use `..` for "not applicable". The header states it was updated for 2025 Q3. It is a convenience lookup that repeats the six country attributes already carried on every data row, so joining it adds nothing unless you want the attributes for a country that never appears as a sender or a receiver.

### Value-code tables

**`transparent` against a zero exchange-rate margin, modern sheet.** This is the single most important trap in the file.

| `transparent` | Rows | Of those, `cc1 fx margin` exactly 0 |
|---|---|---|
| yes (either capitalization) | 201,108 | 25,886 |
| no | 3,361 | 3,351 |

When `transparent` is `no`, the provider refused to quote its exchange rate, and the publisher stores the margin as a literal `0`. That zero means "unknown", not "free". The publisher's own standard note says exactly that. Treat those 3,361 rows as censored, and remember that `cc1 total cost %` on them is a lower bound on the real cost. The 25,886 transparent rows with a zero margin are a different thing: they are mostly same-currency services where both the interbank rate and the provider rate are 1 and there is genuinely no exchange. The legacy sheet shows the same pattern: 4,036 of its 4,057 non-transparent rows carry a zero margin.

**`access point`, modern sheet, most common values.** Internet 99,969; Agent 69,702; Bank branch 13,385; Bank branch and Call Center 6,183; Call Center 3,020; Agent and Internet 2,628; Agent and Call Center 2,108; Post Office branch 1,752; Mobile phone 1,623. The share of rows mentioning Internet rises from 30.4 percent in 2016 Q2 to 67.6 percent in 2025 Q3.

**`payment instrument`, modern sheet, most common values.** Cash 65,699; Bank account transfer 58,764; Debit card 23,922; Credit Card 16,421; Debit/credit card 10,566; Bank account transfer with Debit/credit card 10,288; Mobile money 1,601 on its own and 1,744 rows in total.

**`pickup method`, modern sheet, all ten values.** Cash 118,745; Bank account 72,594; Mobile wallet 9,207; Own/partner bank account 2,302; Bank account (same/partner bank) 1,210; Own/partner Bank account 204; Debit card 131; ATM Network 62; Home Delivery 13; "Bank account, Cash" 1.

**`firm_type` against the median cost of sending the 200-dollar equivalent, modern sheet.** Mobile Operator 2.69 percent (1,037 rows); Money Transfer Operator 4.75 (165,547); Money Transfer Operator / Post office 5.64 (1,893); Post office 6.07 (1,698); Non-Bank FI 7.88 (182); Bank 8.20 (32,475); Bank / Money Transfer Operator 8.70 (1,383).

**`speed actual` against median cost, modern sheet.** Next day 4.38 percent; Same day 4.74; Less than one hour 5.11; 2 days 5.20; 3-5 days 5.74; 6 days or more 9.10. Slower is not cheaper in this data.

**Largest firms by number of quotes, modern sheet.** Western Union 34,711; MoneyGram 27,042; Ria 12,607; WorldRemit 11,870; Remitly 8,906; Small World 7,697; Wise 3,821 plus Transferwise 1,155; Azimo 3,527; Xoom 3,317; Walmart2World 2,508. The median firm appears in only 2 corridors; the busiest appears in 364.

---

## 6. Notes

### Watch out for

- **The two data sheets do not stack.** They share 36 column names. Five names appear only in the legacy sheet (`product`, `sending location`, `note1`, `coverage`, `pick-up method`) and six only in the modern sheet (`payment instrument`, `access point`, `Standard Note`, `receiving network coverage`, `pickup method`, `pickup location`), and the income-group vocabulary changed in 2016 Q2. Stacking them with `pd.concat` silently produces a table full of holes. Fix: work with the modern sheet alone, or align the two on the columns that survived and say in writing which ones you kept.
- **A zero in `cc1 fx margin` is overloaded.** It means "genuinely no exchange" on a same-currency service and "the provider would not say" on a non-transparent one. Fix: filter on `transparent` first, lower-cased, and treat the non-transparent rows separately or drop them on purpose.
- **`transparent` has three spellings.** `yes`, `Yes` and `no`. The capitalized `Yes` shows up only in the 2025 Q1 and 2025 Q3 rounds. Fix: apply `.str.lower()` before you filter.
- **Pandas returns 47 columns, not 42.** The modern sheet's header names 42 columns, but the 6,470 rows of the 2025 Q3 round carry values in five further unlabeled columns, which pandas names `Unnamed: 42` to `Unnamed: 46`. They hold a year and country-code-plus-year strings, and are not part of the documented schema. Fix: pass `usecols="A:AP"` when reading, as section 4 shows.
- **`2025_2Q` is missing.** Thirty-eight quarters passed between 2016 Q2 and 2025 Q3; 37 appear in the file. The publisher's [September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) never mentions Q2 2025 either, comparing Q3 2025 against Q1 2025 throughout. Fix: never assume a fixed number of quarters between two dates, and say in your writing that the gap is real.
- **Corridors sending from Russia stop after 2021 Q4.** `RUS` is a sending country in all 17 legacy periods and in every modern period from 2016 Q2 to 2021 Q4, 1,446 modern rows in all, and then in none. The publisher's [September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) explains why: "Due to the ongoing Russia-Ukraine war, RPW did not include any data on corridors originating in the Russian Federation in Q1 and Q2 2022. From Q3 2022 to Q3 2025, only publicly available online data on corridors originating in Russia were collected... Due to this deviation in data collection methodology, these services were not included in the main analysis in Q3 2025; instead, the data are presented in Annex V." So a Russia question cannot be answered from these worksheets past 2021, whatever the report's Annex V shows.
- **Two date formats in one column.** In the modern sheet, 191,352 rows read like `11/May/2016` and 13,117 rows, all from the 2025 Q1 and Q3 rounds, read like `2025-02-07T00:00:00`. A plain `pd.to_datetime(col, errors="coerce")` is not enough: in the 4 September 2026 download it turned 173,870 of the 204,469 values into `NaT` without raising anything. Fix: `pd.to_datetime(col, format="mixed", dayfirst=True, errors="coerce")` parsed all 204,469 in that download. Whatever you use, count the `NaT` values afterwards and check the minimum and maximum date against the 9 May 2016 to 10 September 2025 span given in section 5.
- **`..` is a category, not a missing value.** It appears in every region, lending and G8/G20 column and means "not applicable". Fix: do not convert it to a null and then drop those rows; you would lose 178,796 rows of the sending-region column alone.
- **A blank `pickup location` does not tell you the payout is not cash.** It is blank on 56.5 percent of modern rows, and 31,587 of those blanks have `pickup method` = Cash. Fix: use `pickup method` when you need to know how the money is handed over, and treat `pickup location` as extra detail that is often missing.
- **Firm names are free text.** Capitalization varies, "Transferwise" and "Wise" are the same company either side of a rename that one `note2` value records, and separate brand names in the file can belong to one company: Western Union's [2025 Form 10-K, on SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1365135/000119312526061340/wu-20251231.htm), says "We offer money transfer services under the Western Union, Vigo, and Orlandi Valuta brands", and all three names appear separately in this file. Fix: build a small crosswalk table by hand before counting firms or ranking them.
- **`payment instrument` and `access point` hold lists.** They are comma-separated when a service accepts several. Grouping on the raw string gives 26 and 22 categories; splitting on the comma leaves 9 and 8 distinct values, and several of those are capitalization or wording variants of each other. Fix: split on the comma, or filter with `.str.contains()`, and state which you did.
- **Fees are in local currency, not dollars.** `cc1 lcu fee` of 2900 is 2,900 units of whatever `cc1 lcu code` says. Fix: use the percentage columns, `cc1 total cost %` and `cc2 total cost %`, which already divide by the amount sent, whenever you compare across corridors.
- **The "200 dollars" is not 200 dollars.** `cc1 lcu amount` was fixed in local currency back in 2009 and has not moved since, so its dollar value drifts as exchange rates move. Fix: treat the basket as a fixed local amount, and do not describe it as a live 200-dollar transfer.
- **Negative and zero total costs are real.** 1,308 modern rows have a negative `cc1 total cost %` and 1,156 are exactly zero. One of the publisher's own standard notes says a negative margin "may be due to a promotion/special offer that the RSP had on at the time the information was collected". Fix: do not clip them quietly. Drop them or flag them on purpose and write down which you chose.
- **Rising row counts are coverage, not growth.** Rows per quarter climb because the survey adds firms and corridors. Fix: compute medians and averages within a corridor and quarter, or hold the set of corridors fixed, before claiming a trend over time.
- **Duplicate identifiers in the legacy sheet.** Ids 44140 through 44144 are each used twice, so `id` is not a safe index there.
- **183 groups of identical modern rows**, covering 372 rows, once you ignore `id`. Deduplicating on everything but `id` drops 189 rows. Decide and record whether you want that.
- **The workbook is slow and heavy.** Inside the `.xlsx`, which is a zip archive, the modern sheet is a single XML part that unzips to about 298 MB, so reading it is slow and memory-hungry. Fix: read it once, write each sheet to CSV or Parquet, and work from that afterwards.
- **Country names carry accents.** "Côte d'Ivoire" and "Türkiye" will break a CSV written in the wrong encoding. Fix: always pass `encoding="utf-8"` when you write a CSV.
- **Two names for the same country code.** "Czech Republic" and "Czechia", "Turkey" and "Türkiye", and two spellings of the Middle East region. Fix: group on `source_code`, `destination_code` and `corridor`, never on the display names.
- **`sending network coverage` is documented but is not in the file.** The workbook's `Legend` sheet lists it under "as of Q2 2016, categories changed as follows" as "NEW: ranks the extensiveness of the network of the firm in the sending country", and the [methodology page](https://remittanceprices.worldbank.org/methodology) says coverage is captured "both for the sending and receiving networks" from Q2 2016. Neither data sheet has that column. Only `receiving network coverage` is there. Do not plan work around the sending-side ranking.
- **The publisher's corridor counts do not match the file, or each other.** This workbook holds 372 corridors. The methodology page says 367, from 48 sending and 105 receiving countries; the September 2025 report says 367 in one place and 358 in another; the [catalog record](https://datacatalog.worldbank.org/search/dataset/0037898/Remittance-Prices-Worldwide) says 377, from 48 sending and 111 receiving countries. Quote the file's number for the file and say so.
- **The report's own per-provider-type figures for 2025 Q3 do not add up.** In the same passage the report calls mobile operators "the cheapest RSP type" and prints 5.58 percent for them and 5.58 percent for post offices, above the 4.72 percent it prints for MTOs. Its longer-run statement, that banks sit above the global average while MTOs and mobile operators sit below, is consistent with this file. Do not build a single-quarter ranking of provider types on the report's text.
- **Changes are coming to later releases, but not to this one.** Two are announced or in progress upstream, and neither affects the Q3 2025 files this document describes, because those files are fixed. A download taken later will differ. First, the survey keeps growing: the [September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) says 519 services moved from its prospects index into the main analysis in that quarter alone, 138 more entered the prospects index, and "RPW will continue to monitor and include new services when and where relevant using the prospects index", so expect later releases to carry more rows and firms. Second, the region names are mid-change: this file carries both spellings of the Middle East region while the Bank's current [country and lending groups page](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups) uses only the longer one, so a later release may drop the old spelling.
- **The report's target changed in 2023, which matters only if you compare report editions.** A footnote in the September 2025 report says that from the Q1 2023 edition the reporting was adjusted to keep only the SDG 10.c targets and drop the older G8 and G20 5 percent target, with "no change in the methodology". Older editions score the same data against a different target.
- **The `Methodology` sheet is a picture.** There is no readable text on it. The report PDF you download alongside the workbook covers the same ground.

### What the data does not contain

- **No volumes, no revenue, no transactions.** Nothing says how many transfers were sent, how much money moved, or which service any customer actually chose. Every average you compute is an average over surveyed services, not over dollars and not over people. Country-to-country flow estimates are published separately by international institutions, at an annual, country-pair level.
- **No customers.** No senders, no receivers, no ages, no incomes, no migrant population counts. There is no way to weight a price by how many people face it without bringing in outside data. Migrant population counts by country pair are collected by international organizations and national statistical agencies.
- **No market share.** The survey aims to cover at least 80 percent of a corridor's market in aggregate, but records no share for any individual firm. So "the cheapest provider in this corridor" cannot be turned into "what the average sender pays". This is the most common misreading of this dataset.
- **The true cost of non-transparent services is unknown.** On 3,361 modern rows the margin is stored as zero because the provider would not disclose a rate. The real cost is higher by an unknown amount, and nothing inside the file can recover it.
- **No geography below the country.** Corridors are country pairs. Nothing distinguishes money sent from Los Angeles from money sent from Chicago, even though the methodology page says data were captured "from the main sending location/area for the corridor in question to the capital city or most populous city in the receiving market". A Los Angeles question has to be approached through the corridors that matter to Los Angeles, not through Los Angeles itself.
- **Only two send amounts.** The equivalent of 200 and 500 US dollars, and nothing else. Nothing prices a 50-dollar transfer, a 3,000-dollar transfer, or the fee tiers in between.
- **No charges levied in the receiving country.** The [methodology page](https://remittanceprices.worldbank.org/methodology) says that "in some cases, there may be fees and taxes charged by the recipient country/organization that are not tracked in this database", and several `note2` values warn that a receiver paid in a hard currency may face a further conversion cost. The recorded total cost is a sender-side cost.
- **No promotions, coupons or loyalty pricing.** A negative margin may mean a promotion was running on the day of collection, but there is no field for a first-transfer discount, a referral credit or a loyalty tier. A repeat customer may pay something quite different.
- **Not every provider.** The survey aims at firms covering 80 percent of a corridor's market, so small local exchange shops, informal networks and cryptocurrency routes do not appear. The publisher's [September 2025 report](https://datacatalogfiles.worldbank.org/ddh-published/0037898/DR0095413/RPW_main_report_and_annex_Q325.pdf) says 519 services were moved from its prospects index into the main analysis in 2025 Q3 alone, so a firm's first row is an administrative event, not a market entry.
- **No quality, reliability or complaints.** Nothing records failed transfers, money that arrived later than advertised, blocked accounts or customer complaints. The methodology page defines the speed of transfer as "the time needed for the remittance to be available for the receiver", noted once per product in one of six standard categories, not a measured delivery time. Complaint records are held by national financial regulators and consumer bodies.
- **A snapshot four times a year, and one round missing.** Each row carries one collection date, so anything that changed inside a quarter is invisible. The methodology page adds that collection within a corridor runs "over a limited period of time, in order to control for fluctuations in exchange rates".
- **No history before 2011.** The publisher's report says RPW launched in September 2008 and charts its global series from 2009 Q1, but this workbook starts at 2011 Q1. Earlier quarters would have to come from archived reports.
- **Association, not cause.** Comparing an online service against a counter service inside one corridor and quarter is a fair comparison of what a sender would have been quoted, because both faced the same currencies, the same interbank rate and the same rules. What it does not establish is why. Firms choose which channels to offer and where, so the digital services in a corridor come from a different and generally newer set of firms than the counter services, and the price gap mixes the channel together with the firm and its cost base. The same caution applies over time: costs fell while digital share rose, but the survey also kept adding firms and corridors, so part of any trend is a change in what was measured.
