<template>
  <div class="graph-container">
    <div class="controls">
      <button @click="fetchGraphData" class="btn">Refresh Graph</button>
      <button @click="toggleEdgeLabels" class="btn">{{ showEdgeLabels ? 'Hide' : 'Show' }} Edge Labels</button>
    </div>
    <div class="loading" v-if="loading">Loading graph data...</div>
    <div class="error" v-if="error">{{ error }}</div>
    <div id="graph" ref="graphContainer"></div>
  </div>
</template>

<script>
import axios from 'axios';
import * as d3 from 'd3';
import { BACKEND_URL } from '../config/api'

export default {
  name: 'GraphVisualizer',
  data() {
    return {
      graphData: null,
      loading: false,
      error: null,
      simulation: null,
      svg: null,
      width: 800,
      height: 600,
      showEdgeLabels: true
    };
  },
  mounted() {
    this.fetchGraphData();
    window.addEventListener('resize', this.handleResize);
    this.handleResize();
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    if (this.simulation) {
      this.simulation.stop();
    }
  },
  methods: {
    handleResize() {
      const container = this.$refs.graphContainer;
      if (container) {
        this.width = container.clientWidth || 800;
        this.height = container.clientHeight || 600;
        if (this.graphData) {
          this.renderGraph();
        }
      }
    },
    async fetchGraphData() {
      this.loading = true;
      this.error = null;
      
      // Get current user information
      const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
      
      // Process hash route URL (e.g., {BACKEND_URL}/#/analysis?url=...&mode=temp)
      const hash = window.location.hash; // Get #/analysis?url=...&mode=temp
      const queryString = hash.split('?')[1] || ''; // Get url=...&mode=temp
      const urlParams = new URLSearchParams(queryString);
      
      // Correctly get query parameters
      const mode = urlParams.get('mode') || 'view';
      const targetUser = urlParams.get('user') || currentUser.username;
      const paperUrl = urlParams.get('url') || 'https://pubmed.ncbi.nlm.nih.gov/29795461';
      
      // Extract PMID from paperUrl
      const pmid = paperUrl.replace(/\/$/, '').split('/').pop() || '';
      
      // Build API URL
      const apiUrl = `${BACKEND_URL}/api/graph?` +
                    `source=visualizer` +
                    `&pmid=${pmid}` +
                    `&username=${currentUser.username}` +
                    `&mode=${mode}` +
                    `&target_user=${targetUser}`;
      
      console.log(`Attempting to fetch data from: ${apiUrl}`);
      
      try {
        const response = await axios.get(apiUrl, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          withCredentials: false
        });
        
        console.log('Response received:', response);
        this.graphData = response.data;
        this.renderGraph();
      } catch (err) {
        console.error('Detailed error:', err);
        this.error = `Error loading graph data: ${err.message}`;
        console.error('Error fetching graph data:', err);
      } finally {
        this.loading = false;
      }
    },
    toggleEdgeLabels() {
      this.showEdgeLabels = !this.showEdgeLabels;
      if (this.svg) {
        this.svg.selectAll('.link-label, .link-label-bg')
          .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
      }
    },
    renderGraph() {
      if (!this.graphData || !this.graphData.relations) return;
      
      // Clear previous graph
      const container = this.$refs.graphContainer;
      container.innerHTML = '';
      
      // Create nodes and links from relations
      const nodesMap = new Map();
      const links = [];
      
      // Process relations to create nodes and links
      this.graphData.relations.forEach(relation => {
        if (!nodesMap.has(relation.head)) {
          nodesMap.set(relation.head, { id: relation.head, label: relation.head });
        }
        if (!nodesMap.has(relation.tail)) {
          nodesMap.set(relation.tail, { id: relation.tail, label: relation.tail });
        }
        
        links.push({
          source: relation.head,
          target: relation.tail,
          label: relation.label,
          text: relation.text
        });
      });
      
      const nodes = Array.from(nodesMap.values());
      
      // Create SVG
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', this.width)
        .attr('height', this.height)
        .attr('viewBox', [0, 0, this.width, this.height])
        .attr('style', 'max-width: 100%; height: auto;');
      
      // Add zoom functionality
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      
      this.svg.call(zoom);
      
      // Create a group for all elements
      const g = this.svg.append('g');
      
      // Create a force simulation
      this.simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(this.width / 2, this.height / 2))
        .force('collision', d3.forceCollide().radius(60));
      
      // Create arrow marker for links with improved style
      g.append('defs').selectAll('marker')
        .data(['end'])
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8) // Increased to better position the arrow tip
        .attr('refY', 0)
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4') // More elegant arrow shape
        .attr('fill', '#555'); // Darker color for better visibility
      
      // Create links
      const link = g.append('g')
        .attr('class', 'links')
        .selectAll('g')
        .data(links)
        .enter().append('g');
      
      const path = link.append('path')
        .attr('class', 'link')
        .attr('marker-end', 'url(#end)')
        .attr('stroke', '#999')
        .attr('stroke-width', 1.5)
        .attr('fill', 'none');
      
      // Add link labels
      const linkText = link.append('text')
        .attr('class', 'link-label')
        .attr('dy', -5)
        .attr('text-anchor', 'middle')
        .text(d => d.label)
        .attr('fill', '#666')
        .attr('font-size', '10px')
        .attr('background', 'white')
        .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
      
      // Add a white background rectangle for link labels
      link.insert('rect', 'text')
        .attr('class', 'link-label-bg')
        .attr('fill', 'white')
        .attr('opacity', 0.8)
        .attr('rx', 2)
        .attr('ry', 2)
        .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
      
      // Create nodes
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
          .on('start', this.dragstarted)
          .on('drag', this.dragged)
          .on('end', this.dragended));
      
      // Remove the circles for nodes and just use text
      // Add labels for nodes
      node.append('text')
        .attr('text-anchor', 'middle')
        .text(d => d.label)
        .attr('fill', '#333')
        .attr('font-weight', 'bold')
        .attr('font-size', '14px');
      
      // Add tooltips
      node.append('title')
        .text(d => d.label);
      
      // Update positions on each tick
      this.simulation.on('tick', () => {
        // Use straight lines with a slight offset to avoid overlapping paths
        path.attr('d', d => {
          // Calculate the direction vector
          const dx = d.target.x - d.source.x;
          const dy = d.target.y - d.source.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          
          // Normalize the direction vector
          const ndx = dx / length;
          const ndy = dy / length;
          
          // Calculate node radius (using text width approximation)
          const sourceRadius = 20; // Approximate node radius
          const targetRadius = 20; // Approximate node radius
          
          // Start and end points adjusted to be outside the nodes
          const startX = d.source.x + ndx * sourceRadius;
          const startY = d.source.y + ndy * sourceRadius;
          
          // Shorten the end point to avoid overlapping with the node
          const endX = d.target.x - ndx * targetRadius;
          const endY = d.target.y - ndy * targetRadius;
          
          // Return a straight line
          return `M${startX},${startY}L${endX},${endY}`;
        });
        
        // Update link text positioning
        linkText.each(function(d) {
          const dx = d.target.x - d.source.x;
          const dy = d.target.y - d.source.y;
          const midX = (d.source.x + d.target.x) / 2;
          const midY = (d.source.y + d.target.y) / 2;
          
          // Offset the text perpendicular to the line
          const length = Math.sqrt(dx * dx + dy * dy);
          const offset = 10; // pixels
          const perpX = -dy / length * offset;
          const perpY = dx / length * offset;
          
          d3.select(this)
            .attr('x', midX + perpX)
            .attr('y', midY + perpY);
            
          // Update the background rectangle
          const bbox = this.getBBox();
          d3.select(this.parentNode)
            .select('rect.link-label-bg')
            .attr('x', bbox.x - 2)
            .attr('y', bbox.y - 2)
            .attr('width', bbox.width + 4)
            .attr('height', bbox.height + 4);
        });
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
      });
    },
    dragstarted(event, d) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    },
    dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    },
    dragended(event, d) {
      if (!event.active) this.simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }
};
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: 80vh;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
}

.controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  display: flex;
  gap: 10px;
}

.btn {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.btn:hover {
  background-color: #3a7bc8;
}

.loading, .error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.error {
  color: #e74c3c;
}

#graph {
  width: 100%;
  height: 100%;
}
</style> 
