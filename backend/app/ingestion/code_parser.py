"""
Code Parser - Intelligently parse and chunk source code files
Uses tree-sitter for syntax-aware parsing
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from tree_sitter import Language, Parser

@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    chunk_type: str  # 'function', 'class', 'block', or 'file'
    metadata: Dict

class CodeParser:
    """Parse source code files into semantic chunks"""
    
    def __init__(self):
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
        }
    
    def get_language(self, file_path: str) -> Optional[str]:
        """Determine programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.language_map.get(ext)
    
    def parse_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """
        Parse a file into semantic chunks
        
        Args:
            file_path: Path to the file
            content: File content as string
            
        Returns:
            List of CodeChunk objects
        """
        language = self.get_language(file_path)
        
        # For non-code files or unsupported languages, use simple chunking
        if not language:
            return self._simple_chunk(file_path, content)
        
        try:
            # Use tree-sitter for syntax-aware parsing
            return self._syntax_aware_chunk(file_path, content, language)
        except Exception as e:
            print(f"⚠️  Syntax parsing failed for {file_path}, using simple chunking: {e}")
            return self._simple_chunk(file_path, content)
    
    def _syntax_aware_chunk(
        self, 
        file_path: str, 
        content: str, 
        language: str
    ) -> List[CodeChunk]:
        """Parse code using tree-sitter for semantic chunking"""
        chunks = []
        
        try:
            # Initialize tree-sitter parser
            parser = Parser()
            
            # Build and load language library (cached after first build)
            build_dir = os.path.join(os.path.dirname(__file__), "build")
            os.makedirs(build_dir, exist_ok=True)
            lib_path = os.path.join(build_dir, f"{language}.so")
            
            if not os.path.exists(lib_path):
                try:
                    Language.build_library(
                        lib_path,
                        [os.path.expanduser(f"~/.tree-sitter/tree-sitter-{language}")]
                    )
                except:
                    print(f"Failed to build language grammar for {language}")
                    raise
            
            lang = Language(lib_path, language)
            parser.set_language(lang)
            tree = parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Extract functions and classes
            chunks.extend(self._extract_definitions(
                root_node, content, file_path, language
            ))
            
            # If no chunks found, fall back to simple chunking
            if not chunks:
                return self._simple_chunk(file_path, content)
                
        except Exception as e:
            print(f"Tree-sitter parsing error: {e}")
            return self._simple_chunk(file_path, content)
        
        return chunks
    
    def _extract_definitions(
        self, 
        node, 
        content: str, 
        file_path: str, 
        language: str
    ) -> List[CodeChunk]:
        """Extract function and class definitions from AST"""
        chunks = []
        
        # Node types to extract (varies by language)
        target_types = {
            'python': ['function_definition', 'class_definition'],
            'javascript': ['function_declaration', 'class_declaration', 'method_definition'],
            'typescript': ['function_declaration', 'class_declaration', 'method_definition'],
            'java': ['method_declaration', 'class_declaration'],
            'go': ['function_declaration', 'method_declaration'],
        }
        
        targets = target_types.get(language, ['function_definition', 'class_definition'])
        
        def traverse(node):
            """Recursively traverse AST"""
            if node.type in targets:
                # Extract the code for this definition
                start_byte = node.start_byte
                end_byte = node.end_byte
                code = content[start_byte:end_byte]
                
                # Get name if available
                name = self._get_node_name(node)
                
                chunks.append(CodeChunk(
                    content=code,
                    file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    language=language,
                    chunk_type=node.type,
                    metadata={
                        'name': name,
                        'type': node.type,
                        'lines': node.end_point[0] - node.start_point[0] + 1
                    }
                ))
            
            # Continue traversing
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return chunks
    
    def _get_node_name(self, node) -> str:
        """Extract name from a definition node"""
        for child in node.children:
            if child.type == 'identifier' or child.type == 'name':
                return child.text.decode('utf8')
        return "anonymous"
    
    def _simple_chunk(self, file_path: str, content: str, chunk_size: int = 1000) -> List[CodeChunk]:
        """
        Simple line-based chunking for non-code files or fallback
        
        Args:
            file_path: Path to file
            content: File content
            chunk_size: Target chunk size in characters
        """
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            line_size = len(line)
            
            if current_size + line_size > chunk_size and current_chunk:
                # Create chunk from accumulated lines
                chunks.append(CodeChunk(
                    content='\n'.join(current_chunk),
                    file_path=file_path,
                    start_line=start_line,
                    end_line=i - 1,
                    language='text',
                    chunk_type='block',
                    metadata={'lines': len(current_chunk)}
                ))
                current_chunk = []
                current_size = 0
                start_line = i
            
            current_chunk.append(line)
            current_size += line_size
        
        # Add remaining content
        if current_chunk:
            chunks.append(CodeChunk(
                content='\n'.join(current_chunk),
                file_path=file_path,
                start_line=start_line,
                end_line=len(lines),
                language='text',
                chunk_type='block',
                metadata={'lines': len(current_chunk)}
            ))
        
        return chunks


# Test the parser
if __name__ == "__main__":
    parser = CodeParser()
    
    # Test Python code
    test_code = '''
def calculate_sum(a, b):
    """Add two numbers"""
    return a + b

class Calculator:
    def multiply(self, x, y):
        """Multiply two numbers"""
        return x * y
'''
    
    chunks = parser.parse_file("test.py", test_code)
    print(f"✅ Parsed {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  - {chunk.chunk_type}: {chunk.metadata.get('name', 'N/A')} "
              f"(lines {chunk.start_line}-{chunk.end_line})")