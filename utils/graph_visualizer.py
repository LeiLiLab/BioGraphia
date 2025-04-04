import os
import argparse
from pyvis.network import Network
import json

def get_edge_color(label):
    """
    Returns the appropriate color based on the edge label.
    """
    if label == '+':
        return "#2ecc71"  # Green color for positive relations
    elif label == '-':
        return "#e74c3c"  # Red color for negative relations
    return "#1f78b4"      # Default blue color for other relations

def generate_graph_from_json(data, filename):
    """
    Generates a graph from the JSON data structure with entities, relations, and text logs.
    """
    # Initialize network with dimensions
    net = Network(notebook=True, directed=True, height="800px", width="1400px")

    # Add all entities as nodes
    for entity in data["entities"]:
        net.add_node(entity, 
                    label=entity,
                    size=40,
                    color="#1f78b4",
                    font={'size': 16})

    # Add edges for direct relations and meta-relations
    for relation in data["relations"]:
        head = relation["head"]
        tail = relation["tail"]
        label = relation["label"]
        text_log = relation.get("text", "")  # Get the associated text if available
        edge_color = get_edge_color(label)  # Get color based on the label
        
        # For relations with meta-relations, create a virtual node for the label
        if "metaRelations" in relation and relation["metaRelations"]:
            # Create virtual node for the label with specific positioning
            label_node_id = f"{label}_{head}_{tail}"
            net.add_node(label_node_id,
                        label=label,
                        size=1,
                        color=edge_color,  # Use the same color for consistency
                        shape='text',
                        font={'size': 14, 'color': edge_color},
                        physics=False,  # Disable physics for label
                        fixed={'x': True, 'y': True})  # Fix position
            
            # Add the main visible edge
            net.add_edge(head,
                        tail,
                        color=edge_color,
                        width=2,
                        title=text_log,  # Add text as tooltip
                        smooth={"type": "continuous", "roundness": 0.2})
            
            # Add "constraints" to position the label (invisible edges)
            net.add_edge(head, 
                        label_node_id,
                        color=edge_color,
                        width=0.1,
                        length=100,  # Control distance
                        hidden=True,
                        physics=True,
                        smooth=False)
                        
            net.add_edge(label_node_id,
                        tail,
                        color=edge_color,
                        width=0.1,
                        length=100,  # Control distance
                        hidden=True,
                        physics=True,
                        smooth=False)
            
            # Add meta-relations from the label node
            for meta in relation["metaRelations"]:
                meta_color = get_edge_color(meta["label"])  # Get color for meta-relation
                net.add_edge(label_node_id,
                           meta["target"],
                           label=meta["label"],
                           title=meta["label"],
                           color=meta_color,
                           width=2,
                           dashes=True,
                           font={'size': 14},
                           smooth={"type": "continuous", "roundness": 0.2})
        else:
            # Add regular edge for relations without meta-relations
            net.add_edge(head, 
                        tail,
                        label=label,
                        title=text_log,  # Add text as tooltip
                        color=edge_color,
                        width=2,
                        font={'size': 14},
                        smooth={"type": "continuous", "roundness": 0.2})

    # Set physics options for better layout
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -20000,
          "centralGravity": 0.1,
          "springLength": 150,
          "springConstant": 0.08,
          "damping": 0.09,
          "avoidOverlap": 0.5
        },
        "minVelocity": 0.75,
        "maxVelocity": 50
      },
      "nodes": {
        "font": {
          "size": 16,
          "face": "arial"
        },
        "borderWidth": 2,
        "shape": "box",
        "fixed": false
      },
      "edges": {
        "font": {
          "size": 14,
          "align": "middle"
        },
        "smooth": {
          "enabled": true,
          "type": "continuous",
          "roundness": 0.2
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 1
          }
        }
      },
      "layout": {
        "randomSeed": 42,
        "improvedLayout": true,
        "hierarchical": {
          "enabled": false
        }
      },
      "interaction": {
        "navigationButtons": true,
        "hover": true,
        "multiselect": true
      }
    }
    """)

    # Save network
    net.show(filename)

def main():
    """
    Main function to parse arguments and generate the graph.
    """
    parser = argparse.ArgumentParser(description="Generate a graph visualization from JSON data.")
    parser.add_argument("input", type=str, help="Path to the input JSON file.")
    parser.add_argument("--output", type=str, default="reference_graph/graph_with_meta.html", help="Path to save the output HTML graph.")
    
    args = parser.parse_args()

    # Load JSON data from the input file
    with open(args.input, "r") as json_file:
        data = json.load(json_file)

    # Create output directory if it does not exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate the graph
    generate_graph_from_json(data, args.output)
    print(f"Saved graph to {args.output}")

if __name__ == "__main__":
    main()