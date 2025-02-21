# MCP Beeminder Server

This project implements a [Model Context Protocol
(MCP)](https://modelcontextprotocol.io/introduction) server for interacting with
the [Beeminder](https://www.beeminder.com) API.

![Beeminder MCP Server](assets/mcp-bm.png)

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardises how applications provide context to Large Language Models (LLMs). It acts like a "USB-C port for AI applications" - providing a standardised way to connect AI models to different data sources and tools.

MCP follows a client-server architecture where:
- **MCP Hosts**: Programs like Claude Desktop or IDEs that want to access data through MCP
- **MCP Clients**: Protocol clients that maintain 1:1 connections with servers
- **MCP Servers**: Lightweight programs that expose specific capabilities through the standardised protocol
- **Local Data Sources**: Your computer's files, databases, and services that MCP servers can securely access
- **Remote Services**: External systems available over the internet that MCP servers can connect to

## What is Beeminder?

Beeminder is a tool for overcoming akrasia (acting against your better judgment) by combining:
- Quantified self-tracking
- Visual feedback via a "Bright Red Line" (BRL) showing your commitment path
- Financial stakes that increase with each failure
- Flexible commitment with a 7-day "akrasia horizon"

This server implementation provides MCP-compatible access to Beeminder's API, allowing AI assistants to help users manage their Beeminder goals, datapoints, and other related functionality.

## Features

The server provides access to core Beeminder functionality including:
- Goal management (create, read, update, delete)
- Datapoint management (create, read, delete)
- User information retrieval
- Support for all Beeminder goal types:
  - Do More ("hustler")
  - Odometer ("biker")
  - Weight Loss ("fatloser")
  - Gain Weight ("gainer")
  - Inbox Fewer ("inboxer")
  - Do Less ("drinker")


## Running locally with the Claude Desktop app

### Prerequisites

You'll need your Beeminder API key and username to run the server. To get your API key:

1. Log into Beeminder
2. Go to [https://www.beeminder.com/api/v1/auth_token.json](https://www.beeminder.com/api/v1/auth_token.json)

You'll also need `uv` installed. See the [uv
docs](https://docs.astral.sh/uv/getting-started/installation/) for installation
instructions. You can use something else but you'll need to change the `command`
in the `claude_desktop_config.json` file.

### Manual Installation

1. Clone this repository.
2. Add the following to your `claude_desktop_config.json` file:
- On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```
"mcpServers": {
  "beeminder": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/repo/mcp-beeminder",
      "run",
      "mcp-beeminder"
    ],
    "env": {
        "BEEMINDER_API_KEY": "YOUR_BEEMINDER_API_KEY,
        "BEEMINDER_USERNAME": "YOUR_BEEMINDER_USERNAME"
    }
  }
}
```
3. Install and open the [Claude desktop app](https://claude.ai/download).
4. Try asking Claude to do a read/write operation of some sort to confirm the
   setup (e.g. list your Beeminder goals). If there are
   issues, use the Debugging tools provided in the MCP documentation
   [here](https://modelcontextprotocol.io/docs/tools/debugging).

## Acknowledgements

Thanks to [@ianm199](https://github.com/ianm199) for his
[`beeminder-client`](https://github.com/ianm199/beeminder_api_client) package,
on which this project is based.

And obviously thanks to the [Beeminder](https://www.beeminder.com) team for
building such a great product!

