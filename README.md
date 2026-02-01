# Live Research Agent

A powerful AI research assistant with 5 integrated tools, powered by Groq Cloud and LangChain.

## Features

- 🔍 **DuckDuckGo Search** - Real-time web search
- 📚 **Wikipedia** - Encyclopedia knowledge
- 🧮 **Calculator** - Math operations
- 🌤️ **Weather** - Current weather (OpenWeatherMap API)
- 📺 **YouTube** - Video search

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd live_research_agent
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   
   Create a `.env` file in the project root:
   ```bash
   # Required
   GROQ_API_KEY=your_groq_api_key_here
   
   # Optional (for weather tool)
   OPENWEATHER_API_KEY=your_openweather_api_key_here
   ```

   Get your API keys:
   - Groq: https://console.groq.com/keys
   - OpenWeatherMap (free): https://openweathermap.org/api

## Usage

### Terminal Interface
```bash
python main.py
```

### Web Interface (Streamlit)
```bash
python -m streamlit run streamlit_app.py
```

Then open http://localhost:8501 in your browser.

## Example Queries

- "What's the latest news about SpaceX?"
- "Who is Albert Einstein?"
- "What is 999 * 888?"
- "What's the weather in Tokyo?"
- "Find videos about Python programming"

## Tech Stack

- **LLM**: Groq Cloud (Llama 3.3)
- **Framework**: LangChain
- **Frontend**: Streamlit
- **Tools**: DuckDuckGo, Wikipedia, yt-dlp, OpenWeatherMap

## License

MIT
