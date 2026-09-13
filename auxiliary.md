# Auxiliary Data: World Bank Remittance Prices Worldwide

## Audience 1: IFAD Program Officer

**Decision:** Which three remittance corridors should receive a cost-reduction program?

### Important Missing Information

The supplied dataset shows the quoted cost of sending money through each corridor, but it does not show the actual amount of money transferred or the number of people using each corridor. This information matters because a high-cost corridor may affect only a small number of people, while a slightly cheaper corridor may affect many more families. IFAD would need information about the size of each remittance flow to determine where a cost-reduction program could have the greatest impact.

### Possible Auxiliary Data Source

A promising source is the World Bank/KNOMAD Bilateral Remittance Estimates. It provides estimated remittance flows between sending and receiving countries in U.S. dollars. This could help IFAD consider both the quoted cost and the approximate size of each corridor.

Source: [World Bank Bilateral Remittance Estimates](https://data360.worldbank.org/en/indicator/WB_KNOMAD_BRE)

### Who Collects It?

The estimates are produced by the World Bank and KNOMAD. They are calculated using information such as total remittance inflows, migrant populations, and income levels. They are estimates rather than records of actual individual transfers.

### What Does One Row Represent?

One country-pair observation represents the estimated amount of remittances sent from one source country to one destination country during a given year.

### Likely Useful Fields

- Sending country
- Receiving country
- Year
- Estimated remittance flow in U.S. dollars

### How It Could Connect to the Supplied Data

The two datasets could be connected using the sending country and receiving country. The country names or codes could be combined to create a corridor identifier similar to the `corridor` column in the supplied dataset. The team would need to check whether both datasets use the same country names and codes.

### New Question It Would Make Answerable

Combining the two datasets could help answer: Which corridors have both high quoted remittance costs and large estimated remittance flows? This would give IFAD a stronger basis for creating a shortlist than using price alone.

### What Could Fail or Remain Uncertain

The bilateral remittance values are estimates, not observed transactions. They rely on assumptions about migrant populations, income, and total remittance flows. The estimates may also be from a different year than the price data. Country names or codes may not match exactly between the two datasets. In addition, the data does not show how many rural families would benefit or whether an IFAD program would successfully reduce costs.

### Synthetic Fallback

If the real auxiliary data cannot be connected, the team could create a small synthetic table with a corridor, estimated annual remittance flow, and average cost. This could demonstrate how the two datasets might work together. The synthetic values would be clearly labeled as fictional and would not be used as real evidence.
## Audience 2: CHIRLA Campaign Researcher

**Decision:** Which U.S.-origin corridor should receive a “Know What You Really Pay” campaign?
### Important Missing Information

The supplied dataset does not show where senders live within the United States or how many people in Los Angeles may use each remittance corridor. This information matters because CHIRLA needs to choose a campaign audience that is both affected by remittance costs and large enough to justify the campaign. The price data alone cannot show which corridor is most relevant to Los Angeles communities.

### Possible Auxiliary Data Source

A promising source is the U.S. Census Bureau's American Community Survey, especially Table B05006, Place of Birth for the Foreign-Born Population. It provides population estimates for people born in different countries and can be filtered to Los Angeles County.

Source: [U.S. Census ACS Table B05006](https://data.census.gov/table/ACSDT5Y2024.B05006)

### Who Collects It?

The U.S. Census Bureau collects the data through the American Community Survey. The survey produces population estimates rather than a complete count of every resident.

### What Does One Row Represent?

An extracted record could represent the estimated foreign-born population from one place of birth within a selected geographic area and survey period. It represents a population estimate, not one individual person.

### Likely Useful Fields

- Geographic area
- Place or country of birth
- Estimated foreign-born population
- Margin of error
- Survey year

### How It Could Connect to the Supplied Data

The remittance data could first be filtered to corridors with the United States as the sending country. The destination country for each corridor could then be matched to the country-of-birth categories in the Census data. The connection would require a country-name or country-code mapping because the two datasets may use different labels.

### New Question It Would Make Answerable

Combining the two datasets could help answer: Which high-cost U.S.-origin remittance corridors correspond to the largest foreign-born communities in Los Angeles County? This could help CHIRLA create a more relevant campaign shortlist.

### What Could Fail or Remain Uncertain

Country of birth does not prove that a person sends remittances, so the Census population is only a proxy for the potential campaign audience. The data does not identify CHIRLA members or measure actual remittance behavior. Country categories may not match the World Bank data exactly, and the Census survey period may not match the quarterly price data. Population estimates also include margins of error.

### Synthetic Fallback

If the Census data cannot be connected, the team could create a small synthetic table containing destination country, estimated Los Angeles audience size, and average remittance cost. It could demonstrate how campaign prioritization might work, but the values would be clearly labeled as fictional and would not support a real recommendation.

## What We Checked

We reviewed the supplied data overview to identify important information that the Remittance Prices Worldwide dataset does not contain. We also reviewed the World Bank/KNOMAD bilateral remittance estimates as a possible source for corridor size and the U.S. Census American Community Survey as a possible source for the size of foreign-born communities in Los Angeles County.

## Open Questions

- Are the bilateral remittance estimates recent enough to support IFAD's decision for next year?
- Can the country names and codes in the auxiliary datasets be matched reliably to the World Bank price data?
- Does IFAD have more detailed internal data about rural remittance recipients or program feasibility?
- Does CHIRLA have internal information about its members' countries of origin and remittance behavior?
- Is foreign-born population an acceptable proxy for the potential audience of a CHIRLA campaign?
