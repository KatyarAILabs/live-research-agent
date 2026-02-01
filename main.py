import os
import sys
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Load environment variables
load_dotenv()

def get_agent():
    """Initializes and returns the agent (LLM + Tools)."""
    # 1. Setup API Key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in .env file.")
        return None, None

    # 2. Initialize LLM
    llm = ChatGroq(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.6
    )

    # 3. Initialize Tools
    search = DuckDuckGoSearchRun()
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    
    # Custom Calculator Tool
    def calculator(expression):
        try:
            return eval(expression)
        except Exception as e:
            return f"Error: {e}"
    
    # Custom Weather Tool
    def weather(city):
        import requests
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "Error: OPENWEATHER_API_KEY not found in .env file. Get one free at https://openweathermap.org/api"
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                return f"Weather in {city}: {description.capitalize()}, Temperature: {temp}°C (feels like {feels_like}°C), Humidity: {humidity}%"
            else:
                return f"Error: {data.get('message', 'Could not fetch weather data')}"
        except Exception as e:
            return f"Error fetching weather: {e}"
    
    # Custom YouTube Search Tool
    def youtube_search(query):
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(f"ytsearch3:{query}", download=False)
                
                if not search_results or 'entries' not in search_results:
                    return f"No YouTube videos found for '{query}'"
                
                videos = search_results['entries']
                output = f"Top YouTube videos for '{query}':\n"
                
                for i, video in enumerate(videos, 1):
                    if video:
                        title = video.get('title', 'Unknown')
                        channel = video.get('uploader', 'Unknown')
                        duration = video.get('duration', 0)
                        view_count = video.get('view_count', 0)
                        url = video.get('url', '')
                        
                        # Format duration
                        duration = int(duration) if duration else 0
                        mins, secs = divmod(duration, 60)
                        duration_str = f"{mins}:{secs:02d}"
                        
                        # Format views
                        if view_count >= 1_000_000:
                            views_str = f"{view_count / 1_000_000:.1f}M"
                        elif view_count >= 1_000:
                            views_str = f"{view_count / 1_000:.1f}K"
                        else:
                            views_str = str(view_count)
                        
                        output += f"\n{i}. {title}\n"
                        output += f"   Channel: {channel} | Duration: {duration_str} | Views: {views_str}\n"
                        output += f"   Link: https://youtube.com/watch?v={video.get('id', '')}\n"
                
                return output
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error searching YouTube: {e}\n\nDetails:\n{error_details}"

    tools = {
        "search": search,
        "wikipedia": wikipedia,
        "calculator": calculator,
        "weather": weather,
        "youtube": youtube_search
    }
    
    return llm, tools

def main():
    print("🤖 Initializing Live Research Agent (Groq Cloud - Multi-Tool Mode)...")
    
    llm, tools = get_agent()
    if not llm:
        return

    print("✅ Agent ready! Type 'exit' to quit.")
    print("-" * 50)

    # 4. Message History with explicit instructions
    system_prompt = (
        "You are a helpful research assistant with access to tools.\n\n"
        "IMPORTANT: When you need to use a tool, respond with ONLY a JSON object, nothing else.\n"
        "When you don't need a tool, respond with normal text.\n\n"
        "Available tools:\n"
        "1. 'search': DuckDuckGo search for real-time information\n"
        "2. 'wikipedia': Wikipedia for encyclopedic knowledge\n"
        "3. 'calculator': Math calculator (e.g., '123 * 45')\n"
        "4. 'weather': Current weather for any city (e.g., 'Tokyo')\n"
        "5. 'youtube': Search YouTube videos (e.g., 'python tutorials')\n\n"
        "Tool usage format (ONLY output this when using a tool):\n"
        '{"tool": "tool_name", "query": "your query"}\n\n'
        "Examples:\n"
        '{"tool": "youtube", "query": "python programming"}\n'
        '{"tool": "weather", "query": "London"}\n'
        '{"tool": "calculator", "query": "50 * 20"}\n\n'
        "Rules:\n"
        "- If you need information you don't have, use a tool\n"
        "- Output ONLY the JSON, no explanation\n"
        "- After getting tool results, answer the user's question normally\n"
        "- Never show the JSON to the user in your final answer"
    )

    messages = [
        SystemMessage(content=system_prompt)
    ]

    # 5. Interaction Loop
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("🤖 Agent is thinking...")
            messages.append(HumanMessage(content=user_input))
            
            # First LLM Call
            response = llm.invoke(messages)
            content = response.content.strip()
            
            # Robust parsing
            tool_call = None
            try:
                start_index = content.find("{")
                if start_index != -1:
                    potential_json = content[start_index:]
                    end_index = potential_json.rfind("}")
                    if end_index != -1:
                        json_str = potential_json[:end_index+1]
                        tool_call = json.loads(json_str)
            except Exception:
                pass

            if not tool_call:
                try:
                    import ast
                    start_index = content.find("{")
                    if start_index != -1:
                        potential_json = content[start_index:]
                        end_index = potential_json.rfind("}")
                        if end_index != -1:
                            dict_str = potential_json[:end_index+1]
                            tool_call = ast.literal_eval(dict_str)
                except:
                    pass
            
            print(f"[DEBUG] Parsed tool_call: {tool_call}")
            
            if tool_call and "tool" in tool_call:
                tool_name = tool_call.get("tool")
                query = tool_call.get("query")
                
                print(f"🛠️  Using tool '{tool_name}' with Input: '{query}'...")
                messages.append(AIMessage(content=content))
                
                result = "Error: Tool not found."
                if tool_name == "search":
                    try:
                        result = tools["search"].invoke(query)
                    except Exception as e:
                        result = f"Error: {e}"
                elif tool_name == "wikipedia":
                    try:
                        result = tools["wikipedia"].invoke(query)
                    except Exception as e:
                        result = f"Error: {e}"
                elif tool_name == "calculator":
                    result = tools["calculator"](query)
                elif tool_name == "weather":
                    result = tools["weather"](query)
                elif tool_name == "youtube":
                    print(f"[DEBUG] Calling YouTube tool with query: {query}")
                    result = tools["youtube"](query)
                    print(f"[DEBUG] YouTube result: {result[:200]}...")  # First 200 chars
                
                # Report result back to LLM
                messages.append(SystemMessage(content=f"Tool Result: {result}"))
                
                # Second LLM Call
                final_response = llm.invoke(messages)
                print(f"\nAgent: {final_response.content}")
                messages.append(final_response)
                
            else:
                # Normal response
                print(f"\nAgent: {content}")
                messages.append(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
