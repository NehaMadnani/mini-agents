from anthropic import Anthropic
import requests
from typing import Dict, Optional, List, Tuple
import json
import time
from datetime import datetime, timezone
import re
from dotenv import load_dotenv
import os

class WeatherAgent:
    def __init__(self):
        # Make sure to load the environment variables
        load_dotenv(override=True)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.weather_api_key = os.getenv("WEATHER_API_KEY")
        self.rate_limit = {
            "limit": 100000,
            "remaining": 100000,
            "reset_at": int(time.time()) + 3600
        }
        
        if not self.weather_api_key or not self.anthropic_api_key:
            raise ValueError("Missing required API keys")
            
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.last_location = None  # Store the last queried location



    def extract_location(self, query: str) -> Optional[Dict[str, str]]:
        """
        Extract location from query with improved handling of time references
        """
        # Clean the query first
        query = query.lower().strip()
        
        # Updated patterns that exclude time references
        patterns = [
            r"weather (?:in|at|for) ([\w\s]+?)(?:\s+(?:today|now|tomorrow))?\??$",
            r"weather ([\w\s]+?)(?:\s+(?:today|now|tomorrow))?\??$",
            r"(?:what's|what is|how's|how is) (?:the )?weather (?:like )?(?:in|at|for) ([\w\s]+?)(?:\s+(?:today|now|tomorrow))?\??$",
            r"temperature (?:in|at|for) ([\w\s]+?)(?:\s+(?:today|now|tomorrow))?\??$"
        ]
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1).strip()
                # Remove any trailing time references if they somehow got included
                location = re.sub(r'\s*(?:today|now|tomorrow)\s*$', '', location)
                return {"city": location}

        # If no pattern matches, try Claude as fallback
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=70,
                system="Extract only the city name from the weather query. Remove any time references. Respond with just the city name, nothing else.",
                messages=[{"role": "user", "content": query}]
            )
            location = message.content[0].text.strip()
            # Clean up the extracted location
            location = re.sub(r'\s*(?:today|now|tomorrow)\s*$', '', location)
            return {"city": location} if location else None
        except Exception as e:
            print(f"Claude API Error in location extraction: {str(e)}")
            return None

    def is_weather_related(self, query: str) -> bool:
        """
        Check if the query is weather-related
        """
        weather_keywords = [
            'weather', 'temperature', 'rain', 'snow', 'wind', 'sunny', 'cloudy',
            'forecast', 'humidity', 'storm', 'climate', 'precipitation', 'cold',
            'hot', 'warm', 'chilly', 'freezing', 'degrees', 'celsius', 'fahrenheit'
        ]
        query_words = query.lower().split()
        return any(keyword in query_words for keyword in weather_keywords)

    def is_weather_query(self, query: str) -> bool:
        """
        Check if the query is asking for weather information
        """
        weather_patterns = [
            r'weather (?:in|at|for)',
            r'(?:what\'s|what is|how\'s|how is) (?:the )?weather',
            r'temperature (?:in|at|for)',
            r'is it (?:raining|snowing|sunny|cloudy)',
            r'will it (?:rain|snow)',
            r'forecast'
        ]
        return any(re.search(pattern, query.lower()) for pattern in weather_patterns)

    def generate_weather_chat_response(self, query: str, weather_data: Dict) -> str:
        """
        Generate a humorous weather-related chat response with location context
        """
        system_prompt = """You are a witty weather agent with a great sense of humor. 
        Generate a funny response to the user's weather-related chat that incorporates 
        both the location and current weather conditions. Keep it light and playful, 
        but informative. Use weather puns and jokes when appropriate. Keep the response concise."""

        location_name = weather_data.get("location", {}).get("city", "your area")
        
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Location: {location_name}\nCurrent weather: {json.dumps(weather_data)}\nUser chat: {query}"
                }]
            )
            return message.content[0].text if hasattr(message.content[0], 'text') else str(message.content)
        except Exception as e:
            return f"Well, {location_name} is keeping me on my toes today... even forecasts have their cloudy moments! 😅"

    def generate_non_weather_response(self, query: str) -> str:
        """
        Generate a concise, single-sentence response for non-weather queries
        """
        system_prompt = """You are a weather agent. When users ask non-weather questions:
        - Respond with EXACTLY ONE short sentence
        - Include a weather-related pun or metaphor
        - Politely redirect to weather topics
        - Keep it under 15 words"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Using Haiku for efficiency
                max_tokens=50,  # Limiting token count
                temperature=0.7,  # Add some variety to responses
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Off-topic question: {query}"
                }]
            )
            return message.content[0].text if hasattr(message.content[0], 'text') else str(message.content)
        except Exception as e:
            # Single-sentence fallbacks
            responses = [
                "Let's forecast a change of topic to the weather instead! ☔",
                "My expertise is as focused as a laser through a rain cloud - weather only! 🌧",
                "Like a weather vane, I only point towards meteorological matters! 🌤",
                "My forecast shows a 100% chance of weather-related conversations ahead! 🌈"
            ]
            return responses[int(time.time()) % len(responses)]

    def estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def get_weather_data(self, location: Dict[str, str]) -> Tuple[Optional[Dict], int, bool]:
        """
        Get weather data with improved error handling
        """
        try:
            city = location.get("city", "").strip()
            if not city:
                return None, 0, True

            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,  # Use cleaned city name
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=10)
            api_response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return response.json(), api_response_time, False
                
            print(f"Weather API Error: Status {response.status_code}, Response: {response.text}")
            return None, api_response_time, True
            
        except Exception as e:
            print(f"Error in get_weather_data: {str(e)}")
            return None, 0, True

    def format_weather_data(self, data: Dict) -> Dict:
        if not data or "error" in data:
            return {"error": "Weather data currently unavailable"}
            
        try:
            temp_c = data['main']['temp']
            temp_f = (temp_c * 9/5) + 32
            humidity = data['main']['humidity']
            description = data['weather'][0]['description']
            wind_speed = data['wind']['speed']
            wind_speed_mph = wind_speed * 2.237
            
            location_info = {
                "city": data.get('name'),
                "country": data.get('sys', {}).get('country'),
                "coordinates": {
                    "lat": data.get('coord', {}).get('lat'),
                    "lon": data.get('coord', {}).get('lon')
                }
            }
            
            return {
                "location": location_info,
                "temperature": {
                    "celsius": round(temp_c, 1),
                    "fahrenheit": round(temp_f, 1),
                    "feels_like_c": round(data['main']['feels_like'], 1),
                    "feels_like_f": round((data['main']['feels_like'] * 9/5) + 32, 1)
                },
                "humidity": humidity,
                "conditions": {
                    "main": data['weather'][0]['main'],
                    "description": description,
                    "icon_code": data['weather'][0]['icon']
                },
                "wind": {
                    "speed_ms": round(wind_speed, 2),
                    "speed_mph": round(wind_speed_mph, 2),
                    "direction_degrees": data.get('wind', {}).get('deg'),
                    "gust_ms": data.get('wind', {}).get('gust')
                },
                "pressure": data['main'].get('pressure'),
                "visibility": data.get('visibility'),
                "timezone": data.get('timezone')
            }
        except KeyError as e:
            print(f"Data formatting error: {str(e)}")
            return {"error": "Error formatting weather data"}

    def update_rate_limit(self) -> Dict:
        self.rate_limit["remaining"] -= 1
        if self.rate_limit["remaining"] <= 0:
            if time.time() >= self.rate_limit["reset_at"]:
                self.rate_limit["remaining"] = self.rate_limit["limit"]
                self.rate_limit["reset_at"] = int(time.time()) + 3600
        return self.rate_limit

    def calculate_confidence_score(self, weather_data: Dict, claude_response, response_time: int) -> float:
        score = 1.0
        factors: List[float] = []
        
        if weather_data and "dt" in weather_data:
            data_age = time.time() - weather_data["dt"]
            freshness_score = max(0, 1 - (data_age / 3600))
            factors.append(freshness_score * 0.4)
        
        required_fields = ['main', 'weather', 'wind']
        if weather_data:
            completeness = sum(1 for field in required_fields if field in weather_data) / len(required_fields)
            factors.append(completeness * 0.4)
        
        response_time_score = max(0, 1 - (response_time / 2000))
        factors.append(response_time_score * 0.2)
        
        return round(sum(factors), 2) if factors else 0.5

    def calculate_token_usage(self, claude_response) -> Dict:
        try:
            return {
                "total_tokens": claude_response.usage.input_tokens + claude_response.usage.output_tokens,
                "input_tokens": claude_response.usage.input_tokens,
                "output_tokens": claude_response.usage.output_tokens,
                "billable_tokens": claude_response.usage.input_tokens + claude_response.usage.output_tokens
            }
        except (AttributeError, TypeError):
            estimated_tokens = self.estimate_tokens(str(claude_response.content))
            return {
                "total_tokens": estimated_tokens,
                "input_tokens": None,
                "output_tokens": None,
                "billable_tokens": estimated_tokens,
                "estimation_method": "word_count_approximation"
            }

    def process_query(self, query: str) -> Dict:
        start_time = time.time()
        
        # Check if it's a weather query or weather-related chat
        is_direct_weather_query = self.is_weather_query(query)
        is_weather_chat = self.is_weather_related(query)
        
        # Handle non-weather queries first
        if not (is_direct_weather_query or is_weather_chat):
            rate_limit = self.update_rate_limit()
            return {
                "meta": {
                    "request_id": f"req_{int(time.time())}_{hash(query) % 10000}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "api_response_time_ms": 0,
                    "version": "1.0.0"
                },
                "rate_limit": {
                    "limit": rate_limit["limit"],
                    "remaining": rate_limit["remaining"],
                    "reset_at": datetime.fromtimestamp(rate_limit["reset_at"], timezone.utc).isoformat()
                },
                "response": {
                    "text": self.generate_non_weather_response(query),
                    "type": "off_topic_response",
                    "confidence_score": 1.0,
                    "data_freshness": "N/A",
                    "fallback_used": False
                },
                "usage": {
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "billable_tokens": 0,
                    "estimation_method": "no_tokens_used"
                },
                "query": {
                    "text": query,
                    "is_weather_related": False,
                    "extracted_location": None
                }
            }
        
        # Get location - either from query or use last known location
        location = self.extract_location(query)
        
        # Use last known location for weather-related chat if no location found
        if not location and self.last_location and is_weather_chat and not is_direct_weather_query:
            location = self.last_location
            print(f"Using cached location: {location}")
        elif location:
            # Cache new location when found
            self.last_location = location
        elif not location and is_direct_weather_query:
            return {"error": "Could not determine location from query"}
        elif not location:
            # If no location found and no cache for chat
            location = {"city": "general"}  # Default for general weather chat
        
        # Get weather data
        weather_data, api_response_time, fallback_used = self.get_weather_data(location)
        formatted_weather = self.format_weather_data(weather_data if weather_data else {})
        
        # Handle weather-related chat (not direct weather queries)
        if is_weather_chat and not is_direct_weather_query:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                system="You are a witty weather chatbot. Be funny and engaging while discussing weather. Reference the location if available.",
                messages=[{
                    "role": "user", 
                    "content": f"The user is talking about {location['city']}. Their message: {query}"
                }]
            )
            
            total_response_time = int((time.time() - start_time) * 1000)
            token_usage = self.calculate_token_usage(message)
            rate_limit = self.update_rate_limit()
            
            return {
                "meta": {
                    "request_id": f"req_{int(time.time())}_{hash(query) % 10000}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": total_response_time,
                    "api_response_time_ms": api_response_time,
                    "version": "1.0.0"
                },
                "rate_limit": rate_limit,
                "weather_data": formatted_weather,
                "response": {
                    "text": self.generate_weather_chat_response(query, formatted_weather),
                    "type": "weather_chat",
                    "confidence_score": 0.8,
                    "data_freshness": "chat response",
                    "fallback_used": fallback_used,
                    "location_context": "cached" if location == self.last_location else "new"
                },
                "usage": token_usage,
                "query": {
                    "text": query,
                    "is_weather_related": True,
                    "extracted_location": location
                }
            }
        
        # For direct weather queries, continue with normal weather report
        message = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            system=f"You are a helpful and friendly weather assistant. Provide your response as plain text.",
            messages=[{
                "role": "user",
                "content": f"Current weather data: {json.dumps(formatted_weather)} User query: {query}"
            }]
        )
        
        total_response_time = int((time.time() - start_time) * 1000)
        data_freshness = int(time.time() - weather_data["dt"]) if weather_data and "dt" in weather_data else None
        confidence_score = self.calculate_confidence_score(weather_data, message, total_response_time)
        token_usage = self.calculate_token_usage(message)
        rate_limit = self.update_rate_limit()
        
        response_text = message.content[0].text if hasattr(message.content[0], 'text') else str(message.content)
        
        return {
            "meta": {
                "request_id": f"req_{int(time.time())}_{hash(query) % 10000}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": total_response_time,
                "api_response_time_ms": api_response_time,
                "version": "1.0.0"
            },
            "rate_limit": {
                "limit": rate_limit["limit"],
                "remaining": rate_limit["remaining"],
                "reset_at": datetime.fromtimestamp(rate_limit["reset_at"], timezone.utc).isoformat()
            },
            "weather_data": formatted_weather,
            "response": {
                "text": response_text,
                "type": "weather_report",
                "confidence_score": confidence_score,
                "data_freshness": f"{data_freshness} seconds ago" if data_freshness else "unknown",
                "fallback_used": fallback_used
            },
            "usage": token_usage,
            "query": {
                "text": query,
                "extracted_location": location
            }
        }
