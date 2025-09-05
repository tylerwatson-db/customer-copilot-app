"""Query router for customer copilot model serving."""

import time
import re
from datetime import datetime
from typing import Optional, List

import httpx
from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.services.user_service import UserService

router = APIRouter()

# Model serving endpoint name (not the full URL)
MODEL_ENDPOINT_NAME = "agents_team_nasty-customer_copilot-agent_no_mcp"
MODEL_ENDPOINT_URL = "https://fe-vm-team-nasty-hackathon-ws.cloud.databricks.com/serving-endpoints/agents_team_nasty-customer_copilot-agent_no_mcp/invocations"


def extract_tools_used(response_text: str) -> List[str]:
    """Extract tool usage information from agent response."""
    tools_used = []
    
    # Look for common patterns that indicate tool usage in agent responses
    patterns = [
        r"I(?:'ll|'m going to| will| used) (?:use|call|run|execute) (?:the )?(\w+)(?: tool)?",
        r"Using (?:the )?(\w+)(?: tool)?",
        r"I'll (?:use|call) (\w+)",
        r"Let me (?:use|call) (?:the )?(\w+)",
        r"I (?:used|called|ran) (?:the )?(\w+)(?: tool)?",
        r"Called (\w+)(?: tool)?",
        r"Executed (\w+)(?: tool)?",
        r"Running (\w+)(?: tool)?",
        r"Tool used: (\w+)",
        r"Tools? used: ([^.]+)",
        r"I (?:searched|queried|fetched) (?:using|with) (?:the )?(\w+)",
    ]
    
    # Check for specific tool names in the text
    tool_names = [
        "sql", "query", "search", "fetch", "get", "post", "put", "delete",
        "databricks", "workspace", "cluster", "warehouse", "table", "catalog",
        "mlflow", "model", "serving", "endpoint", "vector_search", "embedding",
        "similarity_search", "retrieval", "rag", "knowledge_base"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        for match in matches:
            # Handle cases where match might be a tuple
            tool_name = match if isinstance(match, str) else match[0] if match else ""
            if tool_name and tool_name.lower() not in tools_used:
                tools_used.append(tool_name.lower())
    
    # Also check for explicit tool names mentioned in the text
    for tool_name in tool_names:
        if re.search(rf"\b{tool_name}\b", response_text, re.IGNORECASE):
            if tool_name not in tools_used:
                tools_used.append(tool_name)
    
    # Clean up and deduplicate
    tools_used = list(set([tool.strip() for tool in tools_used if tool.strip()]))
    
    return tools_used


class QueryRequest(BaseModel):
    """Request model for customer copilot queries."""
    query: str


class QueryMetadata(BaseModel):
    """Metadata for query responses."""
    responseTime: float
    timestamp: str
    endpoint: str


class QueryResponse(BaseModel):
    """Response model for customer copilot queries."""
    response: str
    metadata: QueryMetadata
    toolsUsed: List[str] = []
    error: Optional[str] = None


@router.post('/query', response_model=QueryResponse)
async def query_customer_copilot(request: QueryRequest):
    """Query the customer copilot model serving endpoint using Databricks SDK."""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    try:
        # Use Databricks SDK for proper OAuth authentication
        client = WorkspaceClient()
        
        # Prepare payload for model serving endpoint
        payload = {
            "input": [{"role": "user", "content": request.query}]
        }
        
        # Use the SDK's serving endpoints client for OAuth authentication
        # This automatically handles OAuth token generation and refresh
        serving_client = client.serving_endpoints
        
        # Make the request using httpx but with proper OAuth token from SDK
        oauth_token = None
        try:
            # Get OAuth token from the SDK's authentication
            auth_result = client.config.authenticate()
            if isinstance(auth_result, dict) and 'Authorization' in auth_result:
                oauth_token = auth_result['Authorization'].replace('Bearer ', '')
            elif isinstance(auth_result, str):
                oauth_token = auth_result
        except:
            # Fallback to trying the config token
            oauth_token = getattr(client.config, 'token', None)
        
        if not oauth_token:
            raise Exception("Unable to obtain OAuth token for model serving")
        
        # Prepare headers with OAuth token
        headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json"
        }
        
        # Make request to model serving endpoint
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                MODEL_ENDPOINT_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Debug: Log the full response to understand the format
            print(f"DEBUG: Full model response: {response_data}")
            
            # Extract response content (format varies by model)
            ai_response = ""
            if "output" in response_data and len(response_data["output"]) > 0:
                # New format with 'output' array - find the final assistant message
                output_items = response_data["output"]
                # Find the last message with type 'message' and role 'assistant'
                assistant_messages = [
                    item for item in output_items 
                    if item.get("type") == "message" and item.get("role") == "assistant"
                ]
                if assistant_messages:
                    # Get the last assistant message
                    final_message = assistant_messages[-1]
                    if "content" in final_message and len(final_message["content"]) > 0:
                        # Extract text from content array
                        content_items = final_message["content"]
                        text_parts = []
                        for content_item in content_items:
                            if content_item.get("type") == "output_text" and "text" in content_item:
                                text_parts.append(content_item["text"])
                        ai_response = "\n".join(text_parts) if text_parts else str(final_message)
                    else:
                        ai_response = str(final_message)
                else:
                    # Fallback to the last output item
                    ai_response = str(output_items[-1])
            elif "messages" in response_data and len(response_data["messages"]) > 0:
                # Legacy format with 'messages' array
                messages = response_data["messages"]
                assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
                if assistant_messages:
                    final_message = assistant_messages[-1]
                    ai_response = final_message.get("content", str(final_message))
                else:
                    final_message = messages[-1]
                    ai_response = final_message.get("content", str(final_message))
            elif "choices" in response_data and len(response_data["choices"]) > 0:
                # Standard OpenAI-style format
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    ai_response = choice["message"]["content"]
                else:
                    ai_response = str(choice)
            else:
                # Fallback for other response formats
                ai_response = str(response_data)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract tools used from the response
            tools_used = extract_tools_used(ai_response)
            
            return QueryResponse(
                response=ai_response,
                metadata=QueryMetadata(
                    responseTime=response_time,
                    timestamp=timestamp,
                    endpoint=MODEL_ENDPOINT_URL
                ),
                toolsUsed=tools_used
            )
            
    except httpx.HTTPStatusError as e:
        response_time = time.time() - start_time
        error_msg = f"Model endpoint error: {e.response.status_code} - {e.response.text}"
        
        return QueryResponse(
            response="",
            metadata=QueryMetadata(
                responseTime=response_time,
                timestamp=timestamp,
                endpoint=MODEL_ENDPOINT_URL
            ),
            toolsUsed=[],
            error=error_msg
        )
        
    except httpx.TimeoutException:
        response_time = time.time() - start_time
        error_msg = "Request timed out after 30 seconds"
        
        return QueryResponse(
            response="",
            metadata=QueryMetadata(
                responseTime=response_time,
                timestamp=timestamp,
                endpoint=MODEL_ENDPOINT_URL
            ),
            toolsUsed=[],
            error=error_msg
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = f"Authentication or connection error: {str(e)}"
        
        return QueryResponse(
            response="",
            metadata=QueryMetadata(
                responseTime=response_time,
                timestamp=timestamp,
                endpoint=MODEL_ENDPOINT_URL
            ),
            toolsUsed=[],
            error=error_msg
        )