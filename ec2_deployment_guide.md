# DocuQuery AI: EC2 Deployment Guide

This guide helps you deploy the DocuQuery application on an Amazon EC2 instance.

## Prerequisites

- An AWS account with access to EC2
- A running EC2 instance with Ubuntu (recommended)
- Docker and Docker Compose installed on the EC2 instance

## 1. Setting Up an EC2 Instance

If you haven't already set up an EC2 instance:

1. Log in to the AWS Management Console and navigate to EC2
2. Click "Launch Instance"
3. Choose Ubuntu Server 22.04 LTS
4. Select an instance type (t2.medium or better recommended)
5. Configure security groups to allow:
   - SSH (port 22)
   - HTTP (port 80)
   - HTTPS (port 443)
   - Custom TCP for application ports (3000, 8000, 7474, 7687)
6. Launch the instance and save the key pair

## 2. Installing Docker and Docker Compose

Connect to your EC2 instance:

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-dns
```

Install Docker:

```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce
sudo usermod -aG docker ${USER}
```

Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Log out and log back in for the group changes to take effect.

## 3. Deploying the Application

### Clone the Repository

```bash
git clone https://github.com/yourusername/doc-ai.git
cd doc-ai
```

### Create Environment Variables

Create a `.env` file with your environment variables:

```bash
cat > .env << EOL
DJANGO_SECRET_KEY="your-django-secret-key"
DEBUG=0
OPENAI_API_KEY="your-openai-api-key"
CONFLUENCE_ACCESS_TOKEN="your-confluence-access-token"
CONFLUENCE_REFRESH_TOKEN="your-confluence-refresh-token"
CONFLUENCE_BASE_URL="https://rdcrn.atlassian.net/wiki"
CONFLUENCE_CLIENT_ID="your-confluence-client-id"
CONFLUENCE_CLIENT_SECRET="your-confluence-client-secret"
RDCRN_CONFLUENCE_SPACE="RPD"
RDCRN_CONFLUENCE_URL="https://rdcrn.atlassian.net/wiki"
NEO4J_AUTH=neo4j/your-secure-password
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474
EOL
```

### Build and Start the Docker Containers

```bash
docker-compose build
docker-compose up -d
```

### Populate Neo4j with Initial Data

```bash
python3 populate_neo4j.py
```

## 4. Setting Up Nginx as a Reverse Proxy (Optional)

For production deployments, it's recommended to use Nginx as a reverse proxy:

```bash
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/doc-ai << EOL
server {
    listen 80;
    server_name your-domain-or-ip;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable the site
sudo ln -s /etc/nginx/sites-available/doc-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 5. Setting Up SSL with Let's Encrypt (Optional)

For secure HTTPS access:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 6. Updating the Application

To update the application with new changes:

```bash
cd ~/doc-ai
git pull
docker-compose down
docker-compose build
docker-compose up -d
python3 populate_neo4j.py
```

## 7. Monitoring and Logs

To view container logs:

```bash
# All containers
docker-compose logs

# Specific container
docker-compose logs django
docker-compose logs react
docker-compose logs neo4j
```

## 8. Troubleshooting

- If Neo4j isn't accessible, check its logs with `docker-compose logs neo4j`
- If the API is not responding, check Django logs with `docker-compose logs django`
- Check that all environment variables are correctly set in the `.env` file
- Verify that all required ports are open in EC2 security groups 