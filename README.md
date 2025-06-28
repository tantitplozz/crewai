# 🤖 Automated Purchase System - God-Tier AI Developer

A full-stack automated purchasing system built with CrewAI, Playwright, GoLogin, and real-time monitoring capabilities. Features human-like behavior mimicking, fingerprint evasion, and comprehensive logging.

## 🚀 Features

- **🎭 Human-Like Automation**: Advanced behavior mimicking with random delays, typos, and natural mouse movements
- **🔒 Anti-Detection**: Built-in stealth mode with fingerprint evasion and WebDriver detection bypass
- **👥 Multi-Profile Support**: Integration with GoLogin for browser profile management
- **💳 Smart Payment Processing**: Automated form filling with support for various payment gateways
- **📊 Real-Time Monitoring**: WebSocket-based live updates and comprehensive logging
- **📱 Telegram Notifications**: Instant alerts for order status and errors
- **🗄️ MongoDB Integration**: Persistent storage for session replay and analytics
- **🐳 Docker Ready**: Fully containerized with docker-compose

## 📋 Requirements

- Python 3.11+
- Docker & Docker Compose
- GoLogin Account (for profile management)
- MongoDB (optional, for persistent logging)
- Telegram Bot Token (optional, for notifications)

## 🛠️ Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/tantitplozz/crewai.git
cd crewai
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Copy environment template:
```bash
cp env.template .env
```

5. Configure your `.env` file with required credentials

### Docker Installation

1. Build and run with docker-compose:
```bash
cd docker
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOLOGIN_TOKEN` | GoLogin API token | Required |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `TELEGRAM_TOKEN` | Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications | Optional |
| `HEADLESS` | Run browser in headless mode | `false` |
| `WEBSOCKET_ENABLED` | Enable WebSocket server | `true` |

### Order Configuration

Create order JSON files in the `orders/` directory:

```json
{
  "name": "Sample Order",
  "target_site": "https://example-shop.com",
  "products": [
    {
      "name": "Product Name",
      "url": "https://example-shop.com/product",
      "quantity": 1,
      "options": {
        "size": "M",
        "color": "Black"
      }
    }
  ],
  "payment_info": {
    "card_number": "4111111111111111",
    "expiry": "12/25",
    "cvv": "123",
    "cardholder_name": "John Doe"
  },
  "billing": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "US"
  }
}
```

## 📖 Usage

### Interactive Mode

```bash
python src/main.py --interactive
```

### Single Order Execution

```bash
python src/main.py --order orders/sample_order.json
```

### Batch Processing

```bash
python src/main.py --batch orders/
```

### API Mode

```bash
# Start API server
python src/api.py

# Submit order via API
curl -X POST http://localhost:7777/api/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d @orders/sample_order.json
```

## 🌐 Web UI

Access the real-time dashboard at `http://localhost:3000`

Features:
- Live session monitoring
- Action replay
- Screenshot gallery
- Performance metrics
- Error logs

## 📊 Monitoring & Logging

### Log Files
- `logs/automation_YYYYMMDD.log` - Daily logs
- `logs/errors.log` - Error-only logs
- `logs/sessions/` - Individual session data

### MongoDB Collections
- `sessions` - Complete session data
- `actions` - Individual action logs
- `logs` - General application logs

### WebSocket Events
- `status` - Session status updates
- `action` - Individual action notifications
- `progress` - Progress indicators
- `screenshot` - Screenshot notifications
- `error` - Error alerts

## 🔍 Session Replay

To replay a session:

```python
from src.replay import SessionReplay

replay = SessionReplay()
await replay.load_session("session_id")
await replay.execute()
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/
```

### Test Payment Profiles
```bash
python src/main.py --interactive
# Select option 5
```

### Generate Test Orders
```bash
python scripts/generate_test_orders.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Chrome not found**
   ```bash
   # Install Chrome manually
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   sudo apt-get update
   sudo apt-get install google-chrome-stable
   ```

2. **WebSocket connection failed**
   - Check if port 8000 is available
   - Verify WebSocket server is running

3. **MongoDB connection error**
   - Ensure MongoDB is running
   - Check connection string in `.env`

4. **GoLogin authentication failed**
   - Verify API token is correct
   - Check GoLogin service status

## 📈 Performance Optimization

- Use `HEADLESS=true` for better performance
- Enable MongoDB indexing for faster queries
- Adjust `MAX_CONCURRENT_SESSIONS` based on system resources
- Use Redis for caching frequent operations

## 🔐 Security Considerations

- Never commit `.env` files
- Rotate API keys regularly
- Use VPN/Proxy for additional anonymity
- Enable 2FA on GoLogin account
- Restrict MongoDB access

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Users are responsible for complying with all applicable laws and website terms of service. The developers assume no liability for misuse of this software.

## 🙏 Acknowledgments

- CrewAI for the multi-agent framework
- Playwright for browser automation
- GoLogin for profile management
- The open-source community

---

Built with ❤️ by God-Tier AI Developer
