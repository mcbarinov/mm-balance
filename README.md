# mm-balance

A multi-cryptocurrency balance checker that allows you to track balances across multiple networks, wallets, and tokens.

## Features

- Support for multiple networks: Bitcoin, Ethereum, Solana, Aptos, Arbitrum, Optimism
- Check balances of native tokens and custom tokens
- Fetch current prices from CoinGecko
- Group addresses for easier management
- Compare balances between two points in time
- Multiple output formats (table and JSON)
- Proxy support

## Installation

### Ubuntu

```shell
sudo apt update && sudo apt-get install build-essential libgmp3-dev python3-dev -y
sudo curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv tool install mm-balance
```

### macOS

```shell
brew install gmp
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc  # or appropriate shell config
uv tool install mm-balance
```

### Windows (via WSL)

```shell
sudo apt update && sudo apt-get install build-essential libgmp3-dev python3-dev -y
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.bashrc
uv tool install mm-balance
```

## Usage

Create a configuration file in TOML format, then run:

```shell
mm-balance your_config.toml
```

### Command Line Options

```
Options:
  -f, --format [TABLE|JSON]     Print format
  -s, --skip-empty              Skip empty balances
  -d, --debug                   Print debug info
  -c, --config                  Print config and exit
  --price / --no-price          Print prices
  --save-balances PATH          Save balances file
  --diff-from-balances PATH     Diff from balances file
  --example                     Print a config example
  --networks                    Print supported networks
  --version                     Show version and exit
  --help                        Show this message and exit
```

## Configuration

Create a TOML file with the following structure:

```toml
[[coins]]
ticker = "BTC"
network = "bitcoin"
addresses = [
  "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
  "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"
]

[[coins]]
ticker = "ETH"
network = "ethereum"
comment = "exchange_wallets"
addresses = "group: exchange_wallets"

[[addresses]]
name = "exchange_wallets"
addresses = [
  "0xf977814e90da44bfa03b6295a0616a897441acec",
  "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503"
]

[settings]
round_ndigits = 4
price = true
skip_empty = false
print_format = "table"  # table, json
```

For a full configuration example, run:

```shell
mm-balance --example
```

## Supported Networks

Current supported networks include:
- bitcoin
- ethereum
- solana
- aptos
- arbitrum-one
- op-mainnet

To see the complete list, run:

```shell
mm-balance --networks
```
