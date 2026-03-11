"""
DeepSeek LLM Interface via Ollama
Handles communication with local DeepSeek-Coder model
"""

import json
import requests
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structured LLM response"""
    content: str
    success: bool
    tokens_used: int
    processing_time: float


class DeepSeekInterface:
    """Interface to DeepSeek-Coder which is changed to llama-3 via Ollama"""
    
    def __init__(self, 
                 model_name: str = "llama3:latest",
                 ollama_url: str = "http://localhost:11434"):
        """
        Initialize llama-3 interface
        
        Args:
            model_name: Ollama model name
            ollama_url: Ollama API endpoint
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        
    def check_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(self.model_name in model.get('name', '') for model in models)
            return False
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False
    
    def generate(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.1,
                 max_tokens: int = 2000,
                 stop_sequences: Optional[List[str]] = None) -> LLMResponse:
        """
        Generate response from llama-3 model
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum response length
            stop_sequences: Sequences to stop generation
        
        Returns:
            LLMResponse with generated content
        """
        import time
        start_time = time.time()
        
        try:
            # Build full prompt with system instruction
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Prepare request
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            if stop_sequences:
                payload["options"]["stop"] = stop_sequences
            
            # Make request
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=120  # 2 min timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                
                processing_time = time.time() - start_time
                
                return LLMResponse(
                    content=content,
                    success=True,
                    tokens_used=result.get('eval_count', 0),
                    processing_time=processing_time
                )
            else:
                return LLMResponse(
                    content=f"Error: HTTP {response.status_code}",
                    success=False,
                    tokens_used=0,
                    processing_time=time.time() - start_time
                )
        
        except Exception as e:
            return LLMResponse(
                content=f"Error: {str(e)}",
                success=False,
                tokens_used=0,
                processing_time=time.time() - start_time
            )
    
    def generate_code(self,
                     description: str,
                     language: str = "python") -> LLMResponse:
        """
        Generate code from natural language description
        
        Args:
            description: Natural language description
            language: Programming language
        
        Returns:
            LLMResponse with generated code
        """
        system_prompt = f"""You are an expert {language} programmer specializing in scientific computing and numerical methods.
Generate clean, efficient, well-documented code.
Include necessary imports.
Add helpful comments.
Output ONLY the code, no explanations before or after."""
        
        prompt = f"""Generate {language} code for the following task:

{description}

Code:"""
        
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for code generation
            max_tokens=2000
        )
    
    def explain_equation(self, equation: str) -> LLMResponse:
        """
        Get mathematical explanation of an equation
        
        Args:
            equation: Mathematical equation
        
        Returns:
            LLMResponse with explanation
        """
        system_prompt = """You are a mathematics expert specializing in differential equations.
Provide clear, concise explanations suitable for students and researchers.
Focus on physical interpretation and mathematical properties."""
        
        prompt = f"""Explain the following differential equation:

{equation}

Provide:
1. Type and classification
2. Physical meaning (if applicable)
3. Key mathematical properties
4. Common applications

Explanation:"""
        
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )


def demo():
    """Demonstrate DeepSeek integration"""
    print("="*80)
    print("DEEPSEEK-CODER INTEGRATION TEST")
    print("="*80)
    print()
    
    # Initialize interface
    deepseek = DeepSeekInterface()
    
    # Check connection
    print("1. Checking Ollama connection...")
    if deepseek.check_connection():
        print("   ✓ Connected to Ollama")
        print(f"   ✓ Model '{deepseek.model_name}' available")
    else:
        print("   ✗ Cannot connect to Ollama")
        print("   Make sure Ollama is running: ollama serve")
        return
    
    print()
    
    # Test 1: Code generation
    print("2. Testing code generation...")
    print("   Task: Solve heat equation using finite differences")
    print()
    
    response = deepseek.generate_code(
        "Write a Python function to solve the 1D heat equation using finite difference method"
    )
    
    if response.success:
        print(f"   ✓ Generated code ({response.tokens_used} tokens, {response.processing_time:.2f}s)")
        print()
        print("   Generated Code:")
        print("   " + "-"*76)
        for line in response.content.split('\n')[:20]:  # Show first 20 lines
            print(f"   {line}")
        lines = response.content.split('\n')
        extra_lines = len(lines) - 20

        if len(lines) > 20:
            print(f"   ... ({extra_lines} more lines)")
        else:
            print(f"   ✗ Failed: {response.content}")
    
    print()
    
    # Test 2: Equation explanation
    print("3. Testing equation explanation...")
    equation = "x'' + 2*x' + x = 0"
    print(f"   Equation: {equation}")
    print()
    
    response = deepseek.explain_equation(equation)
    
    if response.success:
        print(f"   ✓ Generated explanation ({response.tokens_used} tokens, {response.processing_time:.2f}s)")
        print()
        print("   Explanation:")
        print("   " + "-"*76)
        for line in response.content.split('\n')[:15]:
            print(f"   {line}")
    else:
        print(f"   ✗ Failed: {response.content}")
    
    print()
    print("="*80)
    print("INTEGRATION TEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    demo()