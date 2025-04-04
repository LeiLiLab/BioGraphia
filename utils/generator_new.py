from openai import OpenAI
from typing import Dict, Any
import os
import json
from utils.graph_visualizer import generate_graph_from_json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import unittest
from unittest.mock import patch, MagicMock

def generate_analysis(title: str, abstract: str, prompt_template: str) -> Dict[Any, Any]:
    """
    Generate analysis using OpenAI API based on paper title and abstract
    
    Args:
        title (str): Paper title
        abstract (str): Paper abstract
        prompt_template (str): Template for the prompt with {title} and {abstract} placeholders
    
    Returns:
        Dict: Response from OpenAI API
    """
    # Set API key
    os.environ["OPENAI_API_KEY"] = "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"
    client = OpenAI()
    
    # Format the prompt in the specified format
    formatted_prompt = f"""
    {prompt_template}

    Title: {title}
    Abstract: {abstract}
    Answer:
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.,
            max_tokens=4096
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
    """
    Generate JSON structure from the analysis output using OpenAI API
    
    Args:
        title (str): Paper title
        abstract (str): Paper abstract
        prompt_template (str): Template for the prompt with {title} and {abstract} placeholders
        analysis_output (str): Output from the generate_analysis function
        json_prompt_template (str): Template for the JSON generation prompt
    
    Returns:
        Dict: JSON structure or error information
    """
    os.environ["OPENAI_API_KEY"] = "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"
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
            model="gpt-4o",
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
            
            # Add the analysis output to the JSON response
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
    """
    Save JSON output to a file
    
    Args:
        json_data (Dict): JSON data to save
        pmid (str): PMID to use as directory name
        output_dir (str): Base directory to save the JSON file
    
    Returns:
        str: Path to the saved file
    """
    # 使用传入的完整路径
    output_path = os.path.join(output_dir, 'original_output.json')
    
    # 保存 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return output_path

# Example usage:

    # Example prompt template - you can replace this with your own
PROMPT_TEMPLATE = """
Analyze the provided scientific abstract and extract the gene regulatory network (GRN). Your response should include the following:
	1.	Nodes (Genes/Proteins Involved): Identify the key molecules (e.g., genes, proteins, RNAs) mentioned in the abstract.
	2.	Edges (Regulatory Relationships): Specify how the nodes are connected, including activations, inhibitions, or modifications.
	3.	Summary of Regulatory Pathway: Provide a concise step-by-step explanation of the pathway described in the abstract.
	4.	Graph Representation: Describe the GRN as nodes and edges in textual format to allow visual representation. (in cases where the node might take on a negative state within its particular context. This requires an explicit notation to denote such negative states effectively.
Example:
METTL3 is upregulated in colorectal carcinoma (CRC) metastatic tissues and is correlated with poor prognosis.
* This could be annotated as:
    * dummy  → (+) METTL3)
	5. Context: Identify the primary context of the study, which refers to the broader biological setting, such as a specific disease (e.g., "breast cancer"), organism (e.g., "Arabidopsis thaliana"), or tissue type.

Title:

Epigallocatechin gallate targets FTO and inhibits adipogenesis in an mRNA m6A-YTHDF2-dependent manner

Abstract:

Background/objective: N6-methyladenosine (m6A) modification of mRNA plays a role in regulating adipogenesis. However, its underlying mechanism remains largely unknown. Epigallocatechin gallate (EGCG), the most abundant catechin in green tea, plays a critical role in anti-obesity and anti-adipogenesis. Methods: High-performance liquid chromatography coupled with triple-quadrupole tandem mass spectrometry (HPLC-QqQ-MS/MS) was performed to determine the m6A levels in 3T3-L1 preadipocytes. The effects of EGCG on the m6A levels in specific genes were determined by methylated RNA immunoprecipitation coupled with quantitative real-time PCR (meRIP-qPCR). Several adipogenesis makers and cell cycle genes were analyzed by quantitative real-time PCR (qPCR) and western blotting. Lipid accumulation was evaluated by oil red O staining. All measurements were performed at least for three times. Results: Here we showed that EGCG inhibited adipogenesis by blocking the mitotic clonal expansion (MCE) at the early stage of adipocyte differentiation. Exposing 3T3-L1 cells to EGCG reduced the expression of fat mass and obesity-associated (FTO) protein, an m6A demethylase, which led to increased overall levels of RNA m6A methylation. Cyclin A2 (CCNA2) and cyclin dependent kinase 2 (CDK2) play vital roles in MCE. The m6A levels of CCNA2 and CDK2 mRNA were dramatically enhanced by EGCG. Interestingly, EGCG increased the expression of YTH N6-methyladenosine RNA binding protein 2 (YTHDF2), which recognized and decayed methylated mRNAs, resulting in decreased protein levels of CCNA2 and CDK2. As a result, MCE was blocked and adipogenesis was inhibited. FTO overexpression and YTHDF2 knockdown in 3T3-L1 cells significantly increased CCNA2 and CDK2 protein levels and ameliorated the EGCG-induced adipogenesis inhibition. Thus, m6A-dependent CCNA2 and CDK2 expressions mediated by FTO and YTHDF2 contributed to EGCG-induced adipogenesis inhibition. Conclusion: Our findings provide mechanistic insights into how m6A is involved in the EGCG regulation of adipogenesis and shed light on its anti-obesity effect.

Answer:
**Nodes (Genes/Proteins Involved):**

    1.	EGCG: a catechin influencing adipogenesis

    2.	FTO: an m6A demethylase

    3.	m6A: N6-methyladenosine modification

    4.	YTHDF2: an m6A-binding protein

    5.	CCNA: Cyclin A2, involved in MCE

    6.	CDK2: Cyclin-dependent kinase 2, involved in MCE

    7.	MCE: mitotic clonal expansion

    8.	Adipogenesis: fat cell formation process

**Edges (Regulatory Relationships):**

    1.	EGCG upregulates YTHDF2.

    2.	EGCG downregulates FTO.

    3.	YTHDF2 recognizes m6A on CCNA and CDK2 and promotes their decay (when FTO is active).

    4.	m6A is on CCNA and CDK2.

    5.	CCNA and CDK2 are both associated with MCE.

    6.	EGCG blocks MCE.

    7.	MCE is associated with adipogenesis.

    8.	EGCG inhibits adipogenesis.

**Summary of Regulatory Pathway:**

EGCG reduces FTO levels, leading to higher m6A on CCNA and CDK2 mRNAs. At the same time, EGCG boosts YTHDF2, which targets these m6A-marked transcripts for degradation. Lower CCNA and CDK2 levels result in a block of MCE and, as a consequence, inhibit adipogenesis.

**Graph Representation:**

    EGCG → (upregulate) YTHDF2

    EGCG → (downregulate) FTO

    FTO → (reduce) m6A

    YTHDF2 → (recognize) m6A → (decay) CCNA, CDK2

    m6A → (is on) CCNA, CDK2

    CCNA → (associated with) MCE

    CDK2 → (associated with) MCE

    EGCG → (block) MCE

    MCE → (associated with) adipogenesis

    EGCG → (inhibit) adipogenesis

Context: 
	Adipogenesis.
    """
    

    
JSON_PROMPT_TEMPLATE = """
You are asked to output this json:
{"entities": [], "relations": []}

From a extracted graph representation:
The relations contains 

{
            "head": "",
            "tail": "",
            "label": "",
            "metaRelations": [], # there are hyper-relations behind regarding to m6A
            "text": "" # responding text in the abstract
        }


Include the node and entities that appeared in the edges and the entities list.
**Avoid Subtypes of a Node:** When a node includes specific subtypes or states, such as "geneA mRNA" or "GeneA protein," simplify it to the base biological entity (e.g., "GeneA") unless the subtype is critical to the relationship being described. Always prefer a single, unified representation.

Highlight intermediate mechanisms, such as how YTHDF2 interacts with m6A before affecting CCNA2 and CDK2 mRNA stability.

In order to remove redundancy and improve consistency and accuracy, we shall maintain all node states in the graph as positive, meaning some relations should be flipped compared to the original

Include all the relations.

The desired output for the previous one should be:
{
    "entities": [
        "EGCG",
        "YTHDF2",
        "FTO",
        "m6A",
        "CCNA2",
        "CDK2",
        "MCE",
        "adipogenesis"
    ],
    "relations": [
        {
            "head": "EGCG",
            "tail": "YTHDF2",
            "label": "upregulate",
            "metaRelations": [],
            "text": "Interestingly, EGCG increased the expression of YTH N6-methyladenosine RNA binding protein 2 (YTHDF2), which recognized and decayed methylated mRNAs, resulting in decreased protein levels of CCNA2 and CDK2."
        },
        {
            "head": "EGCG",
            "tail": "FTO",
            "label": "downregulate",
            "metaRelations": [],
            "text": "Exposing 3T3-L1 cells to EGCG reduced the expression of fat mass and obesity-associated (FTO) protein, an m6A demethylase, which led to increased overall levels of RNA m6A methylation."
        },
        {
            "head": "FTO",
            "tail": "m6A",
            "label": "reduce",
            "metaRelations": [],
            "text": "Exposing 3T3-L1 cells to EGCG reduced the expression of fat mass and obesity-associated (FTO) protein, an m6A demethylase, which led to increased overall levels of RNA m6A methylation."
        },
        {
            "head": "m6A",
            "tail": "CCNA2",
            "label": "is on",
            "metaRelations": [],
            "text": "The m6A levels of CCNA2 and CDK2 mRNA were dramatically enhanced by EGCG."
        },
        {
            "head": "m6A",
            "tail": "CDK2",
            "label": "is on",
            "metaRelations": [],
            "text": "The m6A levels of CCNA2 and CDK2 mRNA were dramatically enhanced by EGCG."
        },
        {
            "head": "YTHDF2",
            "tail": "m6A",
            "label": "recognize",
            "metaRelations": [
                { "target": "CCNA2", "label": "decay" },
                { "target": "CDK2", "label": "decay" }
            ],
            "text": "Interestingly, EGCG increased the expression of YTH N6-methyladenosine RNA binding protein 2 (YTHDF2), which recognized and decayed methylated mRNAs, resulting in decreased protein levels of CCNA2 and CDK2."
        },
        {
            "head": "CCNA2",
            "tail": "MCE",
            "label": "associated with",
            "metaRelations": [],
            "text": "Cyclin A2 (CCNA2) and cyclin dependent kinase 2 (CDK2) play vital roles in MCE."
        },
        {
            "head": "CDK2",
            "tail": "MCE",
            "label": "associated with",
            "metaRelations": [],
            "text": "Cyclin A2 (CCNA2) and cyclin dependent kinase 2 (CDK2) play vital roles in MCE."
        },
        {
            "head": "EGCG",
            "tail": "MCE",
            "label": "block",
            "metaRelations": [],
            "text": "Here we showed that EGCG inhibited adipogenesis by blocking the mitotic clonal expansion (MCE) at the early stage of adipocyte differentiation."
        },
        {
            "head": "MCE",
            "tail": "adipogenesis",
            "label": "associated with",
            "metaRelations": [],
            "text": "Here we showed that EGCG inhibited adipogenesis by blocking the mitotic clonal expansion (MCE) at the early stage of adipocyte differentiation."
        },
        {
            "head": "EGCG",
            "tail": "adipogenesis",
            "label": "inhibit",
            "metaRelations": [],
            "text": "Here we showed that EGCG inhibited adipogenesis by blocking the mitotic clonal expansion (MCE) at the early stage of adipocyte differentiation."
        }
    ]
}

Please follow the above instructions and example to finish the JSON output for the second one. Generate only JSON code without any additional text or explanations.”
    """
def process_paper(title: str, abstract: str, output_path: str, pmid: str) -> None:
    # Generate initial analysis
    analysis_result = generate_analysis(title, abstract, PROMPT_TEMPLATE)
    
    if analysis_result["success"]:
        # Generate JSON from analysis
        json_result = generate_json(
            title=title,
            abstract=abstract,
            prompt_template=PROMPT_TEMPLATE,
            analysis_output=analysis_result["response"],
            json_prompt_template=JSON_PROMPT_TEMPLATE
        )
        
        if json_result["success"]:
            # Save JSON to file
            output_dir = os.path.dirname(output_path)
            json_file = save_json_output(json_result["response"], pmid, output_dir)
            print(f"JSON saved to: {json_file}")
            
            # 生成并保存原始图形
            original_graph_path = os.path.join(output_dir, 'original_graph.html')
            generate_graph_from_json(json_result["response"], original_graph_path)
            print(f"Original graph saved to: {original_graph_path}")
            
            print("\nJSON content:")
            print(json.dumps(json_result["response"], indent=2))
        else:
            print("JSON generation failed:", json_result["error"])
    else:
        print("Analysis failed:", analysis_result["error"])


if __name__ == "__main__":
    title = "N6-methyladenosine demethylase FTO suppresses clear cell renal cell carcinoma through a novel FTO-PGC-1α signalling axis"
    abstract = "The abundant and reversible N6-methyladenosine (m6A) RNA modification and its modulators have important roles in regulating various gene expression and biological processes. Here, we demonstrate that fat mass and obesity associated (FTO), as an m6A demethylase, plays a critical anti-tumorigenic role in clear cell renal cell carcinoma (ccRCC). FTO is suppressed in ccRCC tissue. The low expression of FTO in human ccRCC correlates with increased tumour severity and poor patient survival. The Von Hippel-Lindau-deficient cells expressing FTO restores mitochondrial activity, induces oxidative stress and ROS production and shows impaired tumour growth, through increasing expression of PGC-1alpha by reducing m6A levels in its mRNA transcripts. Our work demonstrates the functional importance of the m6A methylation and its modulator, and uncovers a critical FTO-PGC-1alpha axis for developing effective therapeutic strategies in the treatment of ccRCC."
    output_path = "data/output.json"
    pmid = "37456789"
    process_paper(title, abstract, output_path, pmid)
