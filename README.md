# Weather and Language Service

A combined service that provides weather information and language processing capabilities through a Flask API. The service consists of two main components: a Weather Agent for retrieving and formatting weather data, and a Language Agent for natural language processing tasks.

## Features

- **Weather Service**
  - Real-time weather data retrieval
  - Location extraction from natural language queries
  - Weather-related chat responses
  - Support for both direct weather queries and casual weather chat

- **Language Service**
  - Multi-language support
  - Natural language processing
  - Token usage tracking
  - Rate limiting

## Prerequisites

- Python 3.7+
- Node.js
- OpenWeatherMap API key
- Anthropic API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

4. Create a `.env` file in the root directory:
```env
WEATHER_API_KEY=your_openweathermap_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Configuration

The service uses several environment variables for configuration:

- `WEATHER_API_KEY`: Your OpenWeatherMap API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `API_KEY`: API key for accessing the service endpoints (default: "neha-2024")

## API Endpoints

### Weather Service

#### POST /weather/query
Query weather information or engage in weather-related chat.

Request:
```json
{
  "query": "What's the weather like in London?"
}
```

Headers:
```
X-API-Key: your-api-key
```

### Language Service

#### POST /language/query
Process text in different languages.

Request:
```json
{
  "user_input": "Translate this to French",
  "language": "fr"
}
```

## Rate Limiting

Both services include rate limiting:
- Default limit: 100,000 requests per hour
- Remaining requests and reset time included in responses

## Response Format

### Weather Response
```json
{
  "meta": {
    "request_id": "string",
    "timestamp": "ISO datetime",
    "response_time_ms": "number",
    "version": "string"
  },
  "weather_data": {
    "location": {},
    "temperature": {},
    "conditions": {},
    "wind": {}
  },
  "response": {
    "text": "string",
    "type": "string",
    "confidence_score": "number"
  }
}
```

### Language Response
```json
{
  "meta": {
    "request_id": "string",
    "timestamp": "ISO datetime",
    "response_time_ms": "number"
  },
  "response": {
    "text": "string",
    "type": "string",
    "language": "string"
  }
}
```

## Development

The service is built using:
- Flask for the API server
- Anthropic's Claude API for natural language processing
- OpenWeatherMap API for weather data

### Project Structure
```
├── combined_agent.py    # Main Flask application
├── weather_agent.py     # Weather service implementation
├── language_agent.py    # Language service implementation
├── package.json        # Node.js dependencies
```

## Security Notes

- API keys should be stored in environment variables, not in code
- Rate limiting is implemented to prevent abuse
- API key authentication is required for weather endpoints

## Running the Service

Start the Flask server:
```bash
python combined_agent.py
```

The service will be available at `http://localhost:8000`

## Error Handling

The service includes comprehensive error handling for:
- Invalid API keys
- Missing query parameters
- Rate limit exceeded
- External API failures
- Invalid locations
- Malformed requests

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
