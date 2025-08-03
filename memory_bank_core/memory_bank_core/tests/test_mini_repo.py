"""
Create a mini test repository to validate Architecture Agent
"""

import os
import json
from pathlib import Path


def create_microservices_test_repo(base_path: Path):
    """Create a test microservices repository structure"""
    
    # Create base directory
    repo_path = base_path / "test_microservices"
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Create docker-compose.yml
    docker_compose = """version: '3.8'
services:
  user-service:
    build: ./services/user-service
    ports:
      - "3001:3000"
  
  product-service:
    build: ./services/product-service
    ports:
      - "3002:3000"
  
  order-service:
    build: ./services/order-service
    ports:
      - "3003:3000"
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
"""
    (repo_path / "docker-compose.yml").write_text(docker_compose)
    
    # Create services
    services = ["user-service", "product-service", "order-service"]
    for service in services:
        service_path = repo_path / "services" / service
        service_path.mkdir(parents=True, exist_ok=True)
        
        # package.json
        package_json = {
            "name": service,
            "version": "1.0.0",
            "main": "index.js",
            "dependencies": {
                "express": "^4.18.0",
                "mongoose": "^6.0.0"
            }
        }
        (service_path / "package.json").write_text(json.dumps(package_json, indent=2))
        
        # Simple index.js
        index_js = f"""const express = require('express');
const app = express();

app.get('/health', (req, res) => {{
    res.json({{ service: '{service}', status: 'healthy' }});
}});

app.listen(3000, () => {{
    console.log('{service} listening on port 3000');
}});
"""
        (service_path / "index.js").write_text(index_js)
        
        # Dockerfile
        dockerfile = f"""FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "index.js"]
"""
        (service_path / "Dockerfile").write_text(dockerfile)
    
    # Create frontend
    frontend_path = repo_path / "frontend"
    frontend_path.mkdir(exist_ok=True)
    
    frontend_package = {
        "name": "frontend",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.0.0",
            "react-dom": "^18.0.0"
        }
    }
    (frontend_path / "package.json").write_text(json.dumps(frontend_package, indent=2))
    
    # Create shared library
    lib_path = repo_path / "shared" / "common-utils"
    lib_path.mkdir(parents=True, exist_ok=True)
    
    lib_package = {
        "name": "@myapp/common-utils",
        "version": "1.0.0",
        "main": "index.js"
    }
    (lib_path / "package.json").write_text(json.dumps(lib_package, indent=2))
    
    print(f"Created test microservices repo at: {repo_path}")
    return repo_path


def create_monolith_test_repo(base_path: Path):
    """Create a test monolithic repository structure"""
    
    repo_path = base_path / "test_monolith"
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Create standard MVC structure
    dirs = [
        "src/controllers",
        "src/models",
        "src/views",
        "src/services",
        "src/utils",
        "config",
        "tests"
    ]
    
    for dir_path in dirs:
        (repo_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create main package.json
    package_json = {
        "name": "monolith-app",
        "version": "1.0.0",
        "main": "src/index.js",
        "dependencies": {
            "express": "^4.18.0",
            "sequelize": "^6.0.0"
        }
    }
    (repo_path / "package.json").write_text(json.dumps(package_json, indent=2))
    
    # Create sample files
    (repo_path / "src" / "index.js").write_text("// Main application entry point")
    (repo_path / "src" / "controllers" / "userController.js").write_text("// User controller")
    (repo_path / "src" / "models" / "User.js").write_text("// User model")
    
    print(f"Created test monolith repo at: {repo_path}")
    return repo_path


if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent / "test_repos"
    base_path.mkdir(exist_ok=True)
    
    create_microservices_test_repo(base_path)
    create_monolith_test_repo(base_path)