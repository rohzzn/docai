import os
import sys
from pathlib import Path

# Set OpenAI API key if it's not already set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-your-openai-api-key"  # Replace with actual key
    print("Set OPENAI_API_KEY environment variable")
else:
    print(f"OPENAI_API_KEY is already set: {os.environ['OPENAI_API_KEY'][:8]}...")

# Ensure Confluence environment variables are set
required_vars = [
    "CONFLUENCE_ACCESS_TOKEN",
    "CONFLUENCE_REFRESH_TOKEN",
    "CONFLUENCE_BASE_URL",
    "CONFLUENCE_CLIENT_ID",
    "CONFLUENCE_CLIENT_SECRET",
    "RDCRN_CONFLUENCE_SPACE",
    "RDCRN_CONFLUENCE_URL"
]

# Check if they're set and set them from confluence_test.py if not
for var in required_vars:
    if not os.environ.get(var):
        print(f"Setting missing environment variable: {var}")
        # Set them from the values in confluence_test.py
        if var == "CONFLUENCE_BASE_URL":
            os.environ[var] = "https://rdcrn.atlassian.net/wiki"
        elif var == "RDCRN_CONFLUENCE_URL":
            os.environ[var] = "https://rdcrn.atlassian.net/wiki"
        elif var == "RDCRN_CONFLUENCE_SPACE":
            os.environ[var] = "RPD"
        else:
            # For other variables, we need to grab them from confluence_test.py
            print(f"Need to set {var} from confluence_test.py")
    else:
        print(f"{var} is already set")

print("Environment variables check completed")

# Try to import and test ChatOpenAI
try:
    from langchain_openai import ChatOpenAI
    model = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    print("Successfully imported ChatOpenAI")
except Exception as e:
    print(f"Error importing or initializing ChatOpenAI: {str(e)}")
    import traceback
    traceback.print_exc() 