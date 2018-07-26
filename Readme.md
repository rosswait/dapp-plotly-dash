# dapp-plotly-dash

An interactive analysis of auction listings for digital collectibles on the Etherium platform.  Built on [Plotly's Dash framework](https://dash.plot.ly/) and hosted on Google's App Engine. Dataset is static & managed in-memory via pandas.

Currently deployed on Google App Engine: https://dapp-scatter-dashboard.appspot.com/

![Animated example of scatterplot selection](https://storage.googleapis.com/dapp-scatter-dashboard.appspot.com/J5iTHL9gHn.gif "Individual listings can be investigated on the scatterplot")

1. [Auction Overview](#overview)
2. [Dashboard Specifics](#dashboard-specifics)
3. [Credits](#credits)

## Overview

### Decentralized Applications

Decentralized applications, or "dApps" for short, are applications which eschew a traditional centralized data backend in favor of a decentralized, peer-to-peer architecture.  While many of these decentralized applications are designed to power [fungible](https://en.wikipedia.org/wiki/Fungibility) cryptocurrencies, such as Bitcoin, there also exist standards which use blockchain technology for enabling the creation of contracts for unique, non-fungible digital goods. [Etherium's ERC-721 standard](https://medium.com/crypto-currently/the-anatomy-of-erc721-e9db77abfc24), which is profiled in this dashboard, has been the protocol of choice for many popular applications, such as [Cryptokitties](https://www.cryptokitties.co/). One consumer benefit of these digital collectibles is 'true ownership' of goods, which are not reliant on central infrastructure to guarantee uniqueness, validate legitimacy, and facilitate transferral. Better yet (for proponents of open data), the historical record of these transfers is written to the public blockchain.

### Auction Data

Most ERC-721 auctions follow a [Dutch Auction](https://en.wikipedia.org/wiki/Dutch_auction) model, in which the listing price linearly drops in value until the good is either purchased by the first bidder or the auction ends.  This data set covers all auction listings for goods across 15 selected applications, between June '17 and June '18.

* Auctions are priced in [Etherium](https://en.wikipedia.org/wiki/Ethereum), the value of which can fluctuate with respect to other currency.
* Auctions are categorized by their ending state, which can either be a sale or a delisting.  In-progress auctions are marked as 'unresolved.'
* Several axes are only germane to successfully sold auctions ('Sold Price', 'Start-Sold Range', 'Start-Sold Range %').  If any of these fields are selected, the dashboard will remove unsuccessful auctions from the scatterplot.

## Dashboard Specifics

#### Dimensions
* The X- and Y- axes can be customized with the dropdowns.
  * Each selectable dimension has a default axis scale, though you can manually toggle between log and linear scales.
  * The box plot inherits the selected Y-axis dimension by default, though this can also be customized.

#### Drilling Down
* Discrete auction listings can be investigated by clicking on individual markers on the scatter plot.
* Listings can be filtered for any of the below characteristics of a given selected point.  Please note that selecting any of these options will automatically disable sampling of the data set.  Similarly, removing these options will re-apply the sampling filter, out of consideration for application performance.
  * Token Item Id (eg. a unique item)
  * Buyer
  * Seller (frequently an auction house or escrow service)

#### Sampling
* The central scatterplot will display a maximum of 100,000 auction listings per application, by default.  The primary purpose of this feature, which can be disabled, is to prevent the data from CryptoKitties (which has more than 600,000 listings) from impacting performance.  No other application comes close to reaching this sampling limit.
* The box and whisker plot does not observe the sampling limit, as it does not need to render every individual data point

## Credits

* I make use of the bootstrap CSS stylesheet from Plotly's [Oil and Gas example dash](https://github.com/plotly/dash-oil-and-gas-demo).
* Plotly's [Drug Discovery dash](https://github.com/plotly/dash-drug-discovery-demo/blob/master/app.py) was also a very useful resource for instrumenting chart click callbacks.
* Footer styling lifted from Ivan Nieto's [Great Balls of Fire dashboard](https://bitbucket.org/inieto/great-balls-of-fire/).
* Adriano Yoshino's [demonstration article](https://medium.com/a-r-g-o/using-plotlys-dash-to-deliver-public-sector-decision-support-dashboards-ac863fa829fb) provided a very lucid, accessible springboard for getting my project off the ground.
