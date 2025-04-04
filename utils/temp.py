import json

def write_json(prompt_template, json_prompt_template, filename="data/prompt.json"):
    data = {
        "PROMPT_TEMPLATE": prompt_template,
        "JSON_PROMPT_TEMPLATE": json_prompt_template
    }
    
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Fill in the content here
prompt_template = """
Your task is to construct a pathway graph representing the molecular regulatory mechanism described in a given scientific journal abstract. Follow these specific instructions carefully:

1. Context Identification (Strict Rules Apply)
Determine the context only if the molecular mechanism is explicitly linked to a defined biological condition. The context must fall into one of the following three categories:

Disease: The study explicitly states that the molecular mechanism is investigated in the context of a disease model (e.g., cancer, obesity, diabetes, neurodegenerative disease).

Cell/Tissue: The study is conducted in primary cells, tissues, organoids, or an in vivo model. Standard immortalized cell lines alone do not qualify.

Pathological/Environmental Stress: The study examines the pathway under a disease-related stress condition (e.g., hypoxia, oxidative stress, inflammation, drug treatment). Generic stress in standard cell cultures does not qualify.

Strict Context Assignment Rules
1. No context assignment for standard cell line studies: If the study only uses immortalized cell lines without explicitly linking findings to a disease or stress condition, assign context = NULL
2. Do not assume disease relevance: If the study does not explicitly mention a disease model, do not infer a disease association.
3. Do not assume a biological process is a disease: If the study investigates a normal biological process (e.g., adipogenesis, differentiation) without linking it to a disease, assign context = NULL.
4. Drug/Treatment Studies Must Be in a Disease Model: If the study examines the effects of a compound (e.g., chemotherapy, small molecules) but does not specify a disease model, assign context = NULL.

Final Validation Step for Context:
If context ≠ NULL, the study must clearly fit one of the three categories.
If context = NULL, no assumptions should be made about disease relevance.


Examples
Correct Context Assignment:
"m6A demethylation promotes breast cancer cell proliferation." → Context: breast cancer, Context Type: disease
"Hypoxia enhances glycolysis in glioblastoma cells." → Context: glioblastoma, Context Type: disease
"Obesity induces FTO overexpression in adipose tissue." → Context: obesity, Context Type: disease
"m6A modification regulates differentiation in mouse primary muscle tissue." → Context: muscle tissue, Context Type: cell/tissue

Incorrect Context Assignment:
"m6A regulates mRNA modifications in HEK293 cells." → Context: NULL, Context Type: NULL (No explicit disease or stress condition)
"Epigallocatechin gallate inhibits adipogenesis in 3T3-L1 cells." → Context: NULL, Context Type: NULL (Adipogenesis is not a disease, and no disease is mentioned)
"Oxidative stress alters gene expression in fibroblast cultures." → Context: NULL, Context Type: NULL (Pathological stress but no disease model)


2. Node Identification (Classification Required)
Identify all key molecular entities involved in the pathway. Each node should be classified as one of the following types:

Gene
Protein
Biological Process
Chemical Compound
RNA Modification
Medicine or Drug
Disease
Clinical Phenotype

3. Context-Specific Node Status (Strict Rule Enforcement)
Critical Rule: Context-Specific Status Can Exist Only if Context ≠ NULL
If context = NULL, then all nodes must have status = NULL.
If context ≠ NULL, a context-specific status can be assigned only if the study explicitly confirms an observed status (e.g., "Gene X is upregulated in cancer cells").
Do not assign a context-specific status if the study does not specify an observed expression levels or expression changes under the given condition.

Final Validation Step for Node Status:
If context = NULL, all nodes must have status = NULL (no exceptions).
If any node has a status other than NULL, the study must have an assigned context.


4. Regulatory Relationships (Edges)
Clearly define how nodes interact in the pathway using direct regulatory relationships.

Rules for Edges:
1. Use explicit terms (e.g., upregulate, bind, decay, inhibit).
2. Do not assume indirect interactions—include only directly stated relationships in the abstract.
3. Logical ordering of interactions: Ensure that regulatory relationships reflect a biological hierarchy:
If a node is in a neutral or positive state, its effect on downstream targets should be logically consistent.
If inhibition or reduction is involved, relation should be able to logically track the cascaded effects properly.

Example of Logical Ordering:
If YTHDF2 knockdown upregulates KRAS, this means normal YTHDF2 expression downregulates KRAS.
The correct relation should be written as:
"YTHDF2 downregulates KRAS."
This approach ensures that all relationships reflect biological causality, preventing incorrect assumptions about indirect effects.

4. Special case for m6A RNA modification: mechanism via m6A RNA modification should be explicitly cascaded by m6A regulators (writer, eraser, and readers), m6A, and target genes only. 

Example: 
Glucose reduced the expression of METTL3, an m6A methyltransferase, which led to decreased overall levels of RNA m6A methylation. MYC regulate adipogenesis. The m6A levels of MYC were significantly decreased by Glucose.

glucose: a gene
METTL3: writer
m6A: m6A modification
MYC: target gene

The decreased m6A level by glocuse is a result of cascaded m6A mechanism. It can be mislead that glucose decrease m6A levels but this is just a result of cascaded biological mechanism. METTL3 is the actual regulator who increases the m6A level of MYC. Glucose is decreasing METTL3 and inhibition of METTL3 results the decreased m6A levels. It should not be interpreted as glucose decrease m6A level of MYC.


5. Meta-Relations for m6A RNA Modification Mechanisms
m6A regulators (writers, erasers, and readers) interact with m6A modifications on mRNAs. Explicitly use to link m6A regulators, m6A modification, and m6A target genes only. The effect of m6A modifications on target gene expression should be represented as a meta-relation. No other entities can be linked by meta relations. 

Correct Meta-Relation Structure
If an m6A reader protein (e.g., YTHDF2) binds to m6A and causes transcript decay, represent this with a meta-relation:
{
  "head": "m6A",
  "tail": "GENE_NAME",
  "label": "is on",
  "metaRelations": [{"label": "NULL", "target": "NULL"}]
}
{
  "head": "YTHDF2",
  "tail": "m6A",
  "label": "bind", 
  "metaRelations": [{"label": "decay", "target": "GENE_NAME"}]
}

If an m6A eraser protein (e.g., FTO) reduces m6A, leading to increased gene expression, represent this with a meta-relation:
{
  "head": "FTO",
  "tail": "m6A",
  "label": "reduce", 
  "metaRelations": [{"label": "increase", "target": "GENE_NAME"}]
}
{
  "head": "m6A",
  "tail": "GENE_NAME",
  "relation": "is on", 
  "metaRelations": [{"label": "NULL", "target": "NULL"}]
}


Example: FTO reduces m6A levels on β-catenin’s mRNA, leading to increased β-catenin expression.

Correct:
{
  "head": "FTO",
  "tail": "m6A",
  "label": "reduce", 
  "metaRelations": [{"label": "increase", "target": "β-catenin"}]
}
{
  "head": "m6A",
  "tail": "β-catenin",
  "label": "is on", 
  "metaRelations": [{"label": "NULL", "target": "NULL"}]
}

Incorrect:
FTO increases β-catenin (This ignores the m6A mechanism!)


6. Output Format (JSON)
The pathway graph should be structured in the following JSON format:
{
  "context": [
  {
	  "name": "namevalue",
	  "type": "typevalue"}
    ], 
  "entities": {
    "node_value": ["node_type", "context_specific_node_status"]
  },
  "relations": {
       {
        "head": "node_value",
        "tail": "node_value",
        "label": "relation_value", 
        "metaRelations": [{"label": "relation_value", "target": "node_value"}]
      }
  }
}


Example
Title:
"FTO regulates the chemo-radiotherapy resistance of cervical squamous cell carcinoma (CSCC) by targeting β-catenin through mRNA demethylation."

Abstract: 
"The role of N6-methyladenosine (m6A) demethylase fat mass and obesity-associated protein (FTO) in the regulation of chemo-radiotherapy resistance remains largely unknown. Here, we show that the mRNA level of FTO is elevated in cervical squamous cell carcinoma (CSCC) tissues when compared with respective adjacent normal tissues. FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts and in turn increases excision repair cross-complementation group 1 (ERCC1) activity. Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples. Taken together, these findings uncover a critical function for FTO and its substrate m6A in the regulation of chemo-radiotherapy resistance, which may bear potential clinical implications for CSCC treatment."

Context: 
Because the molecular mechanism is explicitly connected to cervical cancer and therapy resistance, the context is cervical squamous cell carcinoma, and the type of context is disease

Nodes:
	1. fat mass and obesity-associated protein: this is a gene and it was elevated in cervical squamous cell carcinoma
	2. N6-methyladenosine: this is a type of RNA modification
	3. beta-catenin: this is protein
	4. excision repair cross-complementation group 1: this is a gene
	5. chemo-radiotherapy resistance: this is a treatment response
	6. survival: this is a clinical phenotype

Regulatory relationships:
	1. fat mass and obesity-associated protein reduces N6-methyladenosine
	2. fat mass and obesity-associated protein upregulates beta-catenin: this is meta-relation associated with m6A RNA modification mechanism. The upregulation of beta-catenin is a following result of demethylation process of m6A by FTO.
	3. N6-methyladenosine is on beta-catenin mRNA transcripts
	4. beta-catenin increases the activity of excision repair cross-complementation group 1
	5. excision repair cross-complementation group 1 enhances chemo-radiotherapy resistance 
	6. chemo-radiotherapy resistance affects survival
	7. fat mass and obesity-associated protein enhances chemo-radiotherapy resistance 
	8. fat mass and obesity-associated protein affects surviaval


Constructed Pathway Graph:
{
    "context": [
        {
            "name": "cervical squamous cell carcinoma",
            "type": "cancer"
        }
    ],
    "entities": {
          "fat mass and obesity-associated protein" : 
          ["gene", "upregulated"],
          "N6-methyladenosine" : 
          ["RNA modification", "NULL"],
          "beta-catenin" : 
          ["protein", "NULL"],
          "excision repair cross-complementation group 1" : 
          ["gene", "NULL"],
          "chemo-radiotherapy resistance" : 
          ["treatment response", "NULL"], 
          "survival" : 
          ["clinical phenotype", "NULL"]
            },
    "relations": [
                {
                "head": "fat mass and obesity-associated protein",
                "tail": "N6-methyladenosine",
                "label": "reduce", 
                "metaRelations": 
                [{"label": "upregulate", "target": "beta-catenin"}]
            },
                 {
                "head": "N6-methyladenosine",
                "tail": "beta-catenin",
                "label": "is on", 
                "metaRelations": 
                [{"label": "NULL", "target": "NULL"}]
            },
                 {
                "head": "beta-catenin",
                "tail": "excision repair cross-complementation group 1",
                "label": "increase", 
                "metaRelations": 
                [{"label": "NULL", "target" : "NULL"}]},
                 {
                "head": "excision repair cross-complementation group 1",
                "tail": "chemo-radiotherapy resistance",
                "label": "enhance", 
                "metaRelations": 
                [{"label": "NULL", "target" : "NULL"}]},
                 {
                "head": "chemo-radiotherapy resistance",
                "tail": "survival",
                "label": "affect", 
                "metaRelations": 
                [{"label": "NULL", "target" : "NULL"}]},
                 {
                "head": "fat mass and obesity-associated protein",
                "tail": "chemo-radiotherapy resistance",
                "label": "enhance", 
                "metaRelations": 
                [{"label": "NULL", "target" : "NULL"}]},
                 {
                "head:": "fat mass and obesity-associated protein",
                "tail": "chemo-radiotherapy resistance",
                "label": "affect", 
                "metaRelations": 
                [{"label": "NULL", "target" : "NULL"}]}
                 ]
    }
    You output should include and only includethe Context, Nodes, Regulatory relationships, and Constructed Pathway Graph.
"""
json_prompt_template = """
You are asked to output this json:
{"context": [], "entities": {}, "relations": []}

From a extracted graph representation:
The relations contains 

{        
            "head": "",
            "tail": "",
            "label": "",
            "metaRelations": [], # empty if is NULL
            "text": "" # find and fill the responding text in the abstract
        }

You should copy the exact same information from the extracted graph representation and fill the desired output and change metaRelations to empty list if it is NULL, do not add metaRelations that do not exist in the extracted graph representation.

The desired output for the previous one should be:
{   "context": [
        {
            "name": "Cervical Squamous Cell Carcinoma",
            "type": "Cancer"
        }
    "entities": {
          "fat mass and obesity-associated protein" : 
          ["gene", "upregulated"],
          "N6-methyladenosine" : 
          ["RNA modification", "NULL"],
          "beta-catenin" : 
          ["protein", "NULL"],
          "excision repair cross-complementation group 1" : 
          ["gene", "NULL"],
          "chemo-radiotherapy resistance" : 
          ["treatment response", "NULL"], 
          "survival" : 
          ["clinical phenotype", "NULL"]
            },
    "relations": [
		    {
            "head": "fat mass and obesity-associated protein",
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
            "head": "beta-catenin",
            "tail": "excision repair cross-complementation group 1",
            "label": "increase",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts."
        },
        {
            "head": "excision repair cross-complementation group 1",
            "tail": "chemo-radiotherapy resistance",
            "label": "enhance",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo through regulating expression of beta-catenin by reducing m6A levels in its mRNA transcripts and in turn increases excision repair cross-complementation group 1 (ERCC1) activity."
        },
        {
            "head": "chemo-radiotherapy resistance",
            "tail": "surviaval",
            "label": "affect",
            "metaRelations": [],
            "text": "Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples."
        },
        {
            "head": "fat mass and obesity-associated protein",
            "tail": "chemo-radiotherapy resistance",
            "label": "enhance",
            "metaRelations": [],
            "text": "FTO enhances the chemo-radiotherapy resistance both in vitro and in vivo."
        },
        {
            "head": "fat mass and obesity-associated protein",
            "tail": "survival",
            "label": "affect",
            "metaRelations": [],
            "text": "Clinically, the prognostic value of FTO for overall survival is found to be dependent on beta-catenin expression in human CSCC samples."
        }
    ]
}

Please follow the above instructions and example to finish the JSON output for the second one. Generate only JSON code without any additional text or explanations.”
"""

write_json(prompt_template, json_prompt_template)
