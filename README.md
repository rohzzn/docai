# Confluence API Integration

This project demonstrates how to interact with the Confluence Cloud REST API using OAuth 2.0 authentication. It allows you to:

- Retrieve spaces from your Confluence instance
- List pages within a space
- Fetch and save page content
- Handle token refresh automatically

## Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/doc-ai.git
cd doc-ai
```

2. Install dependencies:
```bash
npm install axios dotenv
```

3. Configure your environment:
   - Create a `.env` file with the following variables:
   ```
   CONFLUENCE_ACCESS_TOKEN=your_access_token
   CONFLUENCE_REFRESH_TOKEN=your_refresh_token
   CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki
   CONFLUENCE_CLIENT_ID=your_client_id
   CONFLUENCE_CLIENT_SECRET=your_client_secret
   ```
   - Or use the `run-confluence.js` script to set environment variables directly in code

## Usage

### Basic Usage

Run the script to fetch spaces and the first page from the first space:

```bash
node run-confluence.js
```

### Extended Usage

The `confluence-page-content.js` script demonstrates how to:
- Retrieve and save full page content
- Save tokens to a file for persistence
- Handle token refresh

```bash
node confluence-page-content.js
```

## API Client Features

The `ConfluenceClient` class provides:

- Automatic token refresh on 401 errors
- Error handling for API requests
- Methods for common operations:
  - `getSpaces()` - List all spaces
  - `getSpace(spaceKey)` - Get a specific space by key
  - `getPages(spaceId)` - List pages in a space
  - `getPageContent(pageId)` - Get content for a specific page
  - `savePageContentToFile(pageId, fileName)` - Save page content to a file

## OAuth 2.0 Setup

To obtain OAuth credentials:

1. Create an app in the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Configure OAuth 2.0 with the following scopes:
   - `read:confluence-content.all`
   - `read:confluence-content.summary`
   - `read:confluence-space.summary`
3. Set your callback URL (e.g., `http://localhost:8000/oauth/callback`)
4. Use the authorization code flow to obtain access and refresh tokens

## License

MIT 