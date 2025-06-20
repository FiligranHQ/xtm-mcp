# Agentic Platform - MCP Servers Collection

This repository contains a collection of MCP (Machine Control Protocol) servers designed to interact with various services and APIs. Each server provides specific tools and capabilities for different platforms.

## Available MCP Servers

### 1. OpenCTI GraphQL Filigran Server

A server that provides tools to interact with OpenCTI's GraphQL API, allowing you to query and manipulate data in OpenCTI through a standardized interface.

#### Features

- List available GraphQL types
- Get detailed type definitions
- Execute custom GraphQL queries
- Get STIX relationships mapping between types

#### Prerequisites

- Python 3.7+
- Access to an OpenCTI instance
- OpenCTI API token

#### Environment Variables

The OpenCTI server requires the following environment variables:

- `OPENCTI_URL`: The URL of your OpenCTI GraphQL endpoint
- `OPENCTI_TOKEN`: Your OpenCTI API token


#### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agentic_platform.git
cd agentic_platform/src/mcp_server/opencti_graphql_filigran
```

2. Install dependencies for the specific server you want to use:
```bash
pip install -r requirements.txt
```



#### Usage

You can run the server using Python directly:

```bash
python opencti_graphql_filigran.py
```

Or configure it in your application with these parameters:

```json
{
    "command": "python",
    "args": ["<path_of_script>/opencti_graphql_filigran.py"],
    "env": {
        "OPENCTI_URL": "<url_graphql>",
        "OPENCTI_TOKEN": "<token_graphql>"
    }
}
```

#### Available Tools

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
