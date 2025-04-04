from openai import OpenAI
from typing import Dict, Any
import os
import json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import unittest
from unittest.mock import patch, MagicMock
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")
ANALYSIS_MODEL = os.getenv("OPENAI_ANALYSIS_MODEL")
JSON_MODEL = os.getenv("OPENAI_JSON_MODEL")

# Load prompt templates from JSON file
with open('data/prompt.json', 'r', encoding='utf-8') as f:
    prompts = json.load(f)
    PROMPT_TEMPLATE_1 = prompts['PROMPT_TEMPLATE']
    PROMPT_TEMPLATE_2 = prompts['JSON_PROMPT_TEMPLATE']

def generate_analysis(title: str, abstract: str, prompt_template: str) -> Dict[Any, Any]:
    # Set API key from config
    os.environ["OPENAI_API_KEY"] = API_KEY
    client = OpenAI()
    formatted_prompt = f"""
    {prompt_template}

    Title: {title}
    Abstract: {abstract}
    Answer:
    """
    try:
        completion = client.chat.completions.create(
            model=ANALYSIS_MODEL,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ],
        )
        
        # Extract the response content
        response = completion.choices[0].message.content
        
        return {
            "success": True,
            "response": response,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "error": str(e)
        }

def generate_json(title: str, abstract: str, prompt_template: str, analysis_output: str, json_prompt_template: str) -> Dict[Any, Any]:
    os.environ["OPENAI_API_KEY"] = API_KEY
    client = OpenAI()
    
    formatted_prompt = f"""
    {prompt_template}

    Title: {title}
    Abstract: {abstract}
    Answer: {analysis_output}

    {json_prompt_template}
    
    IMPORTANT: Your response must be valid JSON only. Do not include any explanatory text.
    The response should start with '{{' and end with '}}' and follow proper JSON format.
    """

    try:
        completion = client.chat.completions.create(
            model=JSON_MODEL,
            messages=[
                {"role": "system", "content": "You are a JSON formatting assistant. Always respond with valid JSON only."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.0,
            max_tokens=4096
        )
        
        response = completion.choices[0].message.content.strip()
        
        # Try to parse the response as JSON
        try:
            # Remove any potential markdown code block syntax
            if response.startswith("```json"):
                response = response.split("```json")[1]
            if response.startswith("```"):
                response = response.split("```")[1]
            if response.endswith("```"):
                response = response.rsplit("```", 1)[0]
                
            response = response.strip()
            
            json_response = json.loads(response)
            
            # Add the cleaned analysis output to the JSON response
            # Extract only the textual part of the analysis, removing the JSON part
            import re
            # Pattern to match everything before the "Constructed Pathway Graph (JSON):" line
            text_only_pattern = re.compile(r'(.*?)(?:Constructed Pathway Graph \(JSON\):)', re.DOTALL)
            text_match = text_only_pattern.search(analysis_output)
            
            if text_match:
                # Use only the textual analysis part
                json_response["analysis"] = text_match.group(1).strip()
            else:
                # If pattern not found, use the original output
                json_response["analysis"] = analysis_output
            
            return {
                "success": True,
                "response": json_response,
                "error": None
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "response": response,
                "error": f"Failed to parse JSON: {str(e)}\nResponse received: {response}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "error": str(e)
        }

def save_json_output(json_data: Dict[Any, Any], pmid: str, output_dir: str = "data") -> str:
    output_path = os.path.join(output_dir, 'original_output.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return output_path

def process_paper(title: str, abstract: str, output_path: str, pmid: str) -> None:
    # Generate initial analysis
    analysis_result = generate_analysis(title, abstract, PROMPT_TEMPLATE_1) 
    
    if analysis_result["success"]:
        # Generate JSON from analysis
        json_result = generate_json(
            title=title,
            abstract=abstract,
            prompt_template=PROMPT_TEMPLATE_1,  
            analysis_output=analysis_result["response"],
            json_prompt_template=PROMPT_TEMPLATE_2  
        )
        
        if json_result["success"]:
            # Save JSON to file
            output_dir = os.path.dirname(output_path)
            json_file = save_json_output(json_result["response"], pmid, output_dir)
            print(f"JSON saved to: {json_file}")
        else:
            print("JSON generation failed:", json_result["error"])
    else:
        print("Analysis failed:", analysis_result["error"])

if __name__ == "__main__":
    title = "N6-methyladenosine demethylase FTO suppresses clear cell renal cell carcinoma through a novel FTO-PGC-1α signalling axis"
    abstract = "The abundant and reversible N6-methyladenosine (m6A) RNA modification and its modulators have important roles in regulating various gene expression and biological processes. Here, we demonstrate that fat mass and obesity associated (FTO), as an m6A demethylase, plays a critical anti-tumorigenic role in clear cell renal cell carcinoma (ccRCC). FTO is suppressed in ccRCC tissue. The low expression of FTO in human ccRCC correlates with increased tumour severity and poor patient survival. The Von Hippel-Lindau-deficient cells expressing FTO restores mitochondrial activity, induces oxidative stress and ROS production and shows impaired tumour growth, through increasing expression of PGC-1alpha by reducing m6A levels in its mRNA transcripts. Our work demonstrates the functional importance of the m6A methylation and its modulator, and uncovers a critical FTO-PGC-1alpha axis for developing effective therapeutic strategies in the treatment of ccRCC."
    output_path = "data/debug"
    pmid = "37456789"
    process_paper(title, abstract, output_path, pmid) 