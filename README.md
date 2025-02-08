# Hedging Quantification

A high-performance cryptocurrency exchange monitoring system that supports real-time price tracking across multiple exchanges.

[中文文档](README_CN.md)

## Features

- **Multi-Exchange Support**: Simultaneously monitor multiple cryptocurrency exchanges
- **Real-time Price Monitoring**: WebSocket-based real-time price updates
- **Market Type Support**: Support for spot, futures, and margin markets
- **High Precision**: Advanced price precision handling following CCXT standards
- **Market Parameters**: Comprehensive market information including:
  - Minimum purchase amount
  - Leverage range
  - Trading fees (maker/taker)
  - Price and amount precision
- **Error Handling**: Robust error handling and automatic reconnection
- **Cross-Platform**: Optimized for both Windows and Linux systems

## Requirements

- Python 3.8+
- ccxt
- ccxt.pro
- asyncio

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/Hedging_quantification.git
cd Hedging_quantification
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit `Config/exchange_config.py` to configure:

- Exchanges to monitor
- Market types (spot/futures/margin)
- Quote currencies
- Market structure settings

Example configuration:

```python
EXCHANGES = ['binance', 'bybit', 'okx']
MARKET_TYPES = {
    'spot': True,
    'future': True,
    'margin': False
}
QUOTE_CURRENCIES = ['USDT', 'BTC']
```

## Usage

Run the main program:

```bash
python main.py
```

The program will:

1. Initialize exchange connections
2. Find common trading pairs
3. Start real-time price monitoring
4. Output formatted JSON price data

Example output:

```json
{
  "exchange": "binance",
  "type": "spot",
  "symbol": "BTC/USDT",
  "quote": "USDT",
  "price": "45123.45",
  "min_cost": "5.0",
  "leverage": "1-100",
  "fees": {
    "taker": "0.001",
    "maker": "0.001"
  },
  "precision": {
    "price": 2,
    "amount": 6
  }
}
```

## Architecture

- `main.py`: Main program entry point
- `ExchangeModules/`:
  - `exchange_instance.py`: Exchange connection management
  - `monitor_manager.py`: Price monitoring system
  - `market_processor.py`: Market data processing
  - `common_symbols_finder.py`: Common trading pair detection
  - `market_structure_fetcher.py`: Market structure handling

## Performance Optimization

- Automatic event loop optimization:
  - Linux: Uses `uvloop` for maximum performance
  - Windows: Uses `WindowsSelectorEventLoopPolicy`
- Efficient WebSocket connections
- Optimized data structures for quick lookups

## Error Handling

- Comprehensive error detection
- Automatic reconnection mechanism
- Detailed error reporting
- Data validation checks

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
