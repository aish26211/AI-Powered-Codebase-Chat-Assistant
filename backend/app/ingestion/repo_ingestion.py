"""
Repository Ingestion - Process entire codebases
Handles cloning, file discovery, and metadata extraction
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from git import Repo
from datetime import datetime
from .code_parser import CodeParser, CodeChunk

class RepositoryIngestion:
    """Ingest and process entire repositories"""
    
    def __init__(
        self,
        repo_path: str,
        ignore_patterns: List[str] = None,
        supported_extensions: List[str] = None
    ):
        """
        Initialize repository ingestion
        
        Args:
            repo_path: Path to local repository
            ignore_patterns: Directories/files to ignore
            supported_extensions: File extensions to process
        """
        self.repo_path = Path(repo_path)
        self.ignore_patterns = ignore_patterns or [
            'node_modules', '__pycache__', '.git', 'venv',
            'build', 'dist', '.pytest_cache'
        ]
        self.supported_extensions = supported_extensions or [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java',
            '.cpp', '.c', '.go', '.rs', '.md', '.txt'
        ]
        self.parser = CodeParser()
        self.stats = {
            'files_processed': 0,
            'chunks_created': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.ignore_patterns)
    
    def is_supported_file(self, path: Path) -> bool:
        """Check if file type is supported"""
        return path.suffix.lower() in self.supported_extensions
    
    def get_git_info(self) -> Dict:
        """Extract Git metadata from repository"""
        try:
            repo = Repo(self.repo_path)
            
            # Get latest commit info
            latest_commit = repo.head.commit
            
            return {
                'repo_name': self.repo_path.name,
                'branch': repo.active_branch.name,
                'latest_commit': {
                    'sha': latest_commit.hexsha[:8],
                    'author': str(latest_commit.author),
                    'date': datetime.fromtimestamp(latest_commit.committed_date),
                    'message': latest_commit.message.strip()
                },
                'remote_url': repo.remotes.origin.url if repo.remotes else None
            }
        except Exception as e:
            print(f"⚠️  Could not extract Git info: {e}")
            return {'repo_name': self.repo_path.name}
    
    def discover_files(self) -> List[Path]:
        """
        Discover all supported files in repository
        
        Returns:
            List of file paths to process
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                if self.is_supported_file(file_path) and not self.should_ignore(file_path):
                    files.append(file_path)
        
        print(f"📁 Discovered {len(files)} files")
        return files
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read file content with error handling
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as string, or None if error
        """
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 for binary files
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")
                self.stats['errors'] += 1
                return None
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_file(self, file_path: Path, git_info: Dict) -> List[CodeChunk]:
        """
        Process a single file into chunks
        
        Args:
            file_path: Path to file
            git_info: Repository metadata
            
        Returns:
            List of code chunks
        """
        content = self.read_file(file_path)
        if content is None:
            return []
        
        # Parse file into chunks
        relative_path = file_path.relative_to(self.repo_path)
        chunks = self.parser.parse_file(str(relative_path), content)
        
        # Enrich chunks with repository metadata
        for chunk in chunks:
            chunk.metadata.update({
                'repo_name': git_info.get('repo_name'),
                'full_path': str(file_path),
                'relative_path': str(relative_path),
                'file_size': len(content),
                'git_branch': git_info.get('branch'),
            })
        
        return chunks
    
    def ingest_repository(self) -> List[CodeChunk]:
        """
        Ingest entire repository
        
        Returns:
            List of all code chunks from repository
        """
        print(f"\n🚀 Starting repository ingestion: {self.repo_path}")
        self.stats['start_time'] = datetime.now()
        
        # Get repository metadata
        git_info = self.get_git_info()
        print(f"📦 Repository: {git_info.get('repo_name')}")
        if 'latest_commit' in git_info:
            print(f"🔗 Latest commit: {git_info['latest_commit']['sha']} "
                  f"by {git_info['latest_commit']['author']}")
        
        # Discover files
        files = self.discover_files()
        
        # Process all files
        all_chunks = []
        for i, file_path in enumerate(files, 1):
            if i % 50 == 0:
                print(f"⏳ Processing... {i}/{len(files)} files")
            
            chunks = self.process_file(file_path, git_info)
            all_chunks.extend(chunks)
            
            if chunks:
                self.stats['files_processed'] += 1
                self.stats['chunks_created'] += len(chunks)
        
        self.stats['end_time'] = datetime.now()
        self._print_summary()
        
        return all_chunks
    
    def _print_summary(self):
        """Print ingestion statistics"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("✅ INGESTION COMPLETE!")
        print("="*60)
        print(f"📊 Files processed: {self.stats['files_processed']}")
        print(f"📄 Chunks created: {self.stats['chunks_created']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"⚡ Speed: {self.stats['files_processed']/duration:.2f} files/sec")
        print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    # Test with a sample repository
    ingestion = RepositoryIngestion(
        repo_path=".",  # Current directory
        ignore_patterns=['node_modules', '__pycache__', 'venv'],
        supported_extensions=['.py', '.js', '.md']
    )
    
    chunks = ingestion.ingest_repository()
    
    # Show sample chunks
    print("\n📝 Sample chunks:")
    for chunk in chunks[:3]:
        print(f"\n{chunk.file_path} ({chunk.start_line}-{chunk.end_line}):")
        print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)