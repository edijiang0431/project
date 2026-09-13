# Data Fit: World Bank Remittance Prices Worldwide

## What does one row represent?

One row is one firm's remittance service in one country-to-country corridor during one quarterly survey round. A firm can have multiple rows when its services differ by channel, payment method, speed, or pickup method. The overview states: “One row is one firm's service, in one country pair, as priced in one quarterly round” ([Section 1](dataset_wb-remittance-prices/data_overview_wb-remittance-prices.md#1-description-and-industry-context)). A row is a price quote, not a customer or transaction.

## What was observed?

- **People:** No individual senders or receivers. Researchers posed as customers, or prices were collected from websites and APIs.
- **Places:** 372 corridors involving 49 sending and 105 receiving countries in the modern sheet. There is no city-level data.
- **Events:** Provider price quotes for specific services and transfer amounts, not actual transfers or customer choices.
- **Time:** 2011 Q1–2025 Q3, semiannual at first and generally quarterly afterward. The 2025 Q2 round is missing.

## Audience 1: IFAD program officer

**Decision:** Which three corridors should receive a cost-reduction program?

### Useful columns

- Corridor: `corridor`, `source_code`, `destination_code`, `source_name`, `destination_name`
- Price: `cc1 total cost %`, `cc2 total cost %`, `cc1 lcu fee`, `cc1 fx margin`
- Time and providers: `period`, `date`, `firm`, `firm_type`
- Service features: `access point`, `payment instrument`, `pickup method`, `speed actual`, `receiving network coverage`
- Caveats: `transparent`, `Standard Note`, `note2`

### Supported

- Rank surveyed corridors by quoted cost.
- Identify corridors that remain expensive over time.
- Compare surveyed providers, channels, speeds, and pickup methods.
- Identify corridors with frequent exchange-rate non-disclosure.
- Create a price-based shortlist for further study.

### Partly supported

The data can identify expensive corridors but not where a program would help the most people because it has no customer or transfer-volume data. Firm counts do not measure competition because market shares are missing. Historical quotes show trends but cannot reliably predict next year's prices.

### Outside the data's scope

Customer characteristics, actual provider choice, transaction volume, market share, program cost, political feasibility, complaints, reliability, and the likely impact of an IFAD intervention were not observed.

### Association or causation?

Only association. The data may show that some corridors, providers, or service channels have lower prices, but these groups also differ in many unobserved ways. It cannot prove that a particular feature caused the price difference or that an IFAD program would lower costs.

## Audience 2: CHIRLA campaign researcher

**Decision:** Which U.S.-origin corridor should receive a “know what you really pay” campaign?

### Useful columns

- U.S. corridors: `source_code`, `corridor`, `destination_code`, `destination_name`
- Price components: `cc1 total cost %`, `cc2 total cost %`, `cc1 lcu fee`, `cc1 fx margin`, `inter lcu bank fx`
- Transparency: `transparent`, `Standard Note`, `note2`
- Service details: `access point`, `payment instrument`, `pickup method`, `firm`, `firm_type`, `speed actual`
- Time: `period`, `date`

### Supported

- Compare quoted prices across surveyed U.S.-origin corridors.
- Compare internet and counter-service quotes.
- Show that a zero fee may still include an exchange-rate cost.
- Identify services with undisclosed exchange rates.
- Develop corridor-specific educational examples.

### Partly supported

The data can identify expensive U.S.-origin corridors but not which corridor matters most to Los Angeles residents or CHIRLA members. It can compare observed prices, but it does not measure current prices, service reliability, customer usage, or the number of people affected.

### Outside the data's scope

Sender location within the United States, CHIRLA membership, audience size, customer behavior, promotions, actual service reliability, and campaign impact were not observed.

### Association or causation?

Only association. Lower internet prices, for example, do not prove that using the internet causes lower prices because firms and service types also differ. The data cannot prove that a campaign would change customer behavior or reduce costs.
