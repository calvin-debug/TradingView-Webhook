# Webhook

This is a multi-user Flask application that is meant to process incoming
webhook signals from TradingView and turn them into trades at the
selected exchange.

# Exchanges

Currently supported exchanges are:

- Binance
- BinanceUS

# Functionality

Users have a chance to sign up and configure their accounts. This includes
setting their API credentials to connect to their selected exchange.

The application displays all currently open trades as a list on the users'
homepage, along with information about the number of entries taken on that
particular trade and the current PnL for that trade.

Previous acitivity and trades are stored in the users' log. A shortened version
of this user log is displayed on the users' homepage. The full log can be
accessed on the /log route.
