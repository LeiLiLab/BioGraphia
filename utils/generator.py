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
            model="o1",
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
Your task is constructing a pathway graph of the molecular regulatory mechanism in a given scientific journal abstract. You can refer the background, introduction, experiment, future applications or any other unnecessary details in the abstract if they give additional information. However, they should not be included if they are not related to molecular regulatory mechanism directly. Keep in mind that your task is identifying interactions in terms of molecular regulatory mechanism/pathway. Do not use any jargons or obscure representations. Follow these rules:


* Nodes: Identify the key entities involved in pathway. Identify node types such as gene, protein, biological process, chemical compound, medicine or drug, disease, clinical phenotype. Do not use acronym for nodes. Identify a context specific node status if it is provided in the asbtract. Report "NULL" if a node does not have a context specific status.  

* Edges (Regulatory Relationships): Specify how the nodes are connected, including activations, inhibitions, or modifications. All relation should be considered when the node is in neutral or at least in positive status. Use meta-relation if and only if for the relations associated with m6A RNA modification. If a molecule (e.g., YTH N6-methyladenosine RNA binding protein 2) should bind with N6-methyladenosine and this binding leads to an effect on another entity (e.g., Cyclin A2), then this effect should be captured using a meta-relation under binding relation. A lot of times the binding is implicit in the text.
Please include N6-methyladenosine is on .. as a seperate relation when it appears and do not use meta-relation for it. 
When a molecule interacts with N6-methyladenosine, and this interaction influences another target (e.g., Cyclin A2), this indirect effect should be captured using meta-relation.

*  Summary of Regulatory Pathway: Provide a concise step-by-step explanation of the pathway described in the abstract.

*  Context: A molecular regulatory pathway is assigned a **specific context** if the mechanism is explicitly linked to a defined biological condition that affects or is affected by the mechanism. The classification follows these strict guidelines:  

1. **Disease Model Context:**  
   The mechanism is studied in relation to a specific disease, such as cancer, obesity, diabetes, or neurodegeneration.  
   **Example:**  
   *(A pathway regulating breast cancer cell metabolism → Context: "Breast Cancer", Type: "Disease")*  

2. **Cell/Tissue/Organism-Specific Context:**  
   The mechanism is examined within a specific cell type, primary tissue, organoid, or in vivo model.  
   **Example:**  
   *(A molecular mechanism studied in liver organoids with defined metabolic alterations → Context: "Liver Organoid", Type: "Tissue-Specific")*  

3. **Pathological or Environmental Condition Context:**  
   The mechanism is analyzed under specific stress conditions such as hypoxia, oxidative stress, inflammation, drug treatment in a disease model, or toxin exposure.  
   **Example:**  
   *(Oxidative stress regulates a molecular mechanism in neurons → Context: "Oxidative Stress", Type: "Environmental Condition")*  

4. **NULL Context:**  
   The mechanism is **not explicitly linked** to a biological condition. It is classified as **"NULL"** under the following scenarios:  

   - The mechanism is studied in general biological processes such as normal cell differentiation, gene expression, or metabolism without a disease or stress-related association.  
   **Example:**  
   *(A molecular mechanism in adipogenesis without linking it to obesity or other conditions → Context: "NULL", Type: "General Biological Process")*  

   - The mechanism is performed in immortalized cell lines (e.g., 3T3-L1, HeLa, HEK293) **without a disease or stress-related perturbation**.  
   **Example:**  
   *(A molecular mechanism regulating mRNA modifications in HEK293 cells without linking it to another condition → Context: "NULL", Type: "Immortalized Cell Line")*  

   - The mechanism examines the effect of a molecule (e.g., drug, natural compound) but does not associate the mechanism with a specific biological condition.  
   **Example:**  
   *(Context: "NULL", Type: "Molecule Effect Without Condition")*  


Title:

FTO regulates the chemo-radiotherapy resistance of cervical squamous cell carcinoma (CSCC) by targeting β-catenin through mRNA demethylation

Abstract: 

The role of N6-methyladenosine (m6A) demethylase fat mass and obesity-associated protein (FTO) in the regulation of chemo-radiotherapy resistance remains largely unknown. Here, we show that the mRNA level of FTO is elevated in cervical squamous cell carcinoma (CSCC) tissues when compared with respective adjacent normal tissues. FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts and in turn increases excision repair cross-complementation group 1 (ERCC1) activity. Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples. Taken together, these findings uncover a critical function for FTO and its substrate m6A in the regulation of chemo-radiotherapy resistance, which may bear potential clinical implications for CSCC treatment.

Answer:

Context:
The molecular mechanism is explicitly connected to cervical squamous cell carcinoma (CSCC) and therapy resistance, making the context cervical squamous cell carcinoma, classified under cancer.
(Context: “Cervical Squamous Cell Carcinoma”, Type: “Cancer”)

Nodes:
	1.	Fat mass and obesity-associated protein (FTO) – Gene, upregulated in cervical squamous cell carcinoma.
	2.	N6-methyladenosine (m6A) – RNA modification, NULL status.
	3.	Beta-catenin – Protein, NULL status.
	4.	Excision repair cross-complementation group 1 (ERCC1) – Gene, NULL status.
	5.	Chemo-radiotherapy resistance – Treatment response, NULL status.
	6.	Survival – Clinical phenotype, NULL status.

Regulatory relationships:
	1. fat mass and obesity-associated protein reduces N6-methyladenosine
	2. fat mass and obesity-associated protein upregulates beta-catenin: this is meta-relation associated with m6A RNA modification mechanism. The upregulation of beta-catenin is a following result of demethylation process of m6A by FTO.
	3. N6-methyladenosine is on beta-catenin mRNA transcripts
	4. beta-catenin increases the activity of excision repair cross-complementation group 1
	5. excision repair cross-complementation group 1 enhances chemo-radiotherapy resistance 
	6. chemo-radiotherapy resistance affects survival
	7. fat mass and obesity-associated protein enhances chemo-radiotherapy resistance 
	8. fat mass and obesity-associated protein affects surviaval
	
Summary of Regulatory Pathway:
This pathway demonstrates how FTO-mediated m6A RNA demethylation contributes to chemo-radiotherapy resistance in cervical squamous cell carcinoma by upregulating beta-catenin and activating ERCC1. The pathway directly affects patient survival and suggests a potential target for clinical intervention in CSCC treatment.

Graph Representation:
Nodes:
	•	Fat mass and obesity-associated protein – Gene (Upregulated)
	•	N6-methyladenosine – RNA Modification (NULL)
	•	Beta-catenin – Protein (NULL)
	•	Excision repair cross-complementation group 1 – Gene (NULL)
	•	Chemo-radiotherapy resistance – Treatment response (NULL)
	•	Survival – Clinical phenotype (NULL)

	Edges:
	•	Fat mass and obesity-associated protein → (reduce) N6-methyladenosine → (upregulate) beta-catenin
	•	N6-methyladenosine → (is on) beta-catenin
	•	Beta-catenin → (increase) excision repair cross-complementation group 1
	•	Excision repair cross-complementation group 1 → (enhance) Chemo-radiotherapy resistance
	•	Chemo-radiotherapy resistance → (affect) Surviaval
	•	Fat mass and obesity-associated protein → (enhance) Chemo-radiotherapy resistance
	•	Fat mass and obesity-associated protein → (affect) Surviaval
    """
    

    
JSON_PROMPT_TEMPLATE = """
You are asked to output this json:
{"context": [], "entities": [], "relations": []}

From a extracted graph representation:
The relations contains 

{        
            "head": "",
            "tail": "",
            "label": "",
            "metaRelations": [], # there are hyper-relations behind 
            "text": "" # responding text in the abstract
        }


Include the node and entities that appeared in the edges and the entities list.

In order to remove redundancy and improve consistency and accuracy, we shall maintain all node states in the graph as positive, meaning some relations should be flipped compared to the original

Include all the relations.

The desired output for the previous one should be:
{   "context": [
        {
            "name": "Cervical Squamous Cell Carcinoma",
            "type": "Cancer"
        }
    "entities": [
        "Fat mass and obesity-associated protein",
        "N6-methyladenosine",
        "Beta-catenin",
        "Excision repair cross-complementation group 1",
        "Chemo-radiotherapy resistance – Treatment response",
        "Survival"
    ],
    "relations": [
		    {
            "head": "Fat mass and obesity-associated protein",
            "tail": "N6-methyladenosine",
            "label": "reduces",
            "metaRelations": [
            {"target": "beta-catenin", "label": "upregulate"}
            ],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts."
        },
        {
            "head": "N6-methyladenosine",
            "tail": "beta-catenin",
            "label": "is on",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts and in turn increases excision repair cross-complementation group 1 (ERCC1) activity."
        },
        {
            "head": "Beta-catenin",
            "tail": "Excision repair cross-complementation group 1",
            "label": "increase",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts."
        },
        {
            "head": "Excision repair cross-complementation group 1",
            "tail": "Chemo-radiotherapy resistance",
            "label": "enhance",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts and in turn increases excision repair cross-complementation group 1 (ERCC1) activity."
        },
        {
            "head": "Chemo-radiotherapy resistance",
            "tail": "Surviaval",
            "label": "affect",
            "metaRelations": [],
            "text": "Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples."
        },
        {
            "head": "Fat mass and obesity-associated protein",
            "tail": "Chemo-radiotherapy resistance",
            "label": "enhance",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo."
        },
        {
            "head": "Fat mass and obesity-associated protein",
            "tail": "Surviaval",
            "label": "affect",
            "metaRelations": [],
            "text": "Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples."
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