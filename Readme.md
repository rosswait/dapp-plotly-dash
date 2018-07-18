# dapp-plotly-dash

An interactive analysis of auction listings for digital collectibles on the Etherium platform.  Built on [Plotly's Dash framework](https://dash.plot.ly/) and hosted on Google's App Engine.  Data is managed in-memory through Pandas.

#Overview

### Decentralized Applications

Decentralized applications, or "dApps" for short, are applications which eschew a traditional central backend in favor of a decentralized, peer-to-peer architecture.  While many of these decentralized applications are designed to power fungible cryptocurrencies, such as Bitcoin, there also exist standards which use blockchain technology for enabling the creation of contracts for unique, digital goods. [Etherium's ERC-721 standard](https://medium.com/crypto-currently/the-anatomy-of-erc721-e9db77abfc24), which is profiled in this dashboard, has been the protocol of choice for  popular applications such as [Cryptokitties](https://www.cryptokitties.co/). One consumer benefit of these digital collectibles is 'true ownership' of goods, which do are not reliant on central infrastructure to guarantee uniqueness, validate legitimacy, and facilitate transferral. Better yet (for proponents of open data), the historical record of these transfers is written to the public blockchain.

### Auction Data

Most ERC-721 auctions follow a [Dutch Auction](https://en.wikipedia.org/wiki/Dutch_auction) model, in which the listing price linearly drops in value until the good is either purchased by the first bidder or the auction ends.  This data set covers all auction listings for goods across 15 dApps, between June '17 and June '18.

* Auctions are price in [Etherium](https://en.wikipedia.org/wiki/Ethereum), the value of which can fluctuate with respect to other currency.
* Auctions are labeled by their end state, which can either be a sale or a delisting.  In-progress auctions are marked as 'unresolved.'
* Several fields are only germane to successfully sold auctions ('Sold Price', 'Start-Sold Range', 'Start-Sold Range %')

### Dashboard Specifics

####Sampling
* The central scatterplot will display a maximum of 100,000 auction listings per dApp, by default.  The primary purpose of this feature, which can be disabled, is to prevent the data from CryptoKitties (which has more than 600,000 listings) from impacting performance.  No other dApp comes close to reaching this sampling limit.
* The box and whisker plot, which renders an aggregated summarization of the selected data, does not observe the sampling limit

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
 * <Note: embed a GIF with this functionality>

### Tools Used

* Plotly community
* Chris's CSS stylings
