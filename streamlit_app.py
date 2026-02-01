import streamlit as st
import json
import ast
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from main import get_agent

# Page Config
st.set_page_config(page_title="Live Research Agent", page_icon="🤖")
st.title("🤖 Live Research Agent")
st.caption("Powered by Groq & DuckDuckGo")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add system prompt
    system_prompt = (
        "You are a helpful research assistant.\n"
        "You have access to the following tools:\n"
        "1. 'search': DuckDuckGo search for real-time information.\n"
        "2. 'wikipedia': Wikipedia search for encyclopedic knowledge.\n"
        "3. 'calculator': Basic math calculator (e.g., '123 * 45').\n"
        "4. 'weather': Get current weather for any city (e.g., 'Tokyo', 'New York').\n"
        "5. 'youtube': Search YouTube videos (e.g., 'python tutorials').\n"
        "\n"
        "To use a tool, your response MUST be a valid JSON object in this exact format:\n"
        '{"tool": "tool_name", "query": "your query or expression"}\n'
        "\n"
        "Example:\n"
        '{"tool": "calculator", "query": "50 * 20"}\n'
        '{"tool": "weather", "query": "Paris"}\n'
        '{"tool": "youtube", "query": "machine learning basics"}\n'
        "\n"
        "If you already have the information or don't need to search, "
        "just respond with normal text (do not use JSON).\n"
        "Do not wrap the JSON in markdown code blocks. Just output the raw JSON string."
    )
    st.session_state.messages.append(SystemMessage(content=system_prompt))

# Initialize Agent
if "agent_llm" not in st.session_state:
    llm, tools = get_agent()
    if llm:
        st.session_state.agent_llm = llm
        st.session_state.tools = tools
    else:
        st.error("Failed to initialize agent. Check your API Key.")

# Display Chat Messages
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        # Don't show raw tool calls to user, only final answers or "searching" status
        if '{"tool": "search"' not in msg.content:
            with st.chat_message("assistant"):
                st.markdown(msg.content)
    elif isinstance(msg, SystemMessage) and "Search Result:" in msg.content:
        with st.chat_message("assistant"):
            st.markdown(f"*{msg.content}*")

# Chat Input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to history
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process processing
    if "agent_llm" in st.session_state:
        llm = st.session_state.agent_llm

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # First LLM Call
                response = llm.invoke(st.session_state.messages)
                content = response.content.strip()
                
                # Parse for tool call
                tool_call = None
                try:
                    start_index = content.find("{")
                    if start_index != -1:
                        potential_json = content[start_index:]
                        end_index = potential_json.rfind("}")
                        if end_index != -1:
                            json_str = potential_json[:end_index+1]
                            tool_call = json.loads(json_str)
                except:
                    pass
                
                # Fallback parse
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

                if tool_call and "tool" in tool_call:
                    tool_name = tool_call.get("tool")
                    query = tool_call.get("query")
                    
                    status_placeholder = st.empty()
                    status_msg = f"🛠️ Using {tool_name}..."
                    if tool_name == "search":
                        status_msg = f"🔍 Searching for '{query}'..."
                    elif tool_name == "wikipedia":
                        status_msg = f"📚 Reading Wikipedia for '{query}'..."
                    elif tool_name == "calculator":
                        status_msg = f"🧮 Calculating '{query}'..."
                    elif tool_name == "weather":
                        status_msg = f"🌤️ Getting weather for '{query}'..."
                    elif tool_name == "youtube":
                        status_msg = f"📺 Searching YouTube for '{query}'..."
                        
                    status_placeholder.markdown(f"*{status_msg}*")
                    
                    # Log tool request
                    st.session_state.messages.append(AIMessage(content=content))
                    
                    # Execute Tool
                    tools = {
                        "search": st.session_state.tools["search"],
                        "wikipedia": st.session_state.tools["wikipedia"],
                        "calculator": st.session_state.tools["calculator"],
                        "weather": st.session_state.tools["weather"],
                        "youtube": st.session_state.tools["youtube"]
                    }
                    
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
                        result = tools["youtube"](query)
                    
                    # Log tool result
                    st.session_state.messages.append(SystemMessage(content=f"Tool Result: {result}"))
                    
                    # Second LLM Call
                    final_response = llm.invoke(st.session_state.messages)
                    st.session_state.messages.append(final_response)
                    
                    status_placeholder.empty() # Clear status
                    st.markdown(final_response.content)
                    
                else:
                    # Normal response
                    st.session_state.messages.append(response)
                    st.markdown(content)
