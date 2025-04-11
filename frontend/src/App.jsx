import React, { useState } from "react";
import { JSONTree } from "react-json-tree";
import axios from "axios";
import {
  Input,
  Button,
  List,
  Spin,
  Tag,
  Typography,
  message,
  Card,
} from "antd";
import { SearchOutlined } from "@ant-design/icons";

const { Paragraph, Title } = Typography;

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);

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
      const response = await axios.get(
        `${API_BASE_URL}/api/search/?q=${query}`
      );
      setResults(response.data);
    } catch (error) {
      message.error("An error occurred while fetching results.");
    } finally {
      setLoading(false);
    }
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
              <Title level={4}>Answer</Title>
              <p>{results["answer"]}</p>
            </Card>
          )}
          <List
            itemLayout="vertical"
            size="large"
            dataSource={results["relevant_documents"] || []}
            renderItem={(item) => (
              <Card
                style={styles.resultCard}
                key={item.title || item.name || item.disease_name}
              >
                <List.Item>
                  <List.Item.Meta
                    title={
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
                        &nbsp;
                        {item.data_source && (
                          <Tag color="#108ee9">{item.data_source}</Tag>
                        )}
                      </a>
                    }
                    description={
                      <Paragraph
                        ellipsis={
                          item.text || item.description ? { rows: 5 } : false
                        }
                        style={styles.resultDescription}
                      >
                        {item.text || item.description || (
                          <JSONTree
                            data={item}
                            theme={"summerfruit:inverted"}
                          />
                        )}
                      </Paragraph>
                    }
                  />
                </List.Item>
              </Card>
            )}
          />
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
};

export default App;
