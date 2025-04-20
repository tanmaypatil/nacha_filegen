import json
import os
import requests
from typing import Dict, List, Any, Optional, Union

class Agent:
    def __init__(self, api_key: str):
        """
        Initialize the agent with API key and state.
        
        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key
        self.state = {
            "memory": [],  # Long-term memory for the agent
            "goals": [],   # Current goals the agent is pursuing
            "tools_used": {},  # Track tool usage statistics
            "user_preferences": {}  # Store user preferences
        }
        self.model = "claude-3-7-sonnet-20250219"  # Using the latest model
        self.api_url = "https://api.anthropic.com/v1/messages"
        
    def add_to_memory(self, item: Dict[str, Any]):
        """Add an important item to agent's memory."""
        self.state["memory"].append(item)
        # Prune memory if it gets too large
        if len(self.state["memory"]) > 20:
            self.state["memory"] = self.state["memory"][-20:]
    
    def set_goal(self, goal: str):
        """Set a new goal for the agent."""
        self.state["goals"].append(goal)
    
    def clear_goals(self):
        """Clear all current goals."""
        self.state["goals"] = []
    
    def record_tool_use(self, tool_name: str):
        """Record the use of a tool for analytics."""
        if tool_name in self.state["tools_used"]:
            self.state["tools_used"][tool_name] += 1
        else:
            self.state["tools_used"][tool_name] = 1
    
    def create_web_search_tool(self) -> Dict[str, Any]:
        """Create a web search tool definition."""
        return {
            "name": "web_search",
            "description": "Search the web for information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    
    def create_database_query_tool(self) -> Dict[str, Any]:
        """Create a database query tool definition."""
        return {
            "name": "database_query",
            "description": "Query a database for information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    },
                    "database": {
                        "type": "string",
                        "description": "The database to query"
                    }
                },
                "required": ["query", "database"]
            }
        }
    
    def execute_tool(self, tool_name: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool based on its name and parameters.
        
        Args:
            tool_name: Name of the tool to execute
            tool_params: Parameters for the tool
            
        Returns:
            Tool execution results
        """
        self.record_tool_use(tool_name)
        
        # Mock implementations - in a real system these would call actual APIs
        if tool_name == "web_search":
            # Mock web search
            return {
                "status": "success",
                "results": [
                    {"title": "Mock search result 1", "snippet": "This is a mock search result."},
                    {"title": "Mock search result 2", "snippet": "Another mock search result."}
                ]
            }
        
        elif tool_name == "database_query":
            # Mock database query
            return {
                "status": "success",
                "rows": [
                    {"id": 1, "name": "Mock data 1"},
                    {"id": 2, "name": "Mock data 2"}
                ]
            }
        
        else:
            return {
                "status": "error",
                "message": f"Unknown tool: {tool_name}"
            }
    
    def build_mcp_request(self, user_input: str) -> Dict[str, Any]:
        """
        Build an MCP request with the current state.
        
        Args:
            user_input: The current user's input
            
        Returns:
            Complete MCP request structure
        """
        # Define available tools
        tools = [
            self.create_web_search_tool(),
            self.create_database_query_tool()
        ]
        
        # Create resources (documents to be included in context)
        resources = []
        
        # If we have memory items, include them as a resource
        if self.state["memory"]:
            memory_resource = {
                "type": "text",
                "id": "agent_memory",
                "content": json.dumps(self.state["memory"], indent=2)
            }
            resources.append(memory_resource)
        
        # Create prompt structure
        system_prompt = f"""
        You are an autonomous agent that helps users accomplish their goals.
        Current agent state:
        - Goals: {', '.join(self.state['goals']) if self.state['goals'] else 'No specific goals set'}
        - User preferences: {json.dumps(self.state['user_preferences'])}
        
        Make decisions based on the user's input and current state.
        Use the available tools when necessary to accomplish tasks.
        Respond directly to the user in a helpful, concise manner.
        """
        
        prompts = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
        
        # Assemble the full MCP request
        mcp_request = {
            "model": self.model,
            "resources": resources,
            "prompts": prompts,
            "tools": tools,
            "max_tokens": 1024
        }
        
        return mcp_request
    
    def handle_tool_calls(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process any tool calls in the response.
        
        Args:
            response: The model's response
            
        Returns:
            Updated response with tool results
        """
        # Check if the response contains tool calls
        if "tool_calls" in response and response["tool_calls"]:
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                tool_params = tool_call["parameters"]
                
                # Execute the tool
                tool_result = self.execute_tool(tool_name, tool_params)
                
                # Add result to the response
                if "tool_results" not in response:
                    response["tool_results"] = []
                
                response["tool_results"].append({
                    "call_id": tool_call["id"],
                    "result": tool_result
                })
                
                # Save important tool results to memory
                self.add_to_memory({
                    "type": "tool_result",
                    "tool": tool_name,
                    "params": tool_params,
                    "result": tool_result
                })
                
        return response
    
    def process_user_input(self, user_input: str) -> str:
        """
        Process user input and return agent response.
        
        Args:
            user_input: The user's input text
            
        Returns:
            Agent's response
        """
        # Check for explicit goal setting
        if user_input.lower().startswith("goal:"):
            goal = user_input[5:].strip()
            self.set_goal(goal)
            return f"I've set your goal: {goal}"
        
        # Build MCP request
        mcp_request = self.build_mcp_request(user_input)
        
        # Call Claude API (mock implementation)
        # In a real implementation, this would make an actual API call
        response = self.mock_claude_api_call(mcp_request)
        
        # Process any tool calls
        response = self.handle_tool_calls(response)
        
        # Extract final text response
        final_response = response.get("content", [{"text": "I couldn't process your request."}])[0]["text"]
        
        # Add important interaction to memory
        self.add_to_memory({
            "type": "interaction",
            "user_input": user_input,
            "agent_response": final_response
        })
        
        return final_response
    
    def mock_claude_api_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock implementation of Claude API call.
        In production, this would call the actual Anthropic API.
        
        Args:
            request: The MCP request
            
        Returns:
            Mock response from Claude
        """
        # This is a simplified mock implementation
        # A real implementation would call the actual API
        user_input = ""
        for prompt in request["prompts"]:
            if prompt["role"] == "user":
                user_input = prompt["content"]
                break
        
        # Simple response logic based on user input
        if "search" in user_input.lower():
            return {
                "id": "msg_mockid12345",
                "type": "message",
                "role": "assistant",
                "model": self.model,
                "content": [{"text": "I'll search for that information."}],
                "tool_calls": [
                    {
                        "id": "call_mock123",
                        "name": "web_search",
                        "parameters": {"query": user_input}
                    }
                ]
            }
        elif "database" in user_input.lower():
            return {
                "id": "msg_mockid12346",
                "type": "message",
                "role": "assistant",
                "model": self.model,
                "content": [{"text": "Let me query the database for you."}],
                "tool_calls": [
                    {
                        "id": "call_mock124",
                        "name": "database_query",
                        "parameters": {"query": "SELECT * FROM mock_table LIMIT 2", "database": "mock_db"}
                    }
                ]
            }
        else:
            return {
                "id": "msg_mockid12347",
                "type": "message",
                "role": "assistant",
                "model": self.model,
                "content": [{"text": f"I understand you're asking about: {user_input}. How can I help you with this?"}]
            }
    
    def real_claude_api_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a real API call to Claude using the Anthropic API.
        
        Args:
            request: The MCP request
            
        Returns:
            Response from Claude API
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=request
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")


# Example usage
def main():
    # In a real application, you'd use an actual API key
    agent = Agent(api_key="YOUR_ANTHROPIC_API_KEY")
    
    # Set initial user preferences and goals
    agent.state["user_preferences"] = {
        "response_style": "concise",
        "technical_level": "expert"
    }
    
    agent.set_goal("Help the user find information efficiently")
    
    # Example interaction
    print("Agent initialized. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
            
        response = agent.process_user_input(user_input)
        print(f"\nAgent: {response}")
        
        # For debugging
        # print(f"\nCurrent state: {json.dumps(agent.state, indent=2)}")


if __name__ == "__main__":
    main()