import functools
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from logging import INFO, basicConfig, getLogger
from typing import Any
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
            name="validate_graphql_query",
            description="Validate a GraphQL query without returning its result. Returns only success status or error message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "GraphQL query to validate"
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
        ),
        Tool(
            name="get_query_fields",
            description="Get all field names from the GraphQL Query type to identify correct entity field names",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_entity_names",
            description="Get all unique entity names from STIX relationships mapping by splitting relationship keys",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_entities_by_name",
            description="Search for entities by name and intersect with available entity types",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Name of the entity to search for"
                    }
                },
                "required": ["entity_name"]
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
    """Handle get_type_definition tool."""
    logger.info("Executing get_type_definition")
    type_names = arguments.get("type_name")
    if not type_names:
        return [mcp_types.TextContent(type="text", text="Error: type_name is required")]
    
    # NEW: Check if it's a JSON string and parse it
    if isinstance(type_names, str):
        try:
            # Try to parse as JSON array first
            parsed = json.loads(type_names)
            if isinstance(parsed, list):
                type_names = parsed
            else:
                type_names = [type_names]  # Single string value
        except json.JSONDecodeError:
            # Not JSON, treat as single string
            type_names = [type_names]
    
    if not isinstance(type_names, list):
        return [mcp_types.TextContent(type="text", text="Error: type_name must be a string or array of strings")]
    
    introspection_query = """
    query IntrospectionQuery {
    __schema {
        types {
        name
        kind
        fields {
            name
            type {
            kind
            ofType {
                name
                kind
            }
            }
        }
        }
    }
    }
    """
    result = await session.execute(gql(introspection_query))
    all_types = result["__schema"]["types"]
    
    simplified_output = []
    
    for type_name in type_names:
        type_def = next((t for t in all_types if t["name"] == type_name), None)
        if type_def and type_def.get("fields"):
            # Extract field names and their type information
            fields_info = []
            for field in type_def["fields"]:
                field_type = field["type"]
                # Handle nested types (like NON_NULL, LIST)
                while field_type.get("ofType"):
                    field_type = field_type["ofType"]
                
                fields_info.append({
                    "name": field["name"],
                    "type": field_type.get("name"),
                    "kind": field_type.get("kind")
                })
            simplified_output.append({type_name: fields_info})
        else:
            simplified_output.append({type_name: []})
    
    return [mcp_types.TextContent(type="text", text=json.dumps(simplified_output, indent=2))]

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

async def handle_validate_graphql_query(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle validate_graphql_query tool."""
    logger.info("Executing validate_graphql_query")
    
    if not isinstance(arguments, dict):
        return [mcp_types.TextContent(type="text", text=f"Error: arguments must be a dictionary, got {type(arguments)}")]
    
    query_string = arguments.get("query")
    
    if not query_string:
        return [mcp_types.TextContent(type="text", text="Error: query parameter is missing or empty")]
    
    try:
        logger.info(f"🚀 Validating GraphQL query: {query_string[:100]}...")
        
        # Auto-add "query" keyword if missing
        if not query_string.strip().startswith("query"):
            query_string = f"query {query_string}"
        
        # Attempt to execute the query to validate its structure
        await session.execute(gql(query_string))
        
        success_response = {
            "success": True,
            "error": ""
        }
        return [mcp_types.TextContent(type="text", text=json.dumps(success_response, indent=2))]
        
    except Exception as e:
        logger.error(f"❌ GraphQL validation error: {str(e)}")
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

async def handle_get_query_fields(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle get_query_fields tool.
    
    Extracts all field names from the GraphQL Query type to help identify
    the correct field names for entity queries.
    
    Args:
        session: The GraphQL client session
        arguments: Dictionary containing no parameters
        
    Returns:
        List of TextContent containing the field names from the Query type
    """
    logger.info("Executing get_query_fields")
    
    query = """
    query {
      __type(name: "Query") {
        fields(includeDeprecated: false) {
          name
          args {
            name
            type {
              name
              ofType {
                name
              }
            }
          }
        }
      }
    }
    """
    
    try:
        result = await session.execute(gql(query))
        query_type = result.get("__type")
        
        if not query_type or not query_type.get("fields"):
            return [mcp_types.TextContent(type="text", text="Error: Query type not found or has no fields")]
        
        # Extract field names and their arguments from the Query type
        fields_info = []
        for field in query_type["fields"]:
            field_info = {
                "name": field["name"],
                "args": []
            }
            
            # Extract argument information
            for arg in field.get("args", []):
                arg_type = arg["type"]
                # Handle nested types (like NON_NULL, LIST)
                while arg_type.get("ofType"):
                    arg_type = arg_type["ofType"]
                
                field_info["args"].append({
                    "name": arg["name"],
                    "type": arg_type.get("name")
                })
            
            fields_info.append(field_info)
        
        # Sort alphabetically by field name for easier reading
        fields_info.sort(key=lambda x: x["name"])
        
        response = {
            "query_fields": fields_info
        }
        
        return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting Query fields: {str(e)}")
        return [mcp_types.TextContent(
            type="text", 
            text=f"Error getting Query fields: {str(e)}"
        )]

async def handle_get_entity_names(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle get_entity_names tool.
    
    Extracts all unique entity names from the STIX relationships mapping
    by splitting the relationship keys on the underscore character.
    
    Args:
        session: The GraphQL client session
        arguments: Dictionary containing no parameters
        
    Returns:
        List of TextContent containing all unique entity names
    """
    logger.info("Executing get_entity_names")
    
    query = """
    query StixRelationshipsMapping {
      schemaRelationsTypesMapping {
        key
      }
    }
    """
    
    try:
        result = await session.execute(gql(query))
        mappings = result.get("schemaRelationsTypesMapping", [])
        
        # Extract all unique entity names by splitting keys
        entity_names = set()
        for mapping in mappings:
            key = mapping["key"]
            # Split by underscore to get from and to entity names
            if "_" in key:
                from_entity, to_entity = key.split("_", 1)
                entity_names.add(from_entity)
                entity_names.add(to_entity)
        
        # Convert to sorted list for consistent output
        entity_names_list = sorted(list(entity_names))
        
        response = {
            "entity_names": entity_names_list,
            "count": len(entity_names_list)
        }
        
        return [mcp_types.TextContent(type="text", text=json.dumps(response, indent=2))]
        
    except Exception as e:
        logger.error(f"Error getting entity names: {str(e)}")
        return [mcp_types.TextContent(
            type="text", 
            text=f"Error getting entity names: {str(e)}"
        )]

async def handle_search_entities_by_name(session, arguments: dict[str, Any]) -> list[mcp_types.TextContent]:
    """Handle search_entities_by_name tool.
    
    This tool searches for entities by name and returns the intersection with available entity types.
    
    Args:
        session: The GraphQL client session
        arguments: Dictionary containing:
            - entity_name: Name of the entity to search for
            
    Returns:
        List of TextContent containing only the intersection of found and available entity types
    """
    logger.info("Executing search_entities_by_name")
    
    entity_name = arguments.get("entity_name", "").strip()
    if not entity_name:
        return [mcp_types.TextContent(type="text", text="Error: entity_name is required and cannot be empty")]
    
    try:
        # Build and execute the search query
        search_query = f"""
        query EntitySearchByName {{
          stixCoreObjects(
            search: "{entity_name}"
            orderBy: _score
            orderMode: desc
            first: 10
          ) {{
            edges {{
              node {{
                entity_type
              }}
            }}
          }}
        }}
        """
        
        # Execute search query
        search_result = await session.execute(gql(search_query))
        
        # Get all available entity types
        entity_names_query = """
        query StixRelationshipsMapping {
          schemaRelationsTypesMapping {
            key
          }
        }
        """
        entity_names_result = await session.execute(gql(entity_names_query))
        
        # Extract unique entity types from search results
        found_entity_types = set()
        edges = search_result.get("stixCoreObjects", {}).get("edges", [])
        for edge in edges:
            entity_type = edge.get("node", {}).get("entity_type")
            if entity_type:
                found_entity_types.add(entity_type)
        
        # Extract all unique entity names from mappings
        available_entity_types = set()
        mappings = entity_names_result.get("schemaRelationsTypesMapping", [])
        for mapping in mappings:
            key = mapping["key"]
            if "_" in key:
                from_entity, to_entity = key.split("_", 1)
                available_entity_types.add(from_entity)
                available_entity_types.add(to_entity)
        
        # Find intersection and sort it
        intersection = sorted(list(found_entity_types.intersection(available_entity_types)))
        
        return [mcp_types.TextContent(type="text", text=json.dumps(intersection, indent=2))]
        
    except Exception as e:
        logger.error(f"Error in search_entities_by_name: {str(e)}")
        return [mcp_types.TextContent(
            type="text", 
            text=f"Error searching entities by name: {str(e)}"
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
                "validate_graphql_query": handle_validate_graphql_query,
                "get_stix_relationships_mapping": handle_get_stix_relationships_mapping,
                "get_query_fields": handle_get_query_fields,
                "get_entity_names": handle_get_entity_names,
                "search_entities_by_name": handle_search_entities_by_name
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