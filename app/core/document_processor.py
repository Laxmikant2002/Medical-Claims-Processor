from typing import List, Dict, Any
import google.generativeai as genai
from app.agents.base import BaseAgent, DocumentType

class DocumentProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.agent = BaseAgent(api_key)
    
    async def process_documents(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process uploaded documents and return extracted information."""
        documents = []
        
        for file in files:
            content = await self.agent.extract_text_from_pdf(file["path"])
            doc_type = await self.agent.classify_document(content)
            
            doc_info = {
                "type": doc_type,
                "filename": file["filename"],
                "data": await self.agent.extract_info(content, doc_type)
            }
            documents.append(doc_info)
        
        # Validate documents
        validation_result = await self.agent.validate_documents(documents)
        
        return {
            "documents": documents,
            "validation": validation_result
        } 