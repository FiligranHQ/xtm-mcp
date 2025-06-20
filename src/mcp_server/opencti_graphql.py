import functools
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from logging import INFO, basicConfig, getLogger
from typing import Any, Dict, Optional
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from mcp import types as mcp_types
from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = getLogger(__name__)

# Constants from environment variables with fallbacks
GRAPHQL_URL = os.getenv("OPENCTI_URL" )
HEADERS = {"Authorization": f"Bearer {os.getenv('OPENCTI_TOKEN')}"}


class ServerContext:
    """Context for the MCP server."""
    def __init__(self, client: Client):
        self.client = client

@asynccontextmanager
async def server_lifespan(server: Server[ServerContext], api_url: str, auth_headers: dict[str, str]) -> AsyncIterator[ServerContext]:
    """Manage server startup and shutdown lifecycle."""
    transport = AIOHTTPTransport(url=api_url, headers=auth_headers)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    
    try:
        context = ServerContext(client)
        yield context
    finally:
        try:
            await client.close_async()
        except:
            pass

async def list_tools_impl(_server: Server[ServerContext]) -> list[Tool]:
    """List available GraphQL tools."""
    return [
        Tool(
            name="list_graphql_types",
            description="Fetch and return the list of all GraphQL types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_types_definitions",
            description="Fetch and return the definition of one or more GraphQL types",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_name": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        ],
                        "description": "Name(s) of the GraphQL type(s) to fetch. Can be a single string or an array of strings."
                    }
                },
                "required": ["type_name"]
            }
        ),
        Tool(
            name="execute_graphql_query",
            description="Execute a GraphQL query and return the result",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "GraphQL query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_stix_relationships_mapping",
            description="Get all possible STIX relationships between types and their available relationship types",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_name": {
                        "type": "string",
                        "description": "Optional: Filter relationships for a specific type (e.g., 'Malware')"
                    }
                }
            }
        )
    ]

async def handle_list_graphql_types(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle list_graphql_types tool."""
    logger.info("Executing list_graphql_types")
    
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            types {
                name
            }
        }
    }
    """
    
    result = await session.execute(gql(introspection_query))
    types = [t["name"] for t in result["__schema"]["types"]]
    
    return [mcp_types.TextContent(type="text", text=json.dumps(types, indent=2))]

async def handle_get_types_definitions(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle get_types_definitions tool."""
    logger.info("Executing get_types_definitions")
    
    type_names = arguments.get("type_name")
    if not type_names:
        return [mcp_types.TextContent(type="text", text="Error: type_name is required")]
    
    if isinstance(type_names, str):
        type_names = [type_names]
    
    if not isinstance(type_names, list):
        return [mcp_types.TextContent(type="text", text="Error: type_name must be a string or array of strings")]
    
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            types {
                name
                kind
                description
                fields {
                    name
                    description
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    result = await session.execute(gql(introspection_query))
    all_types = result["__schema"]["types"]
    
    type_definitions = {}
    for type_name in type_names:
        type_def = next((t for t in all_types if t["name"] == type_name), None)
        if type_def:
            type_definitions[type_name] = type_def
        else:
            type_definitions[type_name] = {"error": f"Type '{type_name}' not found in schema"}
    
    return [mcp_types.TextContent(type="text", text=json.dumps(type_definitions, indent=2))]

async def handle_execute_graphql_query(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle execute_graphql_query tool."""
    logger.info("Executing execute_graphql_query")
    
    if not isinstance(arguments, dict):
        return [mcp_types.TextContent(type="text", text=f"Error: arguments must be a dictionary, got {type(arguments)}")]
    
    query_string = arguments.get("query")
    
    if not query_string:
        return [mcp_types.TextContent(type="text", text="Error: query parameter is missing or empty")]
    
    try:
        logger.info(f"🚀 Executing GraphQL query: {query_string[:100]}...")
        
        # Auto-add "query" keyword if missing
        if not query_string.strip().startswith("query"):
            query_string = f"query {query_string}"
        
        result = await session.execute(gql(query_string))
        success_response = {
            "success": True,
            "data": result
        }
        return [mcp_types.TextContent(type="text", text=json.dumps(success_response, indent=2))]
        
    except Exception as e:
        logger.error(f"❌ GraphQL execution error: {str(e)}")
        error_response = {
            "success": False,
            "error": str(e)
        }
        return [mcp_types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

async def handle_get_stix_relationships_mapping(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle get_stix_relationships_mapping tool.
    
    Args:
        session: The GraphQL client session
        arguments: Dictionary containing:
            - type_name: Optional filter for a specific type
            - include_examples: Whether to include GraphQL query examples
        
    Returns:
        List of TextContent containing the relationships mapping or entity types list
    """
    logger.info("Executing get_stix_relationships_mapping")
    
    # Query to get all relationships mapping
    mapping_query = """
    query StixRelationshipsMapping {
      schemaRelationsTypesMapping {
        key
        values
      }
    }
    """
    
    try:
        result = await session.execute(gql(mapping_query))
        mappings = result.get("schemaRelationsTypesMapping", [])
        
        # Get parameters
        type_name = arguments.get("type_name")

        # Original functionality for full mapping
        processed_mappings = {}
        processed_entity_types = []
        for mapping in mappings:
            key = mapping["key"]

                
            # Split the key into source and target types
            source_type, target_type = key.split("_")
            if source_type == type_name:
                processed_entity_types.append(target_type)
            elif target_type == type_name:
                processed_entity_types.append(source_type)
            
        processed_entity_types = [source for source in processed_entity_types if source != type_name]
        response = {
            "relationships_mapping": processed_entity_types,
            "filtered_type": type_name
        }
        
        return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting STIX relationships mapping: {str(e)}")
        return [mcp_types.TextContent(
            type="text", 
            text=f"Error getting STIX relationships mapping: {str(e)}"
        )]

async def call_tool_impl(_server: Server[ServerContext], name: str, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Execute a GraphQL tool using the appropriate handler function."""
    try:
        ctx = _server.request_context
        client = ctx.lifespan_context.client
        
        async with client as session:
            tool_handlers = {
                "list_graphql_types": handle_list_graphql_types,
                "get_types_definitions": handle_get_types_definitions,
                "execute_graphql_query": handle_execute_graphql_query,
                "get_stix_relationships_mapping": handle_get_stix_relationships_mapping
            }
            
            if name not in tool_handlers:
                return [mcp_types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
            handler = tool_handlers[name]
            return await handler(session, arguments)
        
    except Exception as e:
        logger.error(f"Error in call_tool_impl for tool '{name}': {str(e)}")
        return [mcp_types.TextContent(type="text", text=f"Error: {str(e)}")]

async def serve(api_url: str = GRAPHQL_URL, auth_headers: dict[str, str] | None = None) -> None:
    """Start the MCP server."""
    server = Server[ServerContext](
        "graphql-tools-mcp",
        lifespan=partial(server_lifespan, api_url=api_url, auth_headers=auth_headers or HEADERS),
    )
    
    server.list_tools()(functools.partial(list_tools_impl, server))
    server.call_tool()(functools.partial(call_tool_impl, server))
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="graphql-tools-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())