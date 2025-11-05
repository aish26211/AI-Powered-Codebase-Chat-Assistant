"""
RAG Engine - Retrieval Augmented Generation for Code
Combines vector search with LLM generation
"""

from typing import List, Dict, Optional
from anthropic import Anthropic
from groq import Groq
import sys
from pathlib import Path
from .vector_store import VectorStore

class RAGEngine:
    """RAG-powered code assistant"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "groq"
    ):
        """
        Initialize RAG engine
        
        Args:
            vector_store: VectorStore instance
            api_key: API key
            model: Model name (optional)
            provider: "groq" or "anthropic"
        """
        self.vector_store = vector_store
        self.provider = provider
        
        if provider == "groq":
            self.client = Groq(api_key=api_key)
            self.model = model or "llama-3.3-70b-versatile"
            print(f"🤖 RAG Engine initialized with Groq ({self.model})")
        else:
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-sonnet-4-5-20250929"
            print(f"🤖 RAG Engine initialized with Anthropic ({self.model})")
    
    def retrieve_context(
        self,
        query: str,
        n_results: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Retrieve relevant code chunks for query
        
        Args:
            query: User query
            n_results: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant code chunks
        """
        results = self.vector_store.search(query, n_results=n_results)
        
        # Filter by similarity threshold
        filtered = [r for r in results if r['similarity_score'] >= similarity_threshold]
        
        return filtered
    
    def format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context for LLM
        
        Args:
            chunks: List of retrieved code chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant code found in the repository."
        
        context_parts = []
        context_parts.append("Here are the most relevant code snippets from the repository:\n")
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            file_path = metadata.get('file_path', 'unknown')
            start_line = metadata.get('start_line', '?')
            end_line = metadata.get('end_line', '?')
            language = metadata.get('language', 'unknown')
            similarity = chunk['similarity_score']
            
            context_parts.append(f"\n--- Snippet {i} (Relevance: {similarity:.2%}) ---")
            context_parts.append(f"File: {file_path}")
            context_parts.append(f"Lines: {start_line}-{end_line}")
            context_parts.append(f"Language: {language}")
            context_parts.append(f"\n```{language}")
            context_parts.append(chunk['content'])
            context_parts.append("```\n")
        
        return "\n".join(context_parts)
    
    def create_prompt(self, query: str, context: str) -> str:
        """
        Create prompt for LLM
        
        Args:
            query: User query
            context: Retrieved code context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are an expert code assistant helping developers understand their codebase. 
You have access to code from their repository.

CONTEXT FROM REPOSITORY:
{context}

USER QUESTION:
{query}

Please provide a clear, helpful answer based on the code provided above. 

Guidelines:
- Reference specific files and line numbers when relevant
- Explain the code logic clearly
- If the context doesn't contain enough information, say so
- Suggest related files or areas to explore if helpful
- Use code examples from the context when explaining
- Be concise but thorough

Answer:"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate response using LLM
        
        Args:
            prompt: Formatted prompt with context
            
        Returns:
            LLM response
        """
        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            return response.choices[0].message.content
        else:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
    
    def query(
        self,
        question: str,
        n_results: int = 5,
        similarity_threshold: float = 0.3
    ) -> Dict:
        """
        Main query method - retrieves context and generates answer
        
        Args:
            question: User question
            n_results: Number of code chunks to retrieve
            similarity_threshold: Minimum similarity for retrieval
            
        Returns:
            Dictionary with answer and retrieved context
        """
        print(f"\n🔍 Processing query: {question}")
        
        # Step 1: Retrieve relevant code
        print("  📚 Retrieving relevant code...")
        chunks = self.retrieve_context(question, n_results, similarity_threshold)
        print(f"  ✅ Found {len(chunks)} relevant snippets")
        
        # Step 2: Format context
        context = self.format_context(chunks)
        
        # Step 3: Create prompt
        prompt = self.create_prompt(question, context)
        
        # Step 4: Generate response
        print("  🤖 Generating answer...")
        answer = self.generate_response(prompt)
        print("  ✅ Answer generated")
        
        return {
            'question': question,
            'answer': answer,
            'sources': [
                {
                    'file': chunk['metadata'].get('file_path'),
                    'lines': f"{chunk['metadata'].get('start_line')}-{chunk['metadata'].get('end_line')}",
                    'similarity': chunk['similarity_score']
                }
                for chunk in chunks
            ],
            'num_sources': len(chunks)
        }
    
    def chat(
        self,
        conversation_history: List[Dict],
        n_results: int = 5
    ) -> Dict:
        """
        Handle multi-turn conversations with context
        """
        latest_message = conversation_history[-1]['content']
        chunks = self.retrieve_context(latest_message, n_results=n_results)
        context = self.format_context(chunks)
        
        system_message = f"""You are an expert code assistant. You have access to the user's codebase.

CURRENT CODEBASE CONTEXT:
{context}

Use this context to answer the user's questions about their code."""
        
        if self.provider == "groq":
            messages = [
                {"role": "system", "content": system_message}
            ] + conversation_history
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            answer = response.choices[0].message.content
        else:
            full_conversation = [
                {"role": "user", "content": system_message}
            ] + conversation_history
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=full_conversation
            )
            answer = message.content[0].text
        
        return {
            'answer': answer,
            'sources': [chunk['metadata'].get('file_path') for chunk in chunks]
        }