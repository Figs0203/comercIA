import os
import json
import requests
from dotenv import load_dotenv
from django.conf import settings

class GeminiProcessor:
    def __init__(self):
        # Load the environment variables
        load_dotenv('GEMINI_API_KEY.env')
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = "gemini-1.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        
    def process_query(self, query):
        """
        Process a natural language query and extract relevant search keywords
        
        Args:
            query (str): The natural language query from the user
            
        Returns:
            dict: A dictionary with success status and processed keywords or error message
        """
        try:
            # Construct the prompt for Gemini API
            prompt = f"""
            Eres un asistente que convierte consultas en lenguaje natural a palabras clave relevantes para búsqueda de productos.
            
            Consulta: "{query}" 
            
            Tu tarea es:
            1. Identificar la intención principal del usuario
            2. Extraer 3-5 palabras clave relevantes para buscar en una base de datos de productos
            3. Responder SOLAMENTE con estas palabras clave separadas por comas
            
            Por ejemplo:
            - Para "¿Dónde puedo encontrar cuadernos ecológicos?", responderías: "cuadernos, ecológicos, sostenibles, papelería"
            - Para "Busco comida rápida cerca de mí", responderías: "comida rápida, snacks, frituras, comida"
            """
            
            # Prepare the request payload
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 100,
                }
            }
            
            # Send request to Gemini API
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key
                },
                json=payload
            )
            
            # Parse the response
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    content = data["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        keywords = content["parts"][0]["text"].strip()
                        # Clean up any unnecessary formatting
                        keywords = keywords.replace("\n", "").replace("```", "").strip()
                        return {
                            "success": True,
                            "keywords": keywords
                        }
            
            # If we reach here, something went wrong in the response parsing
            return {
                "success": False,
                "error": "No se pudieron procesar los resultados de la API"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 