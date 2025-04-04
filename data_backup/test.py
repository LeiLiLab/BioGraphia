import os
import json
from collections import defaultdict

def extract_nodes_relations():
    # Path to the main directory containing paper folders
    main_dir = "/home/ec2-user/work/temp_fix_folder/data/Main_dir"
    
    # Output file path
    output_file = "/home/ec2-user/work/temp_fix_folder/data/nodes_relations_database.json"
    
    # Sets to store unique nodes and relations
    nodes_set = set()
    relations_set = set()
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(main_dir):
        # Check if this directory has an original_data folder
        if "original_data" in dirs:
            # Construct the path to the original_output.json file
            json_path = os.path.join(root, "original_data", "original_output.json")
            
            # Check if the file exists
            if os.path.exists(json_path):
                try:
                    # Read the JSON file
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract relations data
                    if "relations" in data:
                        for relation in data["relations"]:
                            # Add head and tail nodes to the nodes set
                            if "head" in relation and "tail" in relation:
                                nodes_set.add(relation["head"])
                                nodes_set.add(relation["tail"])
                            
                            # Add the relation label to the relations set
                            if "label" in relation:
                                relations_set.add(relation["label"])
                                
                except Exception as e:
                    print(f"Error processing {json_path}: {e}")
    
    # Convert sets to sorted lists for consistent output
    nodes_list = sorted(list(nodes_set))
    relations_list = sorted(list(relations_set))
    
    # Create the output dictionary
    output_data = {
        "nodes": nodes_list,
        "relations": relations_list
    }
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully created {output_file}")
    print(f"Found {len(nodes_list)} unique nodes and {len(relations_list)} unique relations")

if __name__ == "__main__":
    extract_nodes_relations()