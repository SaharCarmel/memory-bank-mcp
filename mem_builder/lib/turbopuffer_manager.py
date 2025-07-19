"""
Turbopuffer Manager for handling vector database operations
"""

import turbopuffer
import os
import concurrent.futures
from typing import List, Dict, Any
from lib.git_utils import extract_repo_name
from lib.logger import get_logger
import tiktoken


class TurbopufferManager:
    """Manages Turbopuffer operations for document storage and retrieval"""
    
    def __init__(self, region: str = "gcp-europe-west3"):
        """Initialize Turbopuffer manager"""
        self.logger = get_logger("turbopuffer_manager")
        
        api_key = os.getenv("TURBOPUFFER_API_KEY")
        if not api_key:
            raise ValueError("TURBOPUFFER_API_KEY environment variable is required")
        
        self.tpuf = turbopuffer.Turbopuffer(
            api_key=api_key,
            region=region,
        )
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create an embedding with OpenAI, optimized for performance with smaller dimensions"""
        if not os.getenv("OPENAI_API_KEY"):
            self.logger.warning("OPENAI_API_KEY not set, using random vectors")
            return [__import__('random').random()] * 512  # Smaller dimension for performance
        
        try:
            import openai
            client = openai.OpenAI()
            # Use text-embedding-3-small with reduced dimensions for better performance
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                dimensions=512  # Reduced from 1536 to 512 for faster queries
            )
            return response.data[0].embedding
        except ImportError:
            self.logger.warning("OpenAI not installed, using random vectors")
            return [__import__('random').random()] * 512
        except Exception as e:
            self.logger.error(f"Error creating embedding: {e}")
            return [__import__('random').random()] * 512
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content with proper encoding handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                return f"[Binary file: {os.path.basename(file_path)}]"
        except Exception as e:
            return f"[Error reading file: {str(e)}]"
    
    def upload_files(self, downloads_dir: str, repo_url: str) -> bool:
        """Upload all downloaded files to Turbopuffer"""
        try:
            # Extract repo name for namespace
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Try to clear existing data if namespace exists, otherwise continue
            try:
                self.logger.info(f"Checking namespace: {repo_name}")
                ns.delete_all()
                self.logger.info(f"Cleared existing data in namespace: {repo_name}")
            except Exception as clear_error:
                # Namespace might not exist yet, which is fine - it will be created on first write
                self.logger.info(f"Namespace {repo_name} doesn't exist yet, will be created on first write")
            
            self.logger.info(f"Uploading files to namespace: {repo_name}")
            
            # Find all files in the downloads directory
            all_files = []
            for root, _, files in os.walk(downloads_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            
            if not all_files:
                self.logger.warning("No files found in downloads directory")
                return False
            
            self.logger.info(f"Found {len(all_files)} files to upload")
            
            # Process files in batches for better performance
            # Larger batches for better throughput, up to 256MB limit
            batch_size = 500  # Increased from 100 for better write performance
            total_batches = (len(all_files) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(all_files))
                batch_files = all_files[start_idx:end_idx]
                
                self.logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)")
                
                upsert_rows = []
                for file_path in batch_files:
                    relative_path = os.path.relpath(file_path, downloads_dir)
                    content = self._read_file_content(file_path)
                    
                    # Create meaningful text for embedding
                    file_info = f"File: {relative_path}\nContent:\n{content}"
                    
                    # Limit content length for embedding (OpenAI has token limits)
                    encoding = tiktoken.get_encoding("cl100k_base")
                    tokens = encoding.encode(file_info)
                    if len(tokens) > 7000:
                        truncated_tokens = tokens[:7000]
                        file_info = encoding.decode(truncated_tokens) + "...[truncated]"
                    
                    # Use hash of file path for consistent, unique U64 IDs
                    file_hash = hash(relative_path) & 0x7FFFFFFFFFFFFFFF  # Ensure positive 64-bit int
                    
                    # Extract file extension for proper recreation
                    file_extension = os.path.splitext(relative_path)[1]
                    
                    upsert_row = {
                        'id': file_hash,  # U64 ID for better performance
                        'vector': self._create_embedding(file_info),
                        'file_name': os.path.basename(file_path),
                        'file_path': relative_path,  # Add relative path for reference
                        'file_extension': file_extension,  # Store file extension
                        'content': content,
                        'repo': repo_name,
                    }

                    upsert_rows.append(upsert_row)
                
                # Upload batch to Turbopuffer
                self.logger.info(f"Uploading batch {batch_idx + 1} ({len(upsert_rows)} files)...")
                
                ns.write(
                    upsert_rows=upsert_rows,
                    distance_metric='cosine_distance',
                    schema={
                        "content": {
                            "type": "string",
                            "full_text_search": True,
                            "filterable": False,  # Content not used for filtering, only FTS
                        },
                        "file_name": {
                            "type": "string", 
                            "filterable": False,  # 50% discount for non-filterable
                        },
                        "file_path": {
                            "type": "string", 
                            "filterable": False,  # Non-filterable for performance
                        },
                        "file_extension": {
                            "type": "string",
                            "filterable": False,  # Allow filtering by file type
                        },
                        "repo": {
                            "type": "string",
                            "filterable": True,  # Used for namespace filtering
                        },
                    }
                )
                
                self.logger.info(f"Successfully uploaded batch {batch_idx + 1}/{total_batches}")
            
            self.logger.info(f"Successfully uploaded {len(all_files)} files to namespace '{repo_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error uploading to Turbopuffer: {e}")
            return False
    
    def _write_batch_concurrent(self, ns, batch_data: Dict) -> bool:
        """Helper method to write a single batch concurrently"""
        try:
            ns.write(
                upsert_rows=batch_data['upsert_rows'],
                distance_metric='cosine_distance',
                schema=batch_data['schema']
            )
            return True
        except Exception as e:
            self.logger.error(f"Error writing batch {batch_data['batch_idx']}: {e}")
            return False
    
    def upload_files_concurrent(self, downloads_dir: str, repo_url: str, max_workers: int = 3) -> bool:
        """Upload all downloaded files to Turbopuffer using concurrent writes for better performance"""
        try:
            # Extract repo name for namespace
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Try to clear existing data if namespace exists, otherwise continue
            try:
                self.logger.info(f"Checking namespace: {repo_name}")
                ns.delete_all()
                self.logger.info(f"Cleared existing data in namespace: {repo_name}")
            except Exception as clear_error:
                # Namespace might not exist yet, which is fine - it will be created on first write
                self.logger.info(f"Namespace {repo_name} doesn't exist yet, will be created on first write")
            
            self.logger.info(f"Uploading files to namespace: {repo_name} with {max_workers} concurrent workers")
            
            # Find all files in the downloads directory
            all_files = []
            for root, _, files in os.walk(downloads_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
            
            if not all_files:
                self.logger.warning("No files found in downloads directory")
                return False
            
            self.logger.info(f"Found {len(all_files)} files to upload")
            
            # Prepare batches for concurrent processing
            batch_size = 200  # Smaller batches for concurrent processing
            total_batches = (len(all_files) + batch_size - 1) // batch_size
            batch_data_list = []
            
            schema = {
                "content": {
                    "type": "string",
                    "full_text_search": True,
                    "filterable": False,
                },
                "file_name": {
                    "type": "string", 
                    "filterable": False,
                },
                "file_path": {
                    "type": "string", 
                    "filterable": False,
                },
                "file_extension": {
                    "type": "string",
                    "filterable": False,  # Allow filtering by file type
                },
                "repo": {
                    "type": "string",
                    "filterable": True,
                },
            }
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(all_files))
                batch_files = all_files[start_idx:end_idx]
                
                self.logger.info(f"Preparing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)")
                
                upsert_rows = []
                for file_path in batch_files:
                    relative_path = os.path.relpath(file_path, downloads_dir)
                    content = self._read_file_content(file_path)
                    
                    # Create meaningful text for embedding
                    file_info = f"File: {relative_path}\nContent:\n{content}"
                    
                    # Limit content length for embedding
                    encoding = tiktoken.get_encoding("cl100k_base")
                    tokens = encoding.encode(file_info)
                    if len(tokens) > 7000:
                        truncated_tokens = tokens[:7000]
                        file_info = encoding.decode(truncated_tokens) + "...[truncated]"
                    
                    file_hash = hash(relative_path) & 0x7FFFFFFFFFFFFFFF
                    
                    # Extract file extension for proper recreation
                    file_extension = os.path.splitext(relative_path)[1]
                    
                    upsert_row = {
                        'id': file_hash,
                        'vector': self._create_embedding(file_info),
                        'file_name': os.path.basename(file_path),
                        'file_path': relative_path,
                        'file_extension': file_extension,  # Store file extension
                        'content': content,
                        'repo': repo_name,
                    }
                    upsert_rows.append(upsert_row)
                
                batch_data_list.append({
                    'batch_idx': batch_idx + 1,
                    'upsert_rows': upsert_rows,
                    'schema': schema
                })
            
            # Execute batches concurrently
            self.logger.info(f"Executing {len(batch_data_list)} batches concurrently...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self._write_batch_concurrent, ns, batch_data) 
                    for batch_data in batch_data_list
                ]
                
                successful_batches = 0
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    if future.result():
                        successful_batches += 1
                        self.logger.info(f"Completed batch {successful_batches}/{total_batches}")
                    else:
                        self.logger.error(f"Failed to upload batch {i + 1}")
            
            if successful_batches == total_batches:
                self.logger.info(f"Successfully uploaded all {len(all_files)} files to namespace '{repo_name}'")
                return True
            else:
                self.logger.error(f"Only {successful_batches}/{total_batches} batches uploaded successfully")
                return False
                
        except Exception as e:
            self.logger.error(f"Error uploading to Turbopuffer: {e}")
            return False
    
    def search_by_vector(self, repo_url: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents by vector similarity"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Create embedding for query
            query_vector = self._create_embedding(query_text)
            
            # Search by vector similarity - only include necessary attributes
            results = ns.query(
                rank_by=("vector", "ANN", query_vector),
                top_k=top_k,
                filters=("repo", "Eq", repo_name),
                include_attributes=["file_name", "file_path", "file_extension", "content"],
            )
            
            return [
                {
                    'id': getattr(row, 'id', None),
                    'file_name': getattr(row, 'file_name', ''),
                    'file_path': getattr(row, 'file_path', ''),
                    'file_extension': getattr(row, 'file_extension', ''),
                    'content': getattr(row, 'content', ''),
                    'distance': getattr(row, '$dist', 0.0),
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Error searching by vector: {e}")
            return []
    
    def search_by_text(self, repo_url: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents by full-text search (BM25)"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Search by full-text - only include necessary attributes
            results = ns.query(
                top_k=top_k,
                filters=("repo", "Eq", repo_name),
                rank_by=('text', 'BM25', query_text),
                include_attributes=["file_name", "file_path", "file_extension", "content"],
            )
            
            return [
                {
                    'id': getattr(row, 'id', None),
                    'file_name': getattr(row, 'file_name', ''),
                    'file_path': getattr(row, 'file_path', ''),
                    'file_extension': getattr(row, 'file_extension', ''),
                    'content': getattr(row, 'content', ''),
                    'score': getattr(row, '$dist', 0.0),
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Error searching by text: {e}")
            return []
    
    def hybrid_search(self, repo_url: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search optimized for first-stage retrieval.
        Follows Turbopuffer best practice of filtering large document sets down to smaller candidates.
        """
        try:
            # Use larger candidate sets for first-stage retrieval, then refine
            candidate_k = min(top_k * 3, 50)  # Get more candidates for better fusion
            
            # Get results from both methods with larger candidate sets
            vector_results = self.search_by_vector(repo_url, query_text, candidate_k)
            text_results = self.search_by_text(repo_url, query_text, candidate_k)
            
            # Weighted fusion with normalization for better ranking
            combined_results = {}
            
            # Normalize and weight vector results (semantic similarity)
            for i, result in enumerate(vector_results):
                doc_id = result['id']
                # Convert distance to similarity score (lower distance = higher similarity)
                vector_score = 1.0 / (1.0 + result.get('distance', 1.0))
                # Position-based bonus for top results
                position_bonus = (candidate_k - i) / candidate_k * 0.1
                
                combined_results[doc_id] = {
                    **result,
                    'vector_score': vector_score + position_bonus,
                    'text_score': 0.0,
                    'search_type': 'vector'
                }
            
            # Add and weight text results (keyword matching)
            for i, result in enumerate(text_results):
                doc_id = result['id']
                # BM25 scores are already normalized
                text_score = result.get('score', 0.0)
                position_bonus = (candidate_k - i) / candidate_k * 0.1
                text_score += position_bonus
                
                if doc_id in combined_results:
                    # Document found in both searches - combine scores
                    combined_results[doc_id]['text_score'] = text_score
                    combined_results[doc_id]['search_type'] = 'hybrid'
                else:
                    # Document only in text search
                    combined_results[doc_id] = {
                        **result,
                        'vector_score': 0.0,
                        'text_score': text_score,
                        'search_type': 'text'
                    }
            
            # Calculate final hybrid scores (weighted combination)
            for doc_id, result in combined_results.items():
                # Weight vector search slightly higher for semantic understanding
                vector_weight = 0.6
                text_weight = 0.4
                
                result['hybrid_score'] = (
                    vector_weight * result['vector_score'] +
                    text_weight * result['text_score']
                )
            
            # Sort by hybrid score and return top_k results
            ranked_results = sorted(
                combined_results.values(),
                key=lambda x: x['hybrid_score'],
                reverse=True
            )
            
            return ranked_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {e}")
            # Fallback to vector search if hybrid fails
            return self.search_by_vector(repo_url, query_text, top_k)
    
    def get_all_files(self, repo_url: str) -> List[Dict[str, Any]]:
        """Get all files for a repository"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Get all files - only include minimal necessary attributes for performance
            results = ns.query(
                top_k=1000,  # Adjust as needed
                filters=("repo", "Eq", repo_name),
                include_attributes=["file_name", "file_path"],  # Minimal attributes for listing
            )
            return [
                {
                    'id': getattr(row, 'id', None),
                    'file_name': getattr(row, 'file_name', ''),
                    'file_path': getattr(row, 'file_path', ''),
                }
                for row in results.rows
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting all files: {e}")
            return []
    
    def delete_namespace(self, repo_url: str) -> bool:
        """Delete all data for a repository namespace"""
        try:
            repo_name = extract_repo_name(repo_url)
            # Delete by IDs
            ns = self.tpuf.namespace(repo_name)
            ns.delete_all()
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting namespace: {e}")
            return False
    
    def search_files(self, repo_url: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search files using hybrid search (combines vector and text search)"""
        return self.hybrid_search(repo_url, query_text, top_k)
    
    def prewarm_namespace(self, repo_url: str) -> bool:
        """Prewarm a namespace to minimize cold start latency"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            self.logger.info(f"Prewarming namespace: {repo_name}")
            
            # Perform a lightweight query to warm up the namespace
            # This helps minimize cold query latency as recommended in docs
            ns.query(
                top_k=1,
                filters=("repo", "Eq", repo_name),
                include_attributes=[],  # Minimal attributes for prewarming
            )
            
            self.logger.info(f"Namespace '{repo_name}' prewarmed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error prewarming namespace: {e}")
            return False
    
    def namespace_exists(self, repo_url: str) -> bool:
        """Check if a namespace exists for the given repository"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            # Try to query the namespace to see if it exists
            # If it has any data, it exists
            results = ns.query(top_k=1, include_attributes=[])
            return True  # If query succeeds, namespace exists
        except Exception as e:
            # If query fails with 404 or similar, namespace doesn't exist
            if "404" in str(e) or "not found" in str(e).lower():
                self.logger.debug(f"Namespace {repo_name} doesn't exist yet")
                return False
            else:
                self.logger.error(f"Error checking namespace existence: {e}")
                return False

    def download_all_files_from_namespace(self, repo_url: str, output_dir: str) -> bool:
        """Download all files from a namespace to a local directory"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            self.logger.info(f"Downloading all files from namespace: {repo_name}")
            
            # Get all files from the namespace
            results = ns.query(
                top_k=10000,  # Large number to get all files
                filters=("repo", "Eq", repo_name),
                include_attributes=["file_name", "file_path", "file_extension", "content"],
            )
            
            if not results.rows:
                self.logger.warning(f"No files found in namespace: {repo_name}")
                return False
            
            self.logger.info(f"Found {len(results.rows)} files in namespace")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            downloaded_count = 0
            for row in results.rows:
                try:
                    file_path = getattr(row, 'file_path', '')
                    file_extension = getattr(row, 'file_extension', '')
                    content = getattr(row, 'content', '')
                    
                    if not file_path or not content:
                        continue
                    
                    # Ensure file has proper extension (use stored extension if available)
                    if file_extension and not file_path.endswith(file_extension):
                        file_path = file_path + file_extension
                    
                    # Create full local file path
                    local_file_path = os.path.join(output_dir, file_path)
                    
                    # Create directory structure if needed
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    # Write file content
                    with open(local_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    downloaded_count += 1
                    self.logger.debug(f"Downloaded: {file_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error downloading file {getattr(row, 'file_path', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Successfully downloaded {downloaded_count} files from namespace '{repo_name}' to: {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading files from namespace: {e}")
            return False
    
    def download_all_files_to_sandbox(self, repo_url: str, sandbox, output_dir: str) -> bool:
        """Download all files from a namespace and upload them to sandbox"""
        try:
            repo_name = extract_repo_name(repo_url)
            ns = self.tpuf.namespace(repo_name)
            
            self.logger.info(f"Downloading all files from namespace to sandbox: {repo_name}")
            
            # Get all files from the namespace
            results = ns.query(
                top_k=1000,  # Large number to get all files
                filters=("repo", "Eq", repo_name),
                include_attributes=["file_name", "file_path", "file_extension", "content"],
            )
            
            if not results.rows:
                self.logger.warning(f"No files found in namespace: {repo_name}")
                return False
            
            self.logger.info(f"Found {len(results.rows)} files in namespace")
            
            # Create output directory in sandbox
            sandbox.process.exec(f"mkdir -p {output_dir}")
            
            uploaded_count = 0
            for row in results.rows:
                try:
                    file_path = getattr(row, 'file_path', '')
                    file_extension = getattr(row, 'file_extension', '')
                    content = getattr(row, 'content', '')
                    
                    if not file_path or not content:
                        continue
                    
                    # Ensure file has proper extension (use stored extension if available)
                    if file_extension and not file_path.endswith(file_extension):
                        file_path = file_path + file_extension
                    
                    # Create full sandbox file path
                    sandbox_file_path = os.path.join(output_dir, file_path)
                    
                    # Create directory structure in sandbox if needed
                    sandbox_dir = os.path.dirname(sandbox_file_path)
                    sandbox.process.exec(f"mkdir -p {sandbox_dir}")
                    
                    # Upload file content to sandbox with proper encoding based on file type
                    if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz']:
                        # For binary files, assume they were stored as base64 or handle as text
                        sandbox.fs.upload_file(content.encode('utf-8'), sandbox_file_path)
                    else:
                        # For text files
                        sandbox.fs.upload_file(content.encode('utf-8'), sandbox_file_path)
                    
                    uploaded_count += 1
                    self.logger.debug(f"Uploaded to sandbox: {file_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error uploading file to sandbox {getattr(row, 'file_path', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Successfully uploaded {uploaded_count} files from namespace '{repo_name}' to sandbox: {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading files from namespace to sandbox: {e}")
            return False
