require('dotenv').config();
const axios = require('axios');

class ConfluenceClient {
  constructor() {
    this.baseURL = process.env.CONFLUENCE_BASE_URL;
    this.accessToken = process.env.CONFLUENCE_ACCESS_TOKEN;
    this.refreshToken = process.env.CONFLUENCE_REFRESH_TOKEN;
    this.clientId = process.env.CONFLUENCE_CLIENT_ID;
    this.clientSecret = process.env.CONFLUENCE_CLIENT_SECRET;
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    // Add response interceptor to handle token expiration
    this.client.interceptors.response.use(
      response => response,
      async error => {
        const originalRequest = error.config;
        
        // If token expired and we haven't tried to refresh yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          // Refresh the token
          await this.refreshAccessToken();
          
          // Update header with new token
          originalRequest.headers['Authorization'] = `Bearer ${this.accessToken}`;
          
          // Retry the request
          return this.client(originalRequest);
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  async refreshAccessToken() {
    try {
      const response = await axios.post('https://auth.atlassian.com/oauth/token', {
        grant_type: 'refresh_token',
        client_id: this.clientId,
        client_secret: this.clientSecret,
        refresh_token: this.refreshToken
      });
      
      // Update tokens
      this.accessToken = response.data.access_token;
      this.refreshToken = response.data.refresh_token;
      
      // Update client headers
      this.client.defaults.headers['Authorization'] = `Bearer ${this.accessToken}`;
      
      console.log('Token refreshed successfully');
      
      // If using this in production, you might want to save these new tokens
      // to your .env file or a secure storage
    } catch (error) {
      console.error('Error refreshing token:', error.message);
      throw error;
    }
  }
  
  // API methods
  
  async getSpaces() {
    try {
      const response = await this.client.get('/api/v2/spaces');
      return response.data;
    } catch (error) {
      console.error('Error fetching spaces:', error.message);
      throw error;
    }
  }
  
  async getSpace(spaceKey) {
    try {
      const response = await this.client.get(`/api/v2/spaces/${spaceKey}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching space ${spaceKey}:`, error.message);
      throw error;
    }
  }
  
  async getPages(spaceId) {
    try {
      const response = await this.client.get('/api/v2/pages', {
        params: { spaceId }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching pages for space ${spaceId}:`, error.message);
      throw error;
    }
  }
  
  async getPageContent(pageId) {
    try {
      const response = await this.client.get(`/api/v2/pages/${pageId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching page ${pageId}:`, error.message);
      throw error;
    }
  }
}

// Usage example
async function main() {
  try {
    const confluence = new ConfluenceClient();
    
    // Get spaces
    const spaces = await confluence.getSpaces();
    console.log('Spaces:', spaces.results.map(space => ({ name: space.name, key: space.key, id: space.id })));
    
    // If spaces exist, get pages from the first space
    if (spaces.results.length > 0) {
      const firstSpace = spaces.results[0];
      console.log(`\nFetching pages for space: ${firstSpace.name}`);
      
      const pages = await confluence.getPages(firstSpace.id);
      console.log('Pages:', pages.results?.map(page => ({ 
        title: page.title, 
        id: page.id 
      })) || 'No pages found');
    }
    
  } catch (error) {
    console.error('Error in main function:', error.message);
  }
}

main(); 