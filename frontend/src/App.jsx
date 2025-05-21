import React, { useState } from "react";
import { JSONTree } from "react-json-tree";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import {
  Input,
  Button,
  List,
  Spin,
  Tag,
  Typography,
  message,
  Card,
  Collapse,
} from "antd";
import { SearchOutlined } from "@ant-design/icons";

const { Paragraph, Title, Text } = Typography;
const { Panel } = Collapse;

// Auto-detect API URL based on current hostname
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // For production environment
  if (hostname === 'doc-ai.rarediseasesnetwork.org') {
    // Use relative URL to avoid CORS issues
    return '';
  }
  
  // For development environment - use the standard local URL
  return process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  const handleSearch = async () => {
    if (query.trim() === "") {
      message.warning("Please enter a search query.");
      setResults({});
      return;
    }

    setLoading(true);

    try {
      // Fixed API URL - added back the 'api/' prefix to match the Django URL configuration
      const apiUrl = `${API_BASE_URL}/api/search/?q=${encodeURIComponent(query)}`;
      console.log(`Calling API: ${apiUrl}`);
      
      const response = await axios.get(apiUrl, {
        withCredentials: false,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      console.log("API response:", response.data);
      setResults(response.data);
    } catch (error) {
      console.error("API error:", error);
      
      let errorMessage = "An error occurred while fetching results.";
      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
        errorMessage += ` Status: ${error.response.status}`;
        
        if (error.response.data && error.response.data.error) {
          errorMessage += ` Message: ${error.response.data.error}`;
        }
      } else if (error.request) {
        console.error("Request made but no response:", error.request);
        errorMessage += " No response received from server. Backend might not be running.";
      } else {
        console.error("Error setting up request:", error.message);
        errorMessage += ` ${error.message}`;
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // Helper function to clean document text from field labels
  const cleanDocumentText = (text) => {
    if (!text) return "";
    
    // Remove field labels like id:, title:, data_source:, text:
    return text
      .replace(/id:"[^"]*"\s*/g, '')
      .replace(/title:"[^"]*"\s*/g, '')
      .replace(/data_source:"[^"]*"\s*/g, '')
      .replace(/text:"[^"]*"\s*/g, '');
  };

  return (
    <div style={styles.container}>
      <Title style={styles.title}>DocuQueryAI</Title>
      <div style={styles.searchContainer}>
        <Input
          placeholder="Enter your search query"
          value={query}
          onChange={handleInputChange}
          style={styles.input}
          size="large"
          onPressEnter={handleSearch}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          size="large"
          onClick={handleSearch}
          style={styles.searchButton}
          loading={loading}
        >
          Search
        </Button>
      </div>

      {loading ? (
        <div style={styles.loading}>
          <Spin size="large" />
        </div>
      ) : (
        <div>
          {results["answer"] && (
            <Card style={styles.answerCard}>
              <div className="markdown-body">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                >
                  {results["answer"]}
                </ReactMarkdown>
              </div>
              
              {(results["relevant_documents"] || []).length > 0 && (
                <Button 
                  type="link" 
                  onClick={() => setShowSources(!showSources)}
                  style={styles.sourcesButton}
                >
                  {showSources ? "Hide Sources" : "Show Sources"}
                </Button>
              )}
            </Card>
          )}
          
          {showSources && (results["relevant_documents"] || []).length > 0 && (
            <div style={styles.sourcesSection}>
              <Title level={5}>Sources</Title>
          <List
            itemLayout="vertical"
            size="large"
            dataSource={results["relevant_documents"] || []}
                renderItem={(item) => {
                  // For display in the UI, prioritize regular text content
                  const displayText = item.text || item.description || '';
                  
                  return (
              <Card
                style={styles.resultCard}
                      key={item.title || item.name || item.disease_name || item.id}
              >
                <List.Item>
                  <List.Item.Meta
                    title={
                            <div>
                      <a
                        href={
                          item.source || item.rfa_url || item.website_url || "#"
                        }
                        rel="noopener noreferrer"
                        style={styles.resultTitle}
                        target="_blank"
                      >
                        {item.title ||
                          item.name ||
                          item.disease_name ||
                          item.id}
                              </a>
                        &nbsp;
                        {item.data_source && (
                          <Tag color="#108ee9">{item.data_source}</Tag>
                        )}
                            </div>
                    }
                    description={
                      <Paragraph
                              ellipsis={displayText ? { rows: 5 } : false}
                        style={styles.resultDescription}
                      >
                              {displayText ? cleanDocumentText(displayText) : 
                                <JSONTree data={item} theme={"summerfruit:inverted"} />
                              }
                      </Paragraph>
                    }
                  />
                </List.Item>
              </Card>
                  );
                }}
              />
            </div>
            )}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "900px",
    margin: "50px auto",
    padding: "20px",
    backgroundColor: "#f0f2f5",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
  },
  title: {
    textAlign: "center",
    marginBottom: "20px",
  },
  searchContainer: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: "20px",
  },
  input: {
    width: "70%",
    marginRight: "10px",
  },
  searchButton: {
    width: "150px",
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    marginTop: "20px",
  },
  answerCard: {
    marginBottom: "20px",
    backgroundColor: "#ffffff",
    padding: "20px",
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  },
  resultCard: {
    marginBottom: "20px",
    padding: "20px",
    backgroundColor: "#ffffff",
    borderRadius: "8px",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  },
  resultTitle: {
    fontSize: "18px",
    fontWeight: "bold",
    color: "#1890ff",
  },
  resultDescription: {
    color: "#555",
    fontSize: "16px",
  },
  sourcesButton: {
    marginTop: "10px",
    padding: "0",
  },
  sourcesSection: {
    marginTop: "20px",
  },
};

export default App;
