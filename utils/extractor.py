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
import sys

# 将项目根目录添加到Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# 从app模块导入load_prompt_config
# 这将使用app.py中定义的、能够感知项目上下文的函数
from src.server.app import load_prompt_config

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")
ANALYSIS_MODEL = os.getenv("OPENAI_ANALYSIS_MODEL")
JSON_MODEL = os.getenv("OPENAI_JSON_MODEL")

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

def save_json_output(json_data: Dict[Any, Any], pmid: str, output_dir: str) -> str:
    """保存JSON数据到指定目录
    
    Args:
        json_data: 要保存的JSON数据
        pmid: 论文ID
        output_dir: 输出目录路径
        
    Returns:
        str: 输出文件的路径
    """
    output_path = os.path.join(output_dir, 'original_output.json')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return output_path

def process_paper(title: str, abstract: str, output_path: str, pmid: str, prompt_template: str, json_prompt_template: str) -> None:
    """处理论文，生成分析和JSON输出
    
    Args:
        title: 论文标题
        abstract: 论文摘要
        output_path: 输出文件路径
        pmid: 论文ID
        prompt_template: 用于分析的Prompt模板
        json_prompt_template: 用于生成JSON的Prompt模板
    """
    # Generate initial analysis
    analysis_result = generate_analysis(title, abstract, prompt_template) 
    
    if analysis_result["success"]:
        # Generate JSON from analysis
        json_result = generate_json(
            title=title,
            abstract=abstract,
            prompt_template=prompt_template,  
            analysis_output=analysis_result["response"],
            json_prompt_template=json_prompt_template
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
    # This standalone script execution needs a way to get project-specific prompts.
    # We will import app-level functions here for that purpose.
    from src.server.app import load_prompt_config, thread_local_data

    # Get the project from command line arguments or use default
    current_project = sys.argv[1] if len(sys.argv) > 1 else 'default'
    
    # Set the project context for this script execution
    thread_local_data.project_name = current_project
    print(f"Running extractor in standalone mode for project: {current_project}")

    title = "N6-methyladenosine demethylase FTO suppresses clear cell renal cell carcinoma through a novel FTO-PGC-1α signalling axis"
    abstract = "The abundant and reversible N6-methyladenosine (m6A) RNA modification and its modulators have important roles in regulating various gene expression and biological processes. Here, we demonstrate that fat mass and obesity associated (FTO), as an m6A demethylase, plays a critical anti-tumorigenic role in clear cell renal cell carcinoma (ccRCC). FTO is suppressed in ccRCC tissue. The low expression of FTO in human ccRCC correlates with increased tumour severity and poor patient survival. The Von Hippel-Lindau-deficient cells expressing FTO restores mitochondrial activity, induces oxidative stress and ROS production and shows impaired tumour growth, through increasing expression of PGC-1alpha by reducing m6A levels in its mRNA transcripts. Our work demonstrates the functional importance of the m6A methylation and its modulator, and uncovers a critical FTO-PGC-1alpha axis for developing effective therapeutic strategies in the treatment of ccRCC."
    
    # 使用项目目录下的测试路径
    test_dir = os.path.join(ROOT_DIR, 'projects', current_project, 'Main_dir', 'test')
    # 确保测试目录存在
    os.makedirs(test_dir, exist_ok=True)
    
    output_path = os.path.join(test_dir, 'original_output.json')
    pmid = "37456789"

    # Process the paper
    # Load prompts for the specified project
    prompt_config = load_prompt_config()
    prompt_template = prompt_config.get("PROMPT_TEMPLATE")
    json_prompt_template = prompt_config.get("JSON_PROMPT_TEMPLATE")
    
    process_paper(title, abstract, output_path, pmid, prompt_template, json_prompt_template)

    # Clean up the thread-local data
    del thread_local_data.project_name
    print("Standalone script execution finished.") 