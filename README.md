# Agentic Platform - OpenCTI GraphQL MCP Server

This MCP (Machine Control Protocol) server provides a set of tools to interact with OpenCTI's GraphQL API. It allows you to query and manipulate data in OpenCTI through a standardized interface.

## Features

- List available GraphQL types
- Get detailed type definitions
- Execute custom GraphQL queries
- Get STIX relationships mapping between types

## Prerequisites

- Python 3.7+
- Access to an OpenCTI instance
- OpenCTI API token

## Environment Variables

The server requires the following environment variables:

- `OPENCTI_URL`: The URL of your OpenCTI GraphQL endpoint
- `OPENCTI_TOKEN`: Your OpenCTI API token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agentic_platform.git
cd agentic_platform
```

2. Install dependencies:
```bash
pip install -r src/mcp_server/requirements.txt
```

## Usage

You can run the server using Python directly:

```bash
python src/mcp_server/opencti_graphql.py
```

Or configure it in your application with these parameters:

```json
{
    "command": "python",
    "args": ["src/mcp_server/opencti_graphql.py"],
    "env": {
        "OPENCTI_URL": "<url_graphql>",
        "OPENCTI_TOKEN": "<token_graphql>"
    }
}
```

## Available Tools

1. `list_graphql_types`
   - Lists all available GraphQL types in the OpenCTI schema
   - No parameters required

2. `get_types_definitions`
   - Fetches detailed definitions for specific GraphQL types
   - Parameters:
     - `type_name`: String or array of strings representing type names

3. `execute_graphql_query`
   - Executes a custom GraphQL query
   - Parameters:
     - `query`: String containing the GraphQL query

4. `get_stix_relationships_mapping`
   - Gets STIX relationships between types
   - Optional parameters:
     - `type_name`: Filter relationships for a specific type
