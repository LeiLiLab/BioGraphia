<template>
  <div class="graph-container">
    <!-- Add UNDO/REDO buttons -->
    <div class="history-controls">
      <button 
        @click="undo" 
        class="history-btn undo-btn" 
        :disabled="historyStack.length <= 1"
        title="Undo"
      ></button>
      <button 
        @click="redo" 
        class="history-btn redo-btn" 
        :disabled="redoStack.length === 0"
        title="Redo"
      ></button>
    </div>
    
    <div class="controls">
      <button @click="fetchGraphData" class="btn">Refresh Graph</button>
      <button @click="startAddNode" class="btn">Add Node</button>
      <button @click="toggleEdgeLabels" class="btn">{{ showEdgeLabels ? 'Hide' : 'Show' }} Edge Labels</button>
      <button @click="toggleFreezeGraph" class="btn">{{ isFrozen ? 'Unfreeze' : 'Freeze' }} Graph</button>
      <div class="save-container">
        <button @click.stop.prevent="handleSaveClick" class="btn save-btn" :disabled="!hasUnsavedChanges || saveStatus === 'saving'">
          {{ saveStatus === 'saving' ? 'Saving...' : 'Save Graph' }}
        </button>
        <span v-if="hasUnsavedChanges" class="unsaved-indicator">*</span>
        <div v-if="saveMessage" :class="['save-message', saveStatus]">{{ saveMessage }}</div>
      </div>
    </div>
    
    <!-- Relation text display window -->
    <div v-if="selectedRelationText" class="relation-text-window">
      <div class="relation-text-header">
        <div class="paper-title">{{ paperTitle }}</div>
        <button @click="closeRelationTextWindow" class="close-btn">&times;</button>
      </div>
      <div class="relation-text-content" v-html="highlightedAbstract"></div>
    </div>
    
    <!-- Supporting text selection window -->
    <div v-if="showSupportingTextSelection" class="supporting-text-window">
      <div class="text-selection-header">
        <div class="text-selection-title">Select Supporting Text</div>
        <button @click="cancelSupportingTextSelection" class="close-btn">&times;</button>
      </div>
      <div class="text-selection-content">
        <div class="text-selection-relation-info">
          Adding relation: <strong>{{ pendingRelationData?.label || '' }}</strong>
        </div>
        <div class="abstract-container" 
             @mouseup="handleTextSelection"
             @mousedown="startTextSelection"
             v-html="highlightedAbstractForSelection"></div>
        <div class="text-selection-instruction" v-if="!selectedSupportingText">
          Please select the supporting text for this relation by highlighting text in the abstract above.
        </div>
        <div class="text-selection-feedback" v-if="selectedSupportingText">
          <span class="selection-indicator">✓</span> Text selected. Click "Save" to confirm.
        </div>
        <div class="text-selection-buttons">
          <button @click="cancelSupportingTextSelection" class="btn cancel-btn">Cancel</button>
          <button @click="confirmSupportingText" class="btn">Save</button>
        </div>
      </div>
    </div>
    
    <!-- Connection mode indicator -->
    <div v-if="isCreatingConnection" class="connection-mode">
      <div class="connection-message-inline">
        Creating connection from: <strong>{{ sourceNode.label }}</strong> - Click on a target node to connect
      </div>
      <button @click="cancelConnectionCreation" class="btn cancel-btn">Cancel</button>
    </div>
    
    <!-- Meta-relation mode indicator -->
    <div v-if="isCreatingMetaRelation" class="connection-mode meta-relation-mode">
      <div class="connection-message-inline">
        Creating meta-relation from relation: <strong>{{ getRelationLabel(sourceRelation) }}</strong> - Click on a target node to connect
      </div>
      <button @click="cancelMetaRelationCreation" class="btn cancel-btn">Cancel</button>
    </div>
    
    <div class="loading" v-if="loading">Loading graph data...</div>
    <div class="error" v-if="error">{{ error }}</div>
    <div id="graph" ref="graphContainer"></div>
    
    <!-- Add context menu -->
    <ContextMenu
      :show="showContextMenu"
      :position="contextMenuPosition"
      :type="contextMenuType"
      :can-edit="canEdit"
      :is-admin="isAdmin"
      :paper-owner="paperOwner"
      :current-user="currentUserName"
      @close="closeContextMenu"
      @rename="handleRename"
      @delete="handleDelete"
      @add-connection="handleAddConnection"
      @add-meta-relation="handleAddMetaRelation"
      @edit-label="handleEditLabel"
    />
    
    <!-- Add dialogs for editing -->
    <div v-if="showEditDialog" class="dialog-overlay" @click.self="cancelEdit">
      <div class="dialog">
        <h3>{{ editDialogTitle }}</h3>
        <input v-model="editDialogValue" @keyup.enter="confirmEdit" ref="dialogInput" />
        <div class="dialog-buttons">
          <button @click.stop="cancelEdit" class="btn cancel-btn">Cancel</button>
          <button @click.stop="confirmEdit" class="btn">Next</button>
        </div>
      </div>
    </div>
    
    <!-- Confirmation dialog -->
    <div v-if="showConfirmDialog" class="dialog-overlay confirmation-dialog-overlay" @click.self="cancelConfirm">
      <div class="dialog">
        <h3>{{ confirmDialogTitle }}</h3>
        <p class="confirm-message">{{ confirmDialogMessage }}</p>
        <div class="dialog-buttons">
          <button @click.stop="cancelConfirm" class="btn cancel-btn">Cancel</button>
          <button @click.stop="confirmDialogAction" class="btn">Confirm</button>
        </div>
      </div>
    </div>
    
    <!-- Edit feedback toast -->
    <div v-if="editFeedback.show" :class="['edit-feedback', editFeedback.type]">
      {{ editFeedback.message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as d3 from 'd3';
import ContextMenu from './ContextMenu.vue';
import { BACKEND_URL } from '../config/api';

export default {
  name: 'GraphVisualizer',
  components: {
    ContextMenu
  },
  props: {
    // 添加entities props接收实体数据
    entities: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      // Add history tracking
      historyStack: [],
      redoStack: [],
      maxHistorySize: 20, // Maximum number of history states to store
      
      graphData: null,
      loading: false,
      error: null,
      simulation: null,
      svg: null,
      width: 800,
      height: 600,
      showEdgeLabels: true,
      isFrozen: false,
      
      // 添加tooltip状态
      nodeTooltip: null,
      showTooltip: false,
      tooltipContent: '',
      tooltipPosition: { x: 0, y: 0 },
      
      // Context menu state
      showContextMenu: false,
      contextMenuPosition: { x: 0, y: 0 },
      contextMenuType: 'node',
      selectedElement: null,
      
      // Paper owner and current user
      paperOwner: '',
      currentUserName: '',
      isAdmin: false,
      
      // Edit dialog state
      showEditDialog: false,
      editDialogTitle: '',
      editDialogValue: '',
      editDialogCallback: null,
      
      // Confirm dialog state
      showConfirmDialog: false,
      confirmDialogTitle: '',
      confirmDialogMessage: '',
      confirmDialogCallback: null,
      
      // Track changes
      hasUnsavedChanges: false,
      
      // Connection creation state
      isCreatingConnection: false,
      sourceNode: null,
      connectionPreview: null,
      
      // Save state feedback
      saveStatus: '', // 'saved', 'unsaved', 'saving', 'error'
      saveMessage: '',
      
      // Edit feedback
      editFeedback: {
        show: false,
        message: '',
        type: 'success' // 'success' or 'error'
      },
      
      // Relation text display
      selectedRelationText: null,
      paperTitle: "", // Add this line to store paper title
      paperAbstract: "", // Store paper abstract
      
      // Meta-relation creation state
      isCreatingMetaRelation: false,
      sourceRelation: null,
      metaRelationPreview: null,
      
      // Supporting text selection
      showSupportingTextSelection: false,
      selectedSupportingText: '',
      supportingTextCallback: null,
      pendingRelationData: null,
      selectionStartOffset: -1,
      selectionEndOffset: -1,
      
      // 新增加的状态跟踪
      isAddingNode: false,
      pendingNodeData: null,
    };
  },
  mounted() {
    // 获取当前用户信息
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    this.currentUserName = currentUser.username || '';
    this.isAdmin = currentUser.username === 'Admin';
    
    // 获取论文所有者
    this.paperOwner = this.getQueryParam('user') || this.currentUserName;
    
    // 输出权限设置日志
    console.log('Graph permission settings:', {
      currentUser: this.currentUserName,
      isAdmin: this.isAdmin,
      paperOwner: this.paperOwner,
      mode: this.getQueryParam('mode'),
      canEdit: this.canEdit
    });
    
    this.fetchGraphData();
    window.addEventListener('resize', this.handleResize);
    this.handleResize();
    
    // Add keyboard event listener for UNDO/REDO shortcuts
    document.addEventListener('keydown', this.handleKeyDown);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    if (this.simulation) {
      this.simulation.stop();
    }
    
    // Remove the keyboard event listener
    document.removeEventListener('keydown', this.handleKeyDown);
    
    // Also disconnect any observers
    if (this._circleObserver) {
      this._circleObserver.disconnect();
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
      
      // Clear existing visualization
      if (this.simulation) {
        this.simulation.stop();
      }
      
      const container = this.$refs.graphContainer;
      if (container) {
        container.innerHTML = '';
      }
      
      // Remove any observers
      if (this._circleObserver) {
        this._circleObserver.disconnect();
        this._circleObserver = null;
      }
      
      // 获取当前用户信息
      const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
      
      // 正确获取查询参数
      const mode = this.getQueryParam('mode') || 'view';
      const targetUser = this.getQueryParam('user') || currentUser.username;
      const paperUrl = this.getQueryParam('url') || 'https://pubmed.ncbi.nlm.nih.gov/29795461';
      
      // 从paperUrl中提取PMID
      const pmid = paperUrl.replace(/\/$/, '').split('/').pop() || '';
      
      try {
        // 首先获取论文数据以获取abstract和title
        const paperDataResponse = await axios.get(`${BACKEND_URL}/api/paper-analysis?url=${paperUrl}&username=${currentUser.username}&mode=${mode}&user=${targetUser}`);
        
        // 从返回的数据中提取abstract和title
        const paperData = paperDataResponse.data;
        const abstractItem = paperData.find(item => item.type === 'abstract');
        const titleItem = paperData.find(item => item.type === 'title');
        
        if (abstractItem) {
          this.paperAbstract = abstractItem.content;
          this.graphData = { ...this.graphData, abstract: abstractItem.content };
        }
        
        if (titleItem) {
          this.paperTitle = titleItem.content;
          this.graphData = { ...this.graphData, title: titleItem.content };
        }
        
        // 获取图数据
        const graphResponse = await axios.get(`${BACKEND_URL}/api/graph?source=visualizer&pmid=${pmid}&username=${currentUser.username}&mode=${mode}&target_user=${targetUser}`);
        
        console.log('Response received:', graphResponse);
        const graphData = graphResponse.data;
        
        // 合并abstract、title和图数据
        this.graphData = {
          ...graphData,
          abstract: this.paperAbstract,
          title: this.paperTitle,
          relations: graphData.relations || []
        };
        
        // 确保 relations 数组存在
        if (!this.graphData.relations) {
          this.graphData.relations = [];
        }
        
        // 过滤掉任何无效的关系
        this.graphData.relations = this.graphData.relations.filter(rel => 
          rel && typeof rel.head === 'string' && typeof rel.tail === 'string'
        );
        
        // 确保 nodes 数组存在
        if (!this.graphData.nodes) {
          // 如果不存在，从关系中创建 nodes 数组
          const nodesMap = new Map();
          
          this.graphData.relations.forEach(rel => {
            if (!nodesMap.has(rel.head)) {
              nodesMap.set(rel.head, { 
                id: rel.head, 
                label: rel.head,
                radius: this.calculateNodeRadius(rel.head)
              });
            }
            if (!nodesMap.has(rel.tail)) {
              nodesMap.set(rel.tail, { 
                id: rel.tail, 
                label: rel.tail,
                radius: this.calculateNodeRadius(rel.tail)
              });
            }
          });
          
          this.graphData.nodes = Array.from(nodesMap.values());
        } else {
          // 确保所有节点都有一致的 id 和 label
          this.graphData.nodes.forEach(node => {
            // 如果 label 缺失，使用 id 作为 label
            if (!node.label) {
              node.label = node.id;
            }
            // 为每个节点计算半径
            node.radius = this.calculateNodeRadius(node.label);
          });
        }
        
        // 重置未保存更改标志，因为我们刚刚从服务器获取了最新数据
        this.hasUnsavedChanges = false;
        
        // 清除保存状态和消息
        this.saveStatus = '';
        this.saveMessage = '';
        
        // Initialize history stack with initial state
        this.historyStack = [JSON.parse(JSON.stringify(this.graphData))];
        this.redoStack = [];
        
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
        this.svg.selectAll('.link-label')
          .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
      }
    },
    toggleFreezeGraph() {
      this.isFrozen = !this.isFrozen;
      
      if (this.simulation) {
        if (this.isFrozen) {
          // Stop the simulation and fix all nodes in place
          this.simulation.stop();
          this.simulation.nodes().forEach(node => {
            // Fix nodes at their current positions
            node.fx = node.x;
            node.fy = node.y;
          });
        } else {
          // Unfreeze all nodes and restart the simulation
          this.simulation.nodes().forEach(node => {
            // Release fixed positions
            node.fx = null;
            node.fy = null;
          });
          this.simulation.alpha(0.3).restart();
        }
      }
    },
    resetHighlights() {
      if (this.svg) {
        // Reset node styles
        this.svg.selectAll('.node')
          .classed('highlighted', false)
          .classed('connected', false)
          .classed('dimmed', false)
          .style('opacity', 1);

        this.svg.selectAll('.node text')
          .attr('fill', '#333')
          .attr('font-weight', 'normal');

        // Reset link styles - select both the groups and the paths
        this.svg.selectAll('.links g')
          .classed('highlighted', false)
          .classed('dimmed', false)
          .style('opacity', 1);
          
        this.svg.selectAll('.link')
          .classed('highlighted', false)
          .classed('dimmed', false)
          .attr('stroke', '#999')
          .attr('stroke-width', 1.5)
          .style('opacity', 1);
          
        this.svg.selectAll('.link-label')
          .attr('fill', '#666')
          .attr('font-weight', 'normal')
          .style('opacity', 1);
          
        // Reset meta link styles - ensure paths are explicitly reset
        this.svg.selectAll('.meta-link-group')
          .classed('highlighted', false)
          .classed('dimmed', false)
          .classed('connected', false)
          .style('opacity', 1);
          
        this.svg.selectAll('.meta-link')
          .classed('highlighted', false)
          .classed('dimmed', false)
          .classed('connected', false)
          .attr('stroke', '#9b59b6')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '3,3')
          .style('opacity', 1);
          
        this.svg.selectAll('.meta-link-label')
          .classed('highlighted', false)
          .attr('fill', '#9b59b6')
          .attr('font-weight', 'normal')
          .style('opacity', 1);
          
        // Ensure all paths are reset
        this.svg.selectAll('path.meta-link')
          .classed('highlighted', false)
          .attr('stroke', '#9b59b6')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '3,3')
          .style('opacity', 1);
          
        // Reset any other elements that might be affected
        this.svg.selectAll('path')
          .style('opacity', 1);
          
        // Close the relation text window
        this.closeRelationTextWindow();
          
        console.log('Highlights reset - including metaRelation edges');
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
      const metaLinks = []; // Add an array to store metaRelation links
      
      // Process relations to create nodes and links
      this.graphData.relations.forEach(relation => {
        // Skip invalid relations
        if (!relation || !relation.head || !relation.tail) {
          console.warn('Skipping invalid relation:', relation);
          return;
        }
        
        if (!nodesMap.has(relation.head)) {
          nodesMap.set(relation.head, { 
            id: relation.head, 
            label: relation.head,
            radius: this.calculateNodeRadius(relation.head) // Calculate radius based on text length
          });
        }
        if (!nodesMap.has(relation.tail)) {
          nodesMap.set(relation.tail, { 
            id: relation.tail, 
            label: relation.tail,
            radius: this.calculateNodeRadius(relation.tail) // Calculate radius based on text length
          });
        }
        
        // Create primary link
        const link = {
          source: relation.head,
          target: relation.tail,
          label: relation.label || '',
          text: relation.text || '',
          // Store original relation data for easier reference
          originalData: {
            head: relation.head,
            tail: relation.tail,
            label: relation.label || '',
            metaRelations: relation.metaRelations || []
          }
        };
        
        links.push(link);
        
        // Process metaRelations if they exist
        if (relation.metaRelations && relation.metaRelations.length > 0) {
          relation.metaRelations.forEach(metaRel => {
            if (metaRel.target && metaRel.label) {
              // Ensure the target node exists
              if (!nodesMap.has(metaRel.target)) {
                nodesMap.set(metaRel.target, { 
                  id: metaRel.target, 
                  label: metaRel.target,
                  radius: this.calculateNodeRadius(metaRel.target)
                });
              }
              
              // Create a metaLink
              metaLinks.push({
                sourceLink: link, // Reference to the parent link
                sourceRelation: relation, // Reference to the original relation
                target: metaRel.target,
                label: metaRel.label,
                isMetaRelation: true
              });
            }
          });
        }
      });
      
      const nodes = Array.from(nodesMap.values());
      
      // Store nodes in graphData for later reference
      this.graphData.nodes = nodes;
      
      // Validate links - ensure all source and target IDs exist as nodes
      const nodeIds = new Set(nodes.map(node => node.id));
      const validLinks = links.filter(link => {
        const isValid = nodeIds.has(link.source) && nodeIds.has(link.target);
        if (!isValid) {
          console.warn('Removing invalid link - node not found:', link);
        }
        return isValid;
      });
      
      // Validate metaLinks
      const validMetaLinks = metaLinks.filter(link => {
        const isValid = nodeIds.has(link.target);
        if (!isValid) {
          console.warn('Removing invalid metaLink - target node not found:', link);
        }
        return isValid;
      });
      
      // Initial positioning to spread nodes out
      nodes.forEach((node, i) => {
        // Position nodes in a circle initially with more spacing
        const angle = (i / nodes.length) * 2 * Math.PI;
        const radius = Math.min(this.width, this.height) * 0.45; // Increased from 0.4
        node.x = this.width / 2 + radius * Math.cos(angle);
        node.y = this.height / 2 + radius * Math.sin(angle);
        
        // Add some random jitter to prevent perfect circle alignment
        node.x += (Math.random() - 0.5) * 50;
        node.y += (Math.random() - 0.5) * 50;
      });
      
      // Create SVG
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', this.width)
        .attr('height', this.height)
        .attr('viewBox', [0, 0, this.width, this.height])
        .attr('style', 'max-width: 100%; height: auto;')
        .on('click', (event) => {
          // Only reset if clicking directly on the SVG background (not on a node or link)
          if (event.target.tagName === 'svg' || event.target === event.currentTarget) {
            console.log('Background click detected, resetting highlights');
            this.resetHighlights();
          }
        });
      // Add zoom functionality
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      
      this.svg.call(zoom);
      
      // Create a group for all elements
      const g = this.svg.append('g');
      
      // Add a transparent background rect to capture clicks
      g.append('rect')
        .attr('width', this.width)
        .attr('height', this.height)
        .attr('fill', 'transparent')
        .on('click', (event) => {
          event.stopPropagation();
          console.log('Background rect clicked, resetting highlights');
          this.resetHighlights();
        });
      
      // Create a force simulation with higher initial alpha
      this.simulation = d3.forceSimulation(nodes)
        .alpha(0.8) // Higher initial alpha for more movement
        .alphaDecay(0.02) // Slower decay to allow more time to find positions
        .force('link', d3.forceLink(validLinks).id(d => d.id).distance(250))
        .force('charge', d3.forceManyBody().strength(-500))
        .force('center', d3.forceCenter(this.width / 2, this.height / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius * 1.5).strength(1))
        .force('x', d3.forceX(this.width / 2).strength(0.05))
        .force('y', d3.forceY(this.height / 2).strength(0.05));
      
      // Create arrow marker for links with improved style
      g.append('defs').selectAll('marker')
        .data(['end', 'meta-end']) // Add marker for meta relations
        .enter().append('marker')
        .attr('id', d => d)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8) // arrow tip position
        .attr('refY', 0)
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .attr('orient', 'auto')
        .append('path') 
        .attr('d', 'M0,-4L8,0L0,4') // Arrow shape
        .attr('fill', d => d === 'meta-end' ? '#9b59b6' : '#555'); // Different color for meta relations
      
      // Create links
      const link = g.append('g')
        .attr('class', 'links')
        .selectAll('g')
        .data(validLinks)
        .join('g')
        .style('cursor', 'pointer') // Indicate interactivity for the entire link group
        .on('click', (event, d) => {
          console.log('Link group clicked');
          event.stopPropagation(); // Prevent event bubbling
          this.handleLinkClick(event, d);
        })
        .on('contextmenu', (event, d) => {
          console.log('Edge context menu triggered for:', d);
          // Prevent default browser context menu and stop propagation
          event.preventDefault();
          event.stopPropagation();
          
          // Validate the data before showing context menu
          if (!d || (!d.source && !d.originalData)) {
            console.error('Invalid edge data for context menu:', d);
            return;
          }
          
          // Show the context menu directly
          this.showContextMenu = true;
          this.contextMenuPosition = { x: event.clientX, y: event.clientY };
          this.contextMenuType = 'edge';
          this.selectedElement = d;
          
          // Setup document click listener to close menu when clicking outside
          this.setupDocumentClickListener();
        });
      
      // Update the path creation to include contextmenu
      const path = link.append('path')
        .attr('class', 'link')
        .attr('marker-end', 'url(#end)')
        .attr('stroke', '#999')
        .attr('stroke-width', 1.5)
        .attr('fill', 'none')
        .style('cursor', 'pointer');
      
      // Update the link text to include contextmenu
      const linkText = link.append('text')
        .attr('class', 'link-label')
        .attr('dy', -5)
        .attr('text-anchor', 'middle')
        .text(d => d.label)
        .attr('fill', '#666')
        .attr('font-size', '10px')
        .style('cursor', 'pointer')
        .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
        
      // Create metaLinks group
      const metaLinkGroup = g.append('g')
        .attr('class', 'meta-links');
        
      // Create meta links (will be populated during simulation tick)
      const metaLinkElements = metaLinkGroup.selectAll('g')
        .data(validMetaLinks)
        .join('g')
        .attr('class', 'meta-link-group')
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
          console.log('Meta link clicked:', d);
          event.stopPropagation();
          // Call the handle function for meta link clicks
          this.handleMetaLinkClick(event, d);
        })
        .on('contextmenu', (event, d) => {
          console.log('Meta edge context menu triggered for:', d);
          // Prevent default browser context menu and stop propagation
          event.preventDefault();
          event.stopPropagation();
          
          // Validate the data before showing context menu
          if (!d || !d.sourceLink || !d.target) {
            console.error('Invalid meta link data for context menu:', d);
            return;
          }
          
          // Show the context menu directly
          this.showContextMenu = true;
          this.contextMenuPosition = { x: event.clientX, y: event.clientY };
          this.contextMenuType = 'meta-edge';
          this.selectedElement = d;
          
          // Setup document click listener to close menu when clicking outside
          this.setupDocumentClickListener();
        });
        
      // Create paths for meta links
      const metaPath = metaLinkElements.append('path')
        .attr('class', 'meta-link')
        .attr('marker-end', 'url(#meta-end)')
        .attr('stroke', '#9b59b6') // Purple color for meta links
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '3,3') // Dashed line for meta links
        .attr('fill', 'none')
        .style('cursor', 'pointer');
        
      // Create labels for meta links
      const metaLinkText = metaLinkElements.append('text')
        .attr('class', 'meta-link-label')
        .attr('dy', -5)
        .attr('text-anchor', 'middle')
        .text(d => d.label)
        .attr('fill', '#9b59b6')
        .attr('font-size', '10px')
        .style('cursor', 'pointer')
        .style('visibility', this.showEdgeLabels ? 'visible' : 'hidden');
      
      // Create nodes with a completely custom enter function
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join(
          enter => {
            // Create node groups without circles
            const nodeEnter = enter.append('g')
              .attr('class', 'node')
              .style('cursor', 'pointer');
            
            // Add only text elements, no circles
            nodeEnter.append('text')
              .attr('text-anchor', 'middle')
              .attr('dy', '0.35em')
              .text(d => d.label)
              .attr('fill', '#333')
              .attr('font-weight', 'normal')
              .attr('font-size', '14px');
              
            // Add event handlers
            nodeEnter.on('click', (event, d) => {
              console.log('Node clicked in render');
              this.handleNodeClick(event, d);
            })
            .on('mouseover', (event, d) => {
              // 保留原有高亮效果
              d3.select(event.currentTarget).select('text')
                .attr('font-weight', 'bold')
                .attr('fill', '#666');
              
              // 添加显示实体信息tooltip
              this.showEntityTooltip(event, d);
            })
            .on('mouseout', (event) => {
              // 保留原有恢复效果
              const element = d3.select(event.currentTarget);
              if (!element.classed('highlighted') && !element.classed('connected')) {
                element.select('text')
                  .attr('font-weight', 'normal')
                  .attr('fill', '#333');
              }
              
              // 直接调用this上的方法隐藏tooltip
              this.hideEntityTooltip();
            })
            .on('contextmenu', (event, d) => {
              console.log('Node context menu triggered for:', d.id);
              // Prevent default browser context menu and stop propagation
              event.preventDefault();
              event.stopPropagation();
              
              // Show the context menu
              this.showContextMenu = true;
              this.contextMenuPosition = { x: event.clientX, y: event.clientY };
              this.contextMenuType = 'node';
              this.selectedElement = d;
              
              // Setup document click listener to close menu when clicking outside
              this.setupDocumentClickListener();
            })
            .call(d3.drag()
              .on('start', (event, d) => this.dragstarted(event, d))
              .on('drag', (event, d) => this.dragged(event, d))
              .on('end', (event, d) => this.dragended(event, d)));
              
            return nodeEnter;
          },
          update => update,
          exit => exit.remove()
        );
      
      // Explicitly remove any circles that might be created by D3.js
      this.svg.selectAll('.node circle').remove();
      
      // Set up a circle removal function
      const removeCircles = () => {
        this.svg.selectAll('.node circle').remove();
      };
      
      // Call removeCircles on each tick
      this.simulation.on('tick', () => {
        // Use straight lines with a slight offset to avoid overlapping paths
        path.attr('d', d => {
          // Skip invalid data
          if (!d || !d.source || !d.target) {
            return '';
          }
          
          // Check for needed properties
          if (typeof d.source.x !== 'number' || typeof d.source.y !== 'number' || 
              typeof d.target.x !== 'number' || typeof d.target.y !== 'number') {
            return '';
          }
          
          // Calculate the direction vector
          const dx = d.target.x - d.source.x;
          const dy = d.target.y - d.source.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          
          // Check for zero length
          if (length === 0) return '';
          
          // Normalize the direction vector
          const ndx = dx / length;
          const ndy = dy / length;
          
          // Calculate text width approximation for text-only nodes
          // make the lines further away from the nodes
          const sourceRadius = 30; 
          const targetRadius = 30; 
          
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
          // Skip invalid data
          if (!d || !d.source || !d.target) {
            return;
          }
          
          // Check for needed properties
          if (typeof d.source.x !== 'number' || typeof d.source.y !== 'number' || 
              typeof d.target.x !== 'number' || typeof d.target.y !== 'number') {
            return;
          }
          
          const dx = d.target.x - d.source.x;
          const dy = d.target.y - d.source.y;
          const midX = (d.source.x + d.target.x) / 2;
          const midY = (d.source.y + d.target.y) / 2;
          
          // Offset the text perpendicular to the line
          const length = Math.sqrt(dx * dx + dy * dy);
          
          // Skip if length is zero
          if (length === 0) return;
          
          const offset = 10; // pixels
          const perpX = -dy / length * offset;
          const perpY = dx / length * offset;
          
          d3.select(this)
            .attr('x', midX + perpX)
            .attr('y', midY + perpY);
        });
        
        // Update meta links
        metaPath.attr('d', d => {
          if (!d || !d.sourceLink || !d.target) {
            return '';
          }
          
          // Get the source and target data
          const sourceLink = d.sourceLink;
          if (!sourceLink.source || !sourceLink.target) {
            return '';
          }
          
          // Find target node
          const targetNode = nodes.find(n => n.id === d.target);
          if (!targetNode) {
            return '';
          }
          
          // Calculate the midpoint of the source link (where the label is)
          const sourceX = typeof sourceLink.source === 'object' ? sourceLink.source.x : null;
          const sourceY = typeof sourceLink.source === 'object' ? sourceLink.source.y : null;
          const targetX = typeof sourceLink.target === 'object' ? sourceLink.target.x : null;
          const targetY = typeof sourceLink.target === 'object' ? sourceLink.target.y : null;
          
          if (sourceX === null || sourceY === null || targetX === null || targetY === null) {
            return '';
          }
          
          // Calculate the midpoint (where the label is)
          const midX = (sourceX + targetX) / 2;
          const midY = (sourceY + targetY) / 2;
          
          // Calculate the direction vector
          const dx = targetNode.x - midX;
          const dy = targetNode.y - midY;
          const length = Math.sqrt(dx * dx + dy * dy);
          
          // Check for zero length
          if (length === 0) return '';
          
          // Normalize the direction vector
          const ndx = dx / length;
          const ndy = dy / length;
          
          // Calculate the start point (slightly offset from the midpoint)
          const startX = midX;
          const startY = midY;
          
          // Calculate the end point (slightly before the target node)
          const targetRadius = 20;
          const endX = targetNode.x - ndx * targetRadius * 1.5; // Increase the offset to 1.5x radius
          const endY = targetNode.y - ndy * targetRadius * 1.5; // Increase the offset to 1.5x radius
          
          // Return a curved path
          return `M${startX},${startY}L${endX},${endY}`;
        });
        
        // Update meta link text positioning
        metaLinkText.each(function(d) {
          if (!d || !d.sourceLink || !d.target) {
            return;
          }
          
          // Get the source and target data
          const sourceLink = d.sourceLink;
          if (!sourceLink.source || !sourceLink.target) {
            return;
          }
          
          // Find target node
          const targetNode = nodes.find(n => n.id === d.target);
          if (!targetNode) {
            return;
          }
          
          // Calculate the midpoint of the source link
          const sourceX = typeof sourceLink.source === 'object' ? sourceLink.source.x : null;
          const sourceY = typeof sourceLink.source === 'object' ? sourceLink.source.y : null;
          const targetX = typeof sourceLink.target === 'object' ? sourceLink.target.x : null;
          const targetY = typeof sourceLink.target === 'object' ? sourceLink.target.y : null;
          
          if (sourceX === null || sourceY === null || targetX === null || targetY === null) {
            return;
          }
          
          // Calculate the midpoint of the source link
          const midX = (sourceX + targetX) / 2;
          const midY = (sourceY + targetY) / 2;
          
          // Calculate the midpoint of the meta link
          const metaMidX = (midX + targetNode.x) / 2;
          const metaMidY = (midY + targetNode.y) / 2;
          
          // Calculate the direction vector of the meta link
          const dx = targetNode.x - midX;
          const dy = targetNode.y - midY;
          const length = Math.sqrt(dx * dx + dy * dy);
          
          // Skip if length is zero
          if (length === 0) return;
          
          // Create a perpendicular offset for the text
          const offset = 10; // pixels
          const perpX = -dy / length * offset;
          const perpY = dx / length * offset;
          
          d3.select(this)
            .attr('x', metaMidX + perpX)
            .attr('y', metaMidY + perpY);
        });
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
        
        // Remove circles on each tick
        removeCircles();
      });
      
      // Also set up a MutationObserver to catch any circles added to the DOM
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            removeCircles();
          }
        });
      });
      
      // Start observing the SVG element for DOM changes
      observer.observe(container, { 
        childList: true, 
        subtree: true 
      });
      
      // Store the observer to disconnect it later
      this._circleObserver = observer;
      
      // If the graph was frozen before, freeze it again
      if (this.isFrozen) {
        this.toggleFreezeGraph();
      }
    },
    dragstarted(event, d) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    },
    dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
      
      // If frozen, update the node position directly
      if (this.isFrozen) {
        d.x = event.x;
        d.y = event.y;
        // Force the simulation to update positions immediately
        this.simulation.tick();
      }
    },
    dragended(event, d) {
      if (!event.active) this.simulation.alphaTarget(0);
      
      // If not frozen, release the fixed position
      if (!this.isFrozen) {
        d.fx = null;
        d.fy = null;
      }
    },
    handleNodeClick(event, d) {
      console.log('Node clicked:', d.id);  // Debug logging
      // Prevent event propagation to avoid triggering the SVG background click
      event.stopPropagation();
      
      // Reset previous highlights
      this.resetHighlights();

      // Select the clicked node and highlight it in red
      const node = d3.select(event.currentTarget);
      node.classed('highlighted', true)
        .style('opacity', 1);

      // Make the text more visible
      node.select('text')
        .attr('fill', '#E74C3C')
        .attr('font-weight', 'bold')
        .style('opacity', 1);

      const sourceNodeId = d.id;

      // Find all connected links - ensure we're using the right property access
      const connectedLinks = this.svg.selectAll('.link').filter(function(link) {
        if (typeof link.source === 'object' && link.source && typeof link.target === 'object' && link.target) {
          return link.source.id === sourceNodeId || link.target.id === sourceNodeId;
        } else {
          return link.source === sourceNodeId || link.target === sourceNodeId;
        }
      });

      // Highlight connected links in red
      connectedLinks
        .classed('highlighted', true)
        .attr('stroke', '#E74C3C')
        .attr('stroke-width', 3)
        .style('opacity', 1);
        
      // Also highlight the parent groups of connected links
      connectedLinks.each(function() {
        d3.select(this.parentNode)
          .classed('highlighted', true)
          .style('opacity', 1);
      });

      // Find and highlight connected nodes in blue
      const connectedNodeIds = new Set();
      connectedLinks.each(function(link) {
        if (typeof link.source === 'object' && link.source && typeof link.target === 'object' && link.target) {
          if (link.source.id === sourceNodeId) {
            connectedNodeIds.add(link.target.id);
          } else {
            connectedNodeIds.add(link.source.id);
          }
        } else {
          if (link.source === sourceNodeId) {
            connectedNodeIds.add(link.target);
          } else {
            connectedNodeIds.add(link.source);
          }
        }
      });

      // Find and highlight meta links that target this node
      const metaLinks = this.svg.selectAll('.meta-link').filter(function(link) {
        return link && link.target === sourceNodeId;
      });
      
      // Highlight meta links
      metaLinks
        .classed('highlighted', true)
        .attr('stroke', '#8e44ad')
        .attr('stroke-width', 3)
        .style('opacity', 1);
        
      // Highlight meta link labels
      metaLinks.each(function() {
        d3.select(this.parentNode)
          .classed('highlighted', true)
          .style('opacity', 1);
          
        d3.select(this.parentNode).select('text')
          .classed('highlighted', true)
          .attr('fill', '#8e44ad')
          .attr('font-weight', 'bold')
          .style('opacity', 1);
      });
      
      // For each meta link, add the source link nodes to the connected nodes
      metaLinks.each(function(metaLink) {
        if (metaLink && metaLink.sourceLink) {
          const sourceId = typeof metaLink.sourceLink.source === 'object' ? 
            metaLink.sourceLink.source.id : metaLink.sourceLink.source;
          const targetId = typeof metaLink.sourceLink.target === 'object' ? 
            metaLink.sourceLink.target.id : metaLink.sourceLink.target;
            
          if (sourceId) connectedNodeIds.add(sourceId);
          if (targetId) connectedNodeIds.add(targetId);
        }
      });

      this.svg.selectAll('.node').filter(function(node) {
        return connectedNodeIds.has(node.id);
      })
      .classed('connected', true)
      .style('opacity', 1)
      .select('text')
      .attr('fill', '#3498DB')
      .attr('font-weight', 'bold')
      .style('opacity', 1);

      // Dim non-connected nodes and links
      this.svg.selectAll('.node:not(.highlighted):not(.connected)')
        .classed('dimmed', true)
        .style('opacity', 0.4);

      // Dim non-highlighted links and their parent groups
      this.svg.selectAll('.link:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      this.svg.selectAll('.links g:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      // Dim non-highlighted meta links and their parent groups
      this.svg.selectAll('.meta-link:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      this.svg.selectAll('.meta-link-group:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      // Also dim the labels of non-highlighted links
      this.svg.selectAll('.links g:not(.highlighted) .link-label')
        .style('opacity', 0.2);
        
      // Also dim the labels of non-highlighted meta links
      this.svg.selectAll('.meta-link-group:not(.highlighted) .meta-link-label')
        .style('opacity', 0.2);
    },
    handleLinkClick(event, d) {
      console.log('Link clicked:', d);
      event.stopPropagation();
      
      // Check if d is valid
      if (!d) {
        console.error('Invalid link data:', d);
        return;
      }
      
      // Reset previous highlights
      this.resetHighlights();

      // Get the link group
      const linkGroup = d3.select(event.currentTarget);
      
      // Highlight the link group
      linkGroup.classed('highlighted', true)
        .style('opacity', 1);
      
      // Highlight the path
      linkGroup.select('path')
        .classed('highlighted', true)
        .attr('stroke', '#E74C3C')
        .attr('stroke-width', 2)
        .style('opacity', 1);
      
      // Highlight the label
      linkGroup.select('text')
        .attr('fill', '#E74C3C')
        .attr('font-weight', 'bold')
        .style('opacity', 1);

      // Try to get source and target IDs from different properties
      let sourceId = null;
      let targetId = null;
      
      // Try originalData first (most reliable)
      if (d && d.originalData) {
        sourceId = d.originalData.head;
        targetId = d.originalData.tail;
      }
      // Then try source/target objects
      else if (d && d.source && d.target) {
        sourceId = typeof d.source === 'object' && d.source ? d.source.id : d.source;
        targetId = typeof d.target === 'object' && d.target ? d.target.id : d.target;
      }
      
      if (!sourceId || !targetId) {
        console.error('Invalid source or target ID in link click:', { d, sourceId, targetId });
        return;
      }

      // Highlight connected nodes
      this.svg.selectAll('.node').filter(node => 
        node && node.id && (node.id === sourceId || node.id === targetId)
      )
      .classed('connected', true)
      .style('opacity', 1)
      .select('text')
      .attr('fill', '#3498DB')
      .attr('font-weight', 'bold')
      .style('opacity', 1);
      
      // Find and highlight meta links that are related to this link
      if (d.originalData && d.originalData.metaRelations && d.originalData.metaRelations.length > 0) {
        // Find the related meta links using their parent link reference
        const metaLinks = this.svg.selectAll('.meta-link').filter(metaLink => {
          if (!metaLink || !metaLink.sourceLink || !metaLink.sourceLink.originalData) return false;
          
          // Check if this meta link's source is the current link
          return metaLink.sourceLink.originalData.head === sourceId && 
                 metaLink.sourceLink.originalData.tail === targetId;
        });
        
        // Highlight meta links
        metaLinks
          .classed('highlighted', true)
          .attr('stroke', '#8e44ad')
          .attr('stroke-width', 2)
          .style('opacity', 1);
          
        // Highlight meta link groups and labels  
        metaLinks.each(function() {
          d3.select(this.parentNode)
            .classed('highlighted', true)
            .style('opacity', 1);
            
          d3.select(this.parentNode).select('text')
            .classed('highlighted', true)
            .attr('fill', '#8e44ad')
            .attr('font-weight', 'bold')
            .style('opacity', 1);
        });
        
        // Add the target nodes of meta links to connected nodes
        const additionalConnectedNodes = new Set();
        
        metaLinks.each(function(metaLink) {
          if (metaLink && metaLink.target) {
            additionalConnectedNodes.add(metaLink.target);
          }
        });
        
        // Highlight these additional nodes
        if (additionalConnectedNodes.size > 0) {
          this.svg.selectAll('.node').filter(node => 
            node && node.id && additionalConnectedNodes.has(node.id)
          )
          .classed('connected', true)
          .style('opacity', 1)
          .select('text')
          .attr('fill', '#9b59b6') // Use purple for meta-connected nodes
          .attr('font-weight', 'bold')
          .style('opacity', 1);
        }
      }

      // Dim other elements
      this.svg.selectAll('.node:not(.connected)')
        .classed('dimmed', true)
        .style('opacity', 0.4);

      // Dim other link groups
      this.svg.selectAll('.links g:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      // Also dim the paths inside those groups
      this.svg.selectAll('.links g:not(.highlighted) path')
        .style('opacity', 0.2);
        
      // And dim the labels inside those groups
      this.svg.selectAll('.links g:not(.highlighted) text')
        .style('opacity', 0.2);
        
      // Dim non-highlighted meta links and their groups
      this.svg.selectAll('.meta-link-group:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      this.svg.selectAll('.meta-link:not(.highlighted)')
        .style('opacity', 0.2);
        
      this.svg.selectAll('.meta-link-label:not(.highlighted)')
        .style('opacity', 0.2);
        
      // Display the relation text in the window
      this.showRelationText(d);
    },
    
    handleMetaLinkClick(event, d) {
      console.log('Meta link clicked:', d);
      event.stopPropagation();
      
      // Check if d is valid
      if (!d || !d.sourceLink || !d.target) {
        console.error('Invalid meta link data:', d);
        return;
      }
      
      // Reset previous highlights
      this.resetHighlights();

      // Get the meta link group
      const metaLinkGroup = d3.select(event.currentTarget);
      
      // Highlight the meta link group
      metaLinkGroup.classed('highlighted', true)
        .style('opacity', 1);
      
      // Highlight the meta link path
      metaLinkGroup.select('path')
        .classed('highlighted', true)
        .attr('stroke', '#8e44ad')
        .attr('stroke-width', 2)
        .style('opacity', 1);
      
      // Highlight the meta link label
      metaLinkGroup.select('text')
        .classed('highlighted', true)
        .attr('fill', '#8e44ad')
        .attr('font-weight', 'bold')
        .style('opacity', 1);

      // Get the source relation (parent relation)
      const sourceLink = d.sourceLink;
      if (!sourceLink) {
        console.error('Invalid source link for meta relation:', d);
        return;
      }
      
      // Get the parent relation's source and target
      let sourceId = null;
      let targetId = null;
      
      // Try originalData first (most reliable)
      if (sourceLink.originalData) {
        sourceId = sourceLink.originalData.head;
        targetId = sourceLink.originalData.tail;
      }
      // Then try source/target objects
      else if (sourceLink.source && sourceLink.target) {
        sourceId = typeof sourceLink.source === 'object' && sourceLink.source ? sourceLink.source.id : sourceLink.source;
        targetId = typeof sourceLink.target === 'object' && sourceLink.target ? sourceLink.target.id : sourceLink.target;
      }
      
      if (!sourceId || !targetId) {
        console.error('Invalid source or target ID in meta link click:', { sourceLink, sourceId, targetId });
        return;
      }
      
      // Find and highlight the parent relation (sourceLink)
      this.svg.selectAll('.links g').each(function(linkData) {
        if (!linkData) return;
        
        // Get source and target IDs from the link data
        const linkSourceId = typeof linkData.source === 'object' && linkData.source ? linkData.source.id : linkData.source;
        const linkTargetId = typeof linkData.target === 'object' && linkData.target ? linkData.target.id : linkData.target;
        
        // Check if this is the parent link
        if (linkSourceId === sourceId && linkTargetId === targetId) {
          const linkGroup = d3.select(this);
          
          // Highlight the parent link group
          linkGroup.classed('highlighted', true)
            .style('opacity', 1);
          
          // Highlight the parent link path
          linkGroup.select('path')
            .classed('highlighted', true)
            .attr('stroke', '#E74C3C')
            .attr('stroke-width', 2)
            .style('opacity', 1);
          
          // Highlight the parent link label
          linkGroup.select('text')
            .attr('fill', '#E74C3C')
            .attr('font-weight', 'bold')
            .style('opacity', 1);
        }
      });
      
      // Get all connected nodes (from parent relation and meta relation)
      const connectedNodeIds = new Set([sourceId, targetId, d.target]);
      
      // Highlight all connected nodes
      this.svg.selectAll('.node').filter(node => 
        node && node.id && connectedNodeIds.has(node.id)
      )
      .classed('connected', true)
      .style('opacity', 1)
      .select('text')
      .attr('fill', '#3498DB')
      .attr('font-weight', 'bold')
      .style('opacity', 1);
      
      // Highlight the target node of meta relation in purple
      this.svg.selectAll('.node').filter(node => 
        node && node.id && node.id === d.target
      )
      .select('text')
      .attr('fill', '#9b59b6');
      
      // Dim other elements
      this.svg.selectAll('.node:not(.connected)')
        .classed('dimmed', true)
        .style('opacity', 0.4);

      // Dim other link groups
      this.svg.selectAll('.links g:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      // Also dim the paths inside those groups
      this.svg.selectAll('.links g:not(.highlighted) path')
        .style('opacity', 0.2);
        
      // And dim the labels inside those groups
      this.svg.selectAll('.links g:not(.highlighted) text')
        .style('opacity', 0.2);
        
      // Dim non-highlighted meta links and their groups
      this.svg.selectAll('.meta-link-group:not(.highlighted)')
        .classed('dimmed', true)
        .style('opacity', 0.2);
        
      this.svg.selectAll('.meta-link:not(.highlighted)')
        .style('opacity', 0.2);
        
      this.svg.selectAll('.meta-link-label:not(.highlighted)')
        .style('opacity', 0.2);
      
      // Create and display meta relation text
      const relationText = `Meta Relation: "${d.label || 'Affects'}" affecting node "${d.target}"\nParent Relation: "${sourceLink.label || ''}" from "${sourceId}" to "${targetId}"`;
      this.selectedRelationText = relationText;
    },
    showRelationText(relation) {
      // First try to get text from the relation object
      let text = relation.text || '';
      
      // If no text in the relation object, try to find it in the original data
      if (!text && relation.originalData) {
        const sourceId = relation.originalData.head;
        const targetId = relation.originalData.tail;
        
        // Find the relation in the graph data
        const originalRelation = this.graphData.relations.find(
          r => r.head === sourceId && r.tail === targetId
        );
        
        if (originalRelation && originalRelation.text) {
          text = originalRelation.text;
        }
      }
      
      // Get the abstract and title from graphData
      if (this.graphData) {
        if (this.graphData.abstract) {
          this.paperAbstract = this.graphData.abstract;
        }
        if (this.graphData.title) {
          this.paperTitle = this.graphData.title;
        }
      }
      
      // Set the selected text for highlighting
      this.selectedRelationText = text;
    },
    closeRelationTextWindow() {
      this.selectedRelationText = null;
    },
    removeAllCircles() {
      // Direct DOM manipulation to remove all circles
      const circles = document.querySelectorAll('.node circle, svg circle');
      circles.forEach(circle => {
        circle.remove();
      });
    },
    calculateNodeRadius(text) {
      // Base radius plus additional space based on text length
      // This helps prevent overlap by giving longer text more space
      const baseRadius = 40; // Increased from 30
      const charWidth = 6; // Increased from 5
      return baseRadius + Math.min(text.length * charWidth / 2, 60); // Increased cap from 50
    },
    closeContextMenu() {
      this.showContextMenu = false;
      this.selectedElement = null;
      
      // 移除文档点击事件监听器
      document.removeEventListener('click', this.handleDocumentClick, true);
      document.removeEventListener('mousedown', this.handleDocumentClick, true);
    },
    
    // Add a new method to handle document click events
    setupDocumentClickListener() {
      // 确保在设置新监听器前移除任何现有的监听器
      document.removeEventListener('click', this.handleDocumentClick, true);
      document.removeEventListener('mousedown', this.handleDocumentClick, true);
      
      // 使用事件捕获阶段以确保能捕获到所有点击
      document.addEventListener('click', this.handleDocumentClick, true);
      document.addEventListener('mousedown', this.handleDocumentClick, true);
      
      console.log('Document click listeners added for context menu');
    },
    
    // Handler for document click events
    handleDocumentClick(event) {
      // 如果菜单已关闭，不需要处理
      if (!this.showContextMenu) return;
      
      // 获取当前上下文菜单元素
      const contextMenuEl = document.querySelector('.context-menu');
      
      // 检查点击是否在菜单外部
      if (!contextMenuEl || !contextMenuEl.contains(event.target)) {
        console.log('Document click detected outside context menu, closing menu');
        this.closeContextMenu();
        
        // 阻止事件冒泡，防止其他处理器再次处理此事件
        event.stopPropagation();
      }
    },
    
    handleContextMenu(event, d, type) {
      // Prevent default browser context menu
      event.preventDefault();
      event.stopPropagation();
      
      // Check if d is valid
      if (!d) {
        console.error('Invalid element data for context menu:', d);
        return;
      }
      
      console.log('Context menu triggered for:', type, d);
      console.log('Event position:', event.clientX, event.clientY);
      
      // Set context menu properties
      this.showContextMenu = true;
      this.contextMenuPosition = { x: event.clientX, y: event.clientY };
      this.contextMenuType = type;
      this.selectedElement = d;
      
      // Debug graph data
      this.debugGraphData();
      
      // Setup document click listener to close menu when clicking outside
      this.setupDocumentClickListener();
      
      // Force Vue to update the DOM
      this.$nextTick(() => {
        console.log('Context menu should be visible now');
      });
    },
    
    handleRename() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      // Add null check for selectedElement
      if (!this.selectedElement) {
        console.error('No element selected for renaming');
        this.showEditFeedback('Error: No element selected', 'error');
        return;
      }
      
      this.editDialogTitle = 'Rename Node';
      this.editDialogValue = this.selectedElement.label || '';
      this.showEditDialog = true;
      
      // Store a copy of the selected element to avoid reference issues
      const selectedElement = {...this.selectedElement};
      
      this.editDialogCallback = (newValue) => {
        if (!selectedElement || !selectedElement.id) {
          console.error('Invalid node data for renaming');
          this.showEditFeedback('Error: Cannot rename node', 'error');
          return false;
        }
        return this.renameNode(selectedElement.id, newValue);
      };
      this.closeContextMenu();
    },
    
    handleDelete() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      try {
        if (this.contextMenuType === 'node') {
          if (!this.selectedElement || !this.selectedElement.id) {
            console.error('Invalid node for deletion:', this.selectedElement);
            this.showEditFeedback('Error: Cannot identify node to delete', 'error');
            return;
          }
          this.deleteNode(this.selectedElement.id);
        } else if (this.contextMenuType === 'meta-edge') {
          // Handle meta relation deletion
          if (!this.selectedElement || !this.selectedElement.sourceLink || !this.selectedElement.target) {
            console.error('Invalid meta relation for deletion:', this.selectedElement);
            this.showEditFeedback('Error: Cannot identify meta relation to delete', 'error');
            return;
          }
          this.deleteMetaRelation(this.selectedElement);
        } else {
          // For regular edge deletion
          if (!this.selectedElement) {
            console.error('Invalid edge for deletion:', this.selectedElement);
            this.showEditFeedback('Error: Cannot identify edge to delete', 'error');
            return;
          }
          this.deleteRelation(this.selectedElement);
        }
        this.closeContextMenu();
      } catch (error) {
        console.error('Error in handleDelete:', error);
        this.showEditFeedback('Error during deletion', 'error');
        this.closeContextMenu();
      }
    },
    
    handleAddConnection() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      this.isCreatingConnection = true;
      this.sourceNode = this.selectedElement;
      this.closeContextMenu();
      
      // Add visual indicator that we're in connection mode
      this.svg.style('cursor', 'crosshair');
      
      // Add temporary preview line
      this.connectionPreview = this.svg.append('path')
        .attr('class', 'preview-connection')
        .attr('stroke', '#4a90e2')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('fill', 'none')
        .style('opacity', 0)
        .attr('marker-end', 'url(#end)');
        
      // Add mousemove handler for preview
      this.svg.on('mousemove', (event) => {
        if (this.isCreatingConnection) {
          const [x, y] = d3.pointer(event);
          this.updateConnectionPreview(x, y);
        }
      });
      
      // Update node click handlers for target selection
      this.svg.selectAll('.node')
        .style('cursor', 'pointer')
        .on('click.connect', (event, d) => {
          if (this.isCreatingConnection && d.id !== this.sourceNode.id) {
            this.showRelationLabelDialog(d);
          }
        });
    },
    
    handleAddMetaRelation() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      // Store the source relation
      this.isCreatingMetaRelation = true;
      this.sourceRelation = this.selectedElement;
      this.closeContextMenu();
      
      // Add visual indicator that we're in meta-relation creation mode
      this.svg.style('cursor', 'crosshair');
      
      // Get the midpoint of the source relation to use as the starting point
      const sourceLink = this.sourceRelation;
      let sourceX, sourceY, targetX, targetY;
      
      if (typeof sourceLink.source === 'object' && sourceLink.source && 
          typeof sourceLink.target === 'object' && sourceLink.target) {
        sourceX = sourceLink.source.x;
        sourceY = sourceLink.source.y;
        targetX = sourceLink.target.x;
        targetY = sourceLink.target.y;
      } else {
        // Log error and return if we can't find the coordinates
        console.error('Could not determine coordinates for meta-relation preview', sourceLink);
        this.cancelMetaRelationCreation();
        return;
      }
      
      // Calculate the midpoint of the source relation
      const midX = (sourceX + targetX) / 2;
      const midY = (sourceY + targetY) / 2;
      
      // Add temporary preview line from the midpoint of the source relation
      this.metaRelationPreview = this.svg.append('path')
        .attr('class', 'preview-connection meta-preview')
        .attr('stroke', '#9b59b6') // Purple to match meta relation style
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '3,3') // Dashed line to match meta relation style
        .attr('fill', 'none')
        .style('opacity', 0)
        .attr('marker-end', 'url(#meta-end)');
        
      // Add mousemove handler for preview
      this.svg.on('mousemove', (event) => {
        if (this.isCreatingMetaRelation) {
          const [x, y] = d3.pointer(event);
          this.updateMetaRelationPreview(midX, midY, x, y);
        }
      });
      
      // Update node click handlers for target selection
      this.svg.selectAll('.node')
        .style('cursor', 'pointer')
        .on('click.meta-connect', (event, d) => {
          // Don't allow connecting to source or target of the original relation
          if (this.isCreatingMetaRelation) {
            // Get source and target IDs with null checks
            let sourceId = null;
            let targetId = null;
            
            // Try to get IDs from various sources
            if (sourceLink.originalData) {
              sourceId = sourceLink.originalData.head;
              targetId = sourceLink.originalData.tail;
            } else if (sourceLink.source && sourceLink.target) {
              sourceId = typeof sourceLink.source === 'object' ? sourceLink.source.id : sourceLink.source;
              targetId = typeof sourceLink.target === 'object' ? sourceLink.target.id : sourceLink.target;
            }
            
            // Check if target node is not source or target of original relation
            if (d.id !== sourceId && d.id !== targetId) {
              this.showMetaRelationLabelDialog(d);
            } else {
              this.showEditFeedback('Cannot create meta-relation to source or target of original relation', 'error');
            }
          }
        });
    },
    
    updateConnectionPreview(x, y) {
      if (!this.connectionPreview || !this.sourceNode) return;
      
      const sourceX = this.sourceNode.x;
      const sourceY = this.sourceNode.y;
      
      this.connectionPreview
        .style('opacity', 1)
        .attr('d', `M${sourceX},${sourceY}L${x},${y}`);
    },
    
    updateMetaRelationPreview(midX, midY, x, y) {
      if (!this.metaRelationPreview || !this.sourceRelation) return;
      
      this.metaRelationPreview
        .style('opacity', 1)
        .attr('d', `M${midX},${midY}L${x},${y}`);
    },
    
    showRelationLabelDialog(targetNode) {
      this.editDialogTitle = 'Enter Relation Label';
      this.editDialogValue = '';
      this.showEditDialog = true;
      this.editDialogCallback = (label) => {
        // 储存关系数据，但不立即添加
        this.pendingRelationData = {
          sourceId: this.sourceNode.id,
          targetId: targetNode.id,
          label: label
        };
        // 关闭标签对话框
        this.showEditDialog = false;
        // 显示选择支持文本的界面
        this.showSupportingTextSelection = true;
      };
    },
    
    showMetaRelationLabelDialog(targetNode) {
      this.editDialogTitle = 'Enter Meta-Relation Label';
      this.editDialogValue = '';
      this.showEditDialog = true;
      this.editDialogCallback = (label) => {
        // 在用户点击编辑对话框的Next按钮后，向用户显示确认对话框
        this.confirmDialogTitle = 'Add Meta-Relation';
        this.confirmDialogMessage = `Add meta-relation with label "${label}" from ${this.getRelationLabel(this.sourceRelation)} to ${targetNode.label}?`;
        this.showConfirmDialog = true;
        
        // 设置确认回调
        this.confirmDialogCallback = () => {
          this.addMetaRelation(this.sourceRelation, targetNode.id, label);
          this.cancelMetaRelationCreation();
        };
      };
    },
    
    cancelConnectionCreation() {
      // 如果在添加新节点过程中取消，需要移除新创建的节点
      if (this.isAddingNode && this.pendingNodeData) {
        // 移除先前添加的临时节点
        this.graphData.nodes = this.graphData.nodes.filter(
          node => node.id !== this.pendingNodeData.id
        );
        this.renderGraph(); // 重新渲染图以反映变化
        this.pendingNodeData = null;
        this.isAddingNode = false;
        
        // 修改为使用toast样式提示（使用warning类型而不是error）
        this.showEditFeedback('Node addition canceled', 'warning');
      }

      this.isCreatingConnection = false;
      this.sourceNode = null;
      
      // 移除预览线
      if (this.connectionPreview) {
        this.connectionPreview.remove();
        this.connectionPreview = null;
      }
      
      // 重置光标和点击处理器
      this.svg.style('cursor', 'default');
      this.svg.selectAll('.node')
        .style('cursor', 'pointer')
        .on('click.connect', null);
        
      // 移除鼠标移动处理器
      this.svg.on('mousemove', null);
    },
    
    cancelMetaRelationCreation() {
      this.isCreatingMetaRelation = false;
      this.sourceRelation = null;
      
      // Remove preview line
      if (this.metaRelationPreview) {
        this.metaRelationPreview.remove();
        this.metaRelationPreview = null;
      }
      
      // Reset cursor and click handlers
      this.svg.style('cursor', 'default');
      this.svg.selectAll('.node')
        .style('cursor', 'pointer')
        .on('click.meta-connect', null);
        
      // Remove mousemove handler
      this.svg.on('mousemove', null);
    },
    handleEditLabel() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      this.editDialogTitle = 'Edit Label';
      
      try {
        // Check if selectedElement exists
        if (!this.selectedElement) {
          console.error('No selected element for editing');
          this.showEditFeedback('Error: No element selected', 'error');
          return;
        }
        
        // Handle meta-edge type
        if (this.contextMenuType === 'meta-edge') {
          const metaRelation = this.selectedElement;
          
          // Check if the meta relation is valid
          if (!metaRelation || !metaRelation.sourceLink || !metaRelation.label) {
            console.error('Invalid meta relation data:', metaRelation);
            this.showEditFeedback('Error: Invalid meta relation data', 'error');
            return;
          }
          
          this.editDialogValue = metaRelation.label || '';
          
          const sourceLink = metaRelation.sourceLink;
          const targetNode = metaRelation.target;
          
          // Store info we need for the edit
          const sourceId = sourceLink.originalData?.head || 
                          (typeof sourceLink.source === 'object' ? sourceLink.source.id : sourceLink.source);
          const targetId = sourceLink.originalData?.tail || 
                          (typeof sourceLink.target === 'object' ? sourceLink.target.id : sourceLink.target);
                          
          if (!sourceId || !targetId || !targetNode) {
            console.error('Cannot identify relation references:', { sourceId, targetId, targetNode });
            this.showEditFeedback('Error: Could not identify the relation references', 'error');
            return;
          }
          
          // Store a copy of data needed for callback
          const metaEditData = {
            sourceId,
            targetId,
            targetNode,
            currentIndex: -1 // Will be set in callback to find the correct metaRelation
          };
          
          this.showEditDialog = true;
          this.editDialogCallback = (newValue) => {
            return this.editMetaRelationLabel(metaEditData, newValue);
          };
          
          this.closeContextMenu();
          return;
        }
        
        // Regular edge handling (existing code)
        // Try to get data from originalData first (more reliable)
        if (this.selectedElement && this.selectedElement.originalData) {
          console.log('Using originalData for editing:', this.selectedElement.originalData);
          const relation = this.selectedElement.originalData;
          this.editDialogValue = relation.label || '';
          
          // Store a copy of the original data for the callback
          const originalData = {...relation};
          
          this.showEditDialog = true;
          this.editDialogCallback = (newValue) => {
            console.log('New label value (from originalData):', newValue);
            // Find and update the relation directly
            const rel = this.graphData.relations.find(
              r => r.head === originalData.head && r.tail === originalData.tail
            );
            
            if (rel) {
              console.log('Found relation to update:', rel);
              rel.label = newValue;
              this.hasUnsavedChanges = true;
              
              // Update the visualization
              try {
                // Update the D3 element text
                this.svg.selectAll('.links g').each(function(d) {
                  if (!d) return;
                  
                  const linkSource = typeof d.source === 'object' && d.source ? d.source.id : d.source;
                  const linkTarget = typeof d.target === 'object' && d.target ? d.target.id : d.target;
                  
                  if (linkSource === originalData.head && linkTarget === originalData.tail) {
                    d.label = newValue;
                    // Update the text directly
                    d3.select(this).select('text').text(newValue);
                  }
                });
              } catch (e) {
                console.warn('Could not update link label directly, will re-render graph:', e);
                this.renderGraph();
              }
              
              console.log('Relation updated successfully (from originalData)');
              return true;
            } else {
              console.error('Could not find relation to update (from originalData)');
              this.showEditFeedback('Error: Could not find relation to update', 'error');
              return false;
            }
          };
        } 
        // Fall back to source/target approach if originalData is not available
        else if (this.selectedElement && this.selectedElement.source && this.selectedElement.target) {
          // Get the correct label from the relation
          const sourceId = typeof this.selectedElement.source === 'object' && this.selectedElement.source ? 
            this.selectedElement.source.id : this.selectedElement.source;
          const targetId = typeof this.selectedElement.target === 'object' && this.selectedElement.target ? 
            this.selectedElement.target.id : this.selectedElement.target;
          
          // Check if we have valid IDs
          if (!sourceId || !targetId) {
            console.error('Invalid source or target ID:', { selectedElement: this.selectedElement, sourceId, targetId });
            this.showEditFeedback('Error: Could not identify the relation', 'error');
            return;
          }
          
          console.log('Editing label for relation:', sourceId, targetId);
          
          // Find the relation in the original data to get the correct label
          const relation = this.graphData.relations.find(r => r.head === sourceId && r.tail === targetId);
          
          if (relation) {
            console.log('Found relation to edit:', relation);
            this.editDialogValue = relation.label || '';
          } else {
            console.log('Relation not found, using fallback label');
            this.editDialogValue = this.selectedElement.label || '';
          }
          
          // Store a reference to the selected element for use in the callback
          const selectedElement = {...this.selectedElement}; // Create a copy to avoid reference issues
          
          this.showEditDialog = true;
          this.editDialogCallback = (newValue) => {
            console.log('New label value:', newValue);
            // Use the stored reference to avoid issues if selectedElement changes
            return this.editRelationLabel(selectedElement, newValue);
          };
        } else {
          console.error('Cannot determine relation data for editing:', this.selectedElement);
          this.showEditFeedback('Error: Cannot edit this relation', 'error');
          return;
        }
        
        this.closeContextMenu();
        
        // Focus the input field after the dialog is shown
        this.$nextTick(() => {
          if (this.$refs.dialogInput) {
            this.$refs.dialogInput.focus();
          }
        });
      } catch (error) {
        console.error('Error in handleEditLabel:', error);
        this.showEditFeedback('Error preparing edit dialog', 'error');
      }
    },
    
    confirmEdit() {
      console.log('Confirming edit with value:', this.editDialogValue);
      
      try {
        // Call the callback with the current value
        if (this.editDialogCallback) {
          try {
            const result = this.editDialogCallback(this.editDialogValue);
            console.log('Edit callback result:', result);
            
            // 移除在Next按钮点击时显示成功消息的代码
            // 仅对实际进行保存操作的操作显示成功提示
            // 由各个具体的callback自己决定是否显示成功提示
          } catch (callbackError) {
            console.error('Error in edit callback:', callbackError);
            this.showEditFeedback(`Error: ${callbackError.message || 'Failed to save changes'}`, 'error');
          }
        }
      } catch (error) {
        console.error('Error in confirmEdit:', error);
        this.showEditFeedback('Error saving changes', 'error');
      } finally {
        // Always close the dialog, regardless of callback success
        this.showEditDialog = false;
        this.editDialogValue = '';
        this.editDialogCallback = null;
        
        console.log('Dialog closed after edit confirmation');
      }
    },
    
    cancelEdit() {
      this.showEditDialog = false;
      this.editDialogValue = '';
      this.editDialogCallback = null;
      
      // 如果此时处于创建连接状态，同时取消连接创建
      if (this.isCreatingConnection) {
        this.cancelConnectionCreation();
      }
      
      // 如果此时处于创建meta-relation状态，同时取消meta-relation创建
      if (this.isCreatingMetaRelation) {
        this.cancelMetaRelationCreation();
      }
    },
    
    renameNode(nodeId, newLabel) {
      console.log('Renaming node:', nodeId, 'to', newLabel);
      
      // Record current state before making changes
      this.recordCurrentState();
      
      // Update the node in the graph data
      if (!this.graphData.nodes) {
        console.error('No nodes array in graph data');
        return false;
      }
      
      const node = this.graphData.nodes.find(n => n.id === nodeId);
      if (node) {
        console.log('Found node to rename:', node);
        
        // Store the old ID before updating
        const oldId = node.id;
        
        // Update the node label and ID
        node.label = newLabel;
        node.id = newLabel; // Update the ID to match the new label
        
        // Also update any relations that use this node
        if (this.graphData.relations) {
          // Update all relations that reference this node
          this.graphData.relations.forEach(relation => {
            if (relation.head === oldId) {
              relation.head = newLabel;
            }
            if (relation.tail === oldId) {
              relation.tail = newLabel;
            }
          });
        }
        
        this.hasUnsavedChanges = true;
        
        // Force a complete re-render of the graph to ensure all references are updated
        this.renderGraph();
        
        // Log the updated graph data for debugging
        console.log('Updated graph data after rename:', JSON.stringify({
          nodes: this.graphData.nodes.map(n => ({ id: n.id, label: n.label })),
          relations: this.graphData.relations
        }, null, 2));
        
        return true;
      } else {
        console.error('Node not found for renaming:', nodeId);
        return false;
      }
    },
    
    deleteNode(nodeId) {
      console.log('Deleting node:', nodeId);
      
      // Record current state before making changes
      this.recordCurrentState();
      
      if (!this.graphData.nodes) {
        console.error('No nodes array in graph data');
        return;
      }
      
      // Check if node exists
      const nodeIndex = this.graphData.nodes.findIndex(n => n.id === nodeId);
      if (nodeIndex === -1) {
        console.error('Node not found for deletion:', nodeId);
        this.showEditFeedback('Error: Node not found', 'error');
        return;
      }
      
      // Check if this node is used in any relations
      const relationsUsingNode = this.graphData.relations.filter(
        rel => rel.head === nodeId || rel.tail === nodeId
      );
      
      if (relationsUsingNode.length > 0) {
        console.log('Node is used in relations, deleting these relations:', relationsUsingNode);
        
        // Delete all relations that use this node
        this.graphData.relations = this.graphData.relations.filter(
          rel => rel.head !== nodeId && rel.tail !== nodeId
        );
        
        this.hasUnsavedChanges = true;
      }
      
      // 新增：检查该节点是否被用作meta-relation的target
      const metaRelationsUsingNode = [];
      this.graphData.relations.forEach(rel => {
        if (rel.metaRelations && Array.isArray(rel.metaRelations)) {
          rel.metaRelations.forEach((meta, index) => {
            if (meta.target === nodeId) {
              metaRelationsUsingNode.push({
                relation: rel,
                metaIndex: index,
                meta: meta
              });
            }
          });
        }
      });
      
      // 如果存在引用该节点的meta-relation，删除这些meta-relation
      if (metaRelationsUsingNode.length > 0) {
        console.log('Node is used as target in meta-relations, removing these meta-relations first:', metaRelationsUsingNode);
        
        // 从每个关系中删除对应的meta-relation
        metaRelationsUsingNode.forEach(({ relation, metaIndex }) => {
          relation.metaRelations.splice(metaIndex, 1);
        });
        
        this.hasUnsavedChanges = true;
      }
      
      // Remove the node from the nodes array
      this.graphData.nodes.splice(nodeIndex, 1);
      this.hasUnsavedChanges = true;
      
      // Update the visualization
      this.renderGraph();
      
      this.showEditFeedback('Node and all its relations deleted successfully', 'success');
    },
    
    deleteRelation(relation) {
      // Add null check for relation
      if (!relation) {
        console.error('Cannot delete null relation');
        this.showEditFeedback('Error: Invalid relation data', 'error');
        return;
      }
      
      // Record current state before making changes
      this.recordCurrentState();
      
      try {
        let sourceId, targetId;
        
        // First try to use originalData if available (more reliable)
        if (relation.originalData) {
          console.log('Using originalData for deletion:', relation.originalData);
          sourceId = relation.originalData.head;
          targetId = relation.originalData.tail;
        } 
        // Fall back to source/target if originalData is not available
        else if (relation.source && relation.target) {
          // Get source and target IDs with null checks
          sourceId = typeof relation.source === 'object' && relation.source ? relation.source.id : relation.source;
          targetId = typeof relation.target === 'object' && relation.target ? relation.target.id : relation.target;
        } else {
          console.error('Relation does not have valid source/target or originalData:', relation);
          this.showEditFeedback('Error: Could not identify the relation to delete', 'error');
          return;
        }
        
        // Check if we have valid IDs
        if (!sourceId || !targetId) {
          console.error('Invalid source or target ID for deletion:', { relation, sourceId, targetId });
          this.showEditFeedback('Error: Could not identify the relation to delete', 'error');
          return;
        }
        
        console.log('Deleting relation:', sourceId, targetId);
        
        // Remove the relation from the graph data
        this.graphData.relations = this.graphData.relations.filter(
          r => !(r.head === sourceId && r.tail === targetId)
        );
        this.hasUnsavedChanges = true;
        this.renderGraph();
      } catch (error) {
        console.error('Error in deleteRelation:', error);
        this.showEditFeedback('Error deleting relation', 'error');
      }
    },
    
    addRelation(sourceId, targetId, label, text = '') {
      // Record the current state before making changes
      this.recordCurrentState();
      
      // Add new relation to the graph data
      this.graphData.relations.push({
        head: sourceId,
        tail: targetId,
        label: label,
        text: text
      });
      
      console.log(`Added relation: ${sourceId} -> ${targetId}, label: ${label}, text: ${text.substring(0, 50)}${text.length > 50 ? '...' : ''}`);
      
      this.hasUnsavedChanges = true;
      this.renderGraph();
    },
    
    addMetaRelation(sourceRelation, targetNodeId, label) {
      // Record the current state before making changes
      this.recordCurrentState();
      
      // First, we need to identify the parent relation in the graph data
      let sourceId, targetId;
      
      // Try to extract the source and target IDs from various properties
      if (sourceRelation.originalData) {
        sourceId = sourceRelation.originalData.head;
        targetId = sourceRelation.originalData.tail;
      } else if (sourceRelation.source && sourceRelation.target) {
        sourceId = typeof sourceRelation.source === 'object' ? sourceRelation.source.id : sourceRelation.source;
        targetId = typeof sourceRelation.target === 'object' ? sourceRelation.target.id : sourceRelation.target;
      } else {
        console.error('Could not determine source and target IDs for meta-relation', sourceRelation);
        this.showEditFeedback('Error: Could not create meta-relation', 'error');
        return;
      }
      
      // Find the parent relation in the graph data
      const relationIndex = this.graphData.relations.findIndex(
        rel => rel.head === sourceId && rel.tail === targetId
      );
      
      if (relationIndex === -1) {
        console.error('Could not find parent relation in graph data', { sourceId, targetId });
        this.showEditFeedback('Error: Could not find parent relation', 'error');
        return;
      }
      
      // Get the parent relation
      const parentRelation = this.graphData.relations[relationIndex];
      
      // Ensure metaRelations array exists
      if (!parentRelation.metaRelations) {
        parentRelation.metaRelations = [];
      }
      
      // Add the new meta-relation
      parentRelation.metaRelations.push({
        target: targetNodeId,
        label: label
      });
      
      // Mark changes as unsaved
      this.hasUnsavedChanges = true;
      
      // Show success message
      this.showEditFeedback('Meta-relation added successfully', 'success');
      
      // Re-render the graph
      this.renderGraph();
    },
    
    editRelationLabel(relation, newLabel) {
      // Check if relation is null or undefined
      if (!relation) {
        console.error('Relation is null or undefined');
        this.showEditFeedback('Error: Invalid relation data', 'error');
        return false;
      }

      // Record the current state before making changes
      this.recordCurrentState();

      try {
        let sourceId, targetId;

        // First try to get IDs from originalData
        if (relation.originalData) {
          sourceId = relation.originalData.head;
          targetId = relation.originalData.tail;
        }
        // Then try getting from source/target objects
        else if (relation.source && relation.target) {
          sourceId = relation.source.id || relation.source;
          targetId = relation.target.id || relation.target;
        }
        // Finally try direct source/target values
        else {
          sourceId = relation.source;
          targetId = relation.target;
        }

        // Validate that we have both IDs
        if (!sourceId || !targetId) {
          console.error('Invalid source or target ID:', { relation, sourceId, targetId });
          this.showEditFeedback('Error: Could not identify the relation', 'error');
          return false;
        }

        // Find and update the relation in the graph data
        const rel = this.graphData.relations.find(r => r.head === sourceId && r.tail === targetId);
        if (!rel) {
          console.error('Could not find relation to update');
          this.showEditFeedback('Error: Could not find relation to update', 'error');
          return false;
        }

        // Update the label
        rel.label = newLabel;
        this.hasUnsavedChanges = true;

        // Try to update the D3 visualization
        try {
          this.svg.selectAll('.links g').each(function(d) {
            if (!d) return;
            const linkSource = d.source?.id || d.source;
            const linkTarget = d.target?.id || d.target;
            
            if (linkSource === sourceId && linkTarget === targetId) {
              d.label = newLabel;
              d3.select(this).select('text').text(newLabel);
            }
          });
        } catch (e) {
          console.warn('Could not update link label directly, re-rendering graph:', e);
          this.renderGraph();
        }

        return true;
      } catch (error) {
        console.error('Error in editRelationLabel:', error);
        this.showEditFeedback('Error updating relation label', 'error');
        return false;
      }
    },
    
    handleSaveClick(event) {
      event.stopPropagation();
      event.preventDefault();
      
      if (!this.hasUnsavedChanges || this.saveStatus === 'saving') {
        return;
      }
      
      // Get all current nodes and relations from the graph
      const nodes = [];
      const relations = [];
      
      // Get nodes from the graph
      if (this.graphData && Array.isArray(this.graphData.nodes)) {
        this.graphData.nodes.forEach(node => {
          if (node && node.id) {
            nodes.push({
              id: node.id,
              label: node.label || node.id
            });
          }
        });
      }
      
      // Get relations from the graph
      if (this.graphData && Array.isArray(this.graphData.relations)) {
        this.graphData.relations.forEach(rel => {
          if (rel && rel.head && rel.tail) {
            const relationData = {
              head: rel.head,
              tail: rel.tail,
              label: rel.label || '',
              text: rel.text || ''
            };
            
            // Preserve metaRelations if they exist
            if (rel.metaRelations && Array.isArray(rel.metaRelations) && rel.metaRelations.length > 0) {
              relationData.metaRelations = rel.metaRelations;
            }
            
            relations.push(relationData);
          }
        });
      }
      
      const dataToSave = {
        nodes: nodes,
        relations: relations
      };
      
      this.saveStatus = 'saving';
      this.saveMessage = 'Saving changes...';
      
      // 获取当前用户信息和URL参数，以便添加到保存请求中
      const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
      
      // 处理hash路由URL (例如 {BACKEND_URL}/#/analysis?url=...&mode=temp)
      const hash = window.location.hash; 
      const queryString = hash.split('?')[1] || '';
      const urlParams = new URLSearchParams(queryString);
      
      // 正确获取查询参数
      const mode = urlParams.get('mode') || 'view';
      const targetUser = urlParams.get('user') || currentUser.username;
      const paperUrl = urlParams.get('url') || 'https://pubmed.ncbi.nlm.nih.gov/29795461';
      
      // 从paperUrl中提取PMID
      const pmid = paperUrl.replace(/\/$/, '').split('/').pop() || '';
      
      // 添加参数到图表数据中
      dataToSave.source = 'visualizer';
      dataToSave.pmid = pmid;
      dataToSave.username = currentUser.username;
      dataToSave.mode = mode;
      dataToSave.target_user = targetUser;
      
      axios.post(`${BACKEND_URL}/api/graph/save`, dataToSave)
        .then(() => {
          this.hasUnsavedChanges = false;
          this.saveStatus = 'saved';
          this.saveMessage = 'Changes saved successfully!';
          
          // 触发全局事件，通知其他组件（如PaperAnalysis）数据已更新
          const event = new CustomEvent('graph-data-updated', { 
            detail: { 
              pmid: pmid,
              username: currentUser.username,
              mode: mode,
              timestamp: new Date().getTime()
            } 
          });
          window.dispatchEvent(event);
          
          setTimeout(() => {
            if (this.saveStatus === 'saved') {
              this.saveStatus = '';
              this.saveMessage = '';
            }
          }, 3000);
        })
        .catch(err => {
          console.error('Error saving graph:', err);
          this.saveStatus = 'error';
          this.saveMessage = `Error saving: ${err.message}`;
        });
    },
    debugGraphData() {
      console.log('Current graph data:', this.graphData);
      if (this.graphData && this.graphData.relations) {
        console.log('Relations count:', this.graphData.relations.length);
        this.graphData.relations.forEach((rel, index) => {
          console.log(`Relation ${index}:`, rel);
        });
      }
    },
    showEditFeedback(message, type = 'success', duration = 3000) {
      this.editFeedback = {
        show: true,
        message,
        type
      };
      
      // 自动隐藏反馈信息
      clearTimeout(this._feedbackTimeout);
      this._feedbackTimeout = setTimeout(() => {
        this.editFeedback.show = false;
      }, duration);
    },
    editMetaRelationLabel(metaData, newLabel) {
      if (!metaData || !metaData.sourceId || !metaData.targetId || !metaData.targetNode) {
        console.error('Invalid meta relation data for editing:', metaData);
        this.showEditFeedback('Error: Invalid meta relation data', 'error');
        return false;
      }
      
      try {
        // Find the parent relation in the graph data
        const parentRelation = this.graphData.relations.find(
          r => r.head === metaData.sourceId && r.tail === metaData.targetId
        );
        
        if (!parentRelation) {
          console.error('Could not find parent relation for meta relation:', metaData);
          this.showEditFeedback('Error: Could not find parent relation', 'error');
          return false;
        }
        
        // Ensure metaRelations array exists
        if (!parentRelation.metaRelations) {
          parentRelation.metaRelations = [];
        }
        
        // Find the specific meta relation by target
        const metaIndex = parentRelation.metaRelations.findIndex(
          meta => meta.target === metaData.targetNode
        );
        
        if (metaIndex === -1) {
          console.error('Could not find meta relation in parent relation:', {
            parentRelation,
            targetNode: metaData.targetNode
          });
          this.showEditFeedback('Error: Could not find meta relation', 'error');
          return false;
        }
        
        // Update the label
        parentRelation.metaRelations[metaIndex].label = newLabel;
        this.hasUnsavedChanges = true;
        
        // Try to update the visualization directly
        try {
          // Update the D3 element directly
          this.svg.selectAll('.meta-link-group').each(function(d) {
            if (!d || !d.sourceLink || !d.target) return;
            
            const sourceLink = d.sourceLink;
            if (!sourceLink) return;
            
            const sourceId = sourceLink.originalData?.head || 
                          (typeof sourceLink.source === 'object' ? sourceLink.source.id : sourceLink.source);
            const targetId = sourceLink.originalData?.tail || 
                          (typeof sourceLink.target === 'object' ? sourceLink.target.id : sourceLink.target);
            
            if (sourceId === metaData.sourceId && 
                targetId === metaData.targetId && 
                d.target === metaData.targetNode) {
              
              // Update the data and text
              d.label = newLabel;
              d3.select(this).select('text').text(newLabel);
            }
          });
        } catch (e) {
          console.warn('Could not update meta link label directly, will re-render graph:', e);
          this.renderGraph();
        }
        
        return true;
      } catch (error) {
        console.error('Error in editMetaRelationLabel:', error);
        this.showEditFeedback('Error updating meta relation', 'error');
        return false;
      }
    },
    
    deleteMetaRelation(metaRelation) {
      if (!metaRelation || !metaRelation.sourceLink || !metaRelation.target) {
        console.error('Invalid meta relation for deletion:', metaRelation);
        this.showEditFeedback('Error: Invalid meta relation data', 'error');
        return;
      }
      
      // Record current state before making changes
      this.recordCurrentState();
      
      try {
        // Get the parent relation's source and target IDs
        const sourceLink = metaRelation.sourceLink;
        const targetNode = metaRelation.target;
        
        const sourceId = sourceLink.originalData?.head || 
                        (typeof sourceLink.source === 'object' ? sourceLink.source.id : sourceLink.source);
        const targetId = sourceLink.originalData?.tail || 
                        (typeof sourceLink.target === 'object' ? sourceLink.target.id : sourceLink.target);
                        
        if (!sourceId || !targetId) {
          console.error('Could not identify parent relation:', { sourceLink, sourceId, targetId });
          this.showEditFeedback('Error: Could not identify parent relation', 'error');
          return;
        }
        
        // Find the parent relation in the graph data
        const parentRelation = this.graphData.relations.find(
          r => r.head === sourceId && r.tail === targetId
        );
        
        if (!parentRelation) {
          console.error('Could not find parent relation for meta relation:', { sourceId, targetId });
          this.showEditFeedback('Error: Could not find parent relation', 'error');
          return;
        }
        
        // Check if metaRelations array exists
        if (!parentRelation.metaRelations || !Array.isArray(parentRelation.metaRelations)) {
          console.error('No metaRelations array in parent relation:', parentRelation);
          this.showEditFeedback('Error: No meta relations found', 'error');
          return;
        }
        
        // Find and remove the specific meta relation
        const initialLength = parentRelation.metaRelations.length;
        parentRelation.metaRelations = parentRelation.metaRelations.filter(
          meta => meta.target !== targetNode
        );
        
        // Check if anything was removed
        if (parentRelation.metaRelations.length === initialLength) {
          console.error('Could not find meta relation to delete:', { targetNode, parentRelation });
          this.showEditFeedback('Error: Could not find meta relation to delete', 'error');
          return;
        }
        
        this.hasUnsavedChanges = true;
        
        // Re-render the graph to reflect the changes
        this.renderGraph();
        
        this.showEditFeedback('Meta relation deleted successfully', 'success');
      } catch (error) {
        console.error('Error in deleteMetaRelation:', error);
        this.showEditFeedback('Error deleting meta relation', 'error');
      }
    },
    
    getRelationLabel(relation) {
      if (!relation) return 'Unknown';
      
      let sourceId, targetId, label;
      
      // Try to extract information from originalData first
      if (relation.originalData) {
        sourceId = relation.originalData.head;
        targetId = relation.originalData.tail;
        label = relation.originalData.label;
      }
      // Then try source/target objects
      else if (relation.source && relation.target) {
        sourceId = typeof relation.source === 'object' ? relation.source.id : relation.source;
        targetId = typeof relation.target === 'object' ? relation.target.id : relation.target;
        label = relation.label;
      }
      // Last resort
      else {
        sourceId = 'unknown';
        targetId = 'unknown';
        label = relation.label || '';
      }
      
      // Create a readable representation
      if (label) {
        return `${sourceId} → ${label} → ${targetId}`;
      } else {
        return `${sourceId} → ${targetId}`;
      }
    },
    
    // 添加辅助方法获取URL查询参数
    getQueryParam(name) {
      // 处理hash路由URL (例如 {BACKEND_URL}/#/analysis?url=...&mode=temp)
      const hash = window.location.hash;
      const queryString = hash.split('?')[1] || '';
      const urlParams = new URLSearchParams(queryString);
      return urlParams.get(name);
    },
    
    // 获取实体类型和名称的方法
    getEntityInfo(entityName) {
      console.log('获取实体信息:', entityName, this.entities[entityName])
      
      if (!this.entities || !this.entities[entityName] || !Array.isArray(this.entities[entityName])) {
        return 'NULL，NULL'
      }
      
      const entityInfo = this.entities[entityName]
      const type = entityInfo[0] || 'NULL'
      const name = entityInfo[1] || 'NULL'
      
      return `${type}，${name}`
    },
    
    // 显示实体tooltip
    showEntityTooltip(event, node) {
      // 获取节点的实体信息
      const entityInfo = this.getEntityInfo(node.id);
      
      // 创建或更新tooltip
      if (!this.nodeTooltip) {
        this.nodeTooltip = d3.select('body')
          .append('div')
          .attr('class', 'entity-node-tooltip')
          .style('opacity', 0)
          .style('position', 'absolute')
          .style('z-index', 10000)
          .style('background-color', '#707070')
          .style('color', 'white')
          .style('padding', '8px 12px')
          .style('border-radius', '4px')
          .style('pointer-events', 'none')
          .style('font-size', '14px')
          .style('box-shadow', '0 1px 5px rgba(0,0,0,0.2)');
      }
      
      // 设置tooltip内容和位置 - 只显示实体信息，不显示节点ID
      this.nodeTooltip
        .html(entityInfo)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 0.9);
    },
    
    // 隐藏tooltip
    hideEntityTooltip() {
      if (this.nodeTooltip) {
        this.nodeTooltip
          .transition()
          .duration(200)
          .style('opacity', 0);
      }
    },
    
    // 处理文本选择事件
    handleTextSelection() {
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const selectedText = range.toString().trim();
        
        if (selectedText) {
          // 保存选择的文本
          this.selectedSupportingText = selectedText;
          
          // 尝试获取选择的偏移量以便高亮显示
          const abstractContainer = document.querySelector('.abstract-container');
          if (abstractContainer) {
            // 计算选择在抽象文本中的位置
            const abstractText = this.paperAbstract;
            const selectedIndex = abstractText.indexOf(selectedText);
            
            if (selectedIndex !== -1) {
              this.selectionStartOffset = selectedIndex;
              this.selectionEndOffset = selectedIndex + selectedText.length;
              
              // 显示成功选择的提示
              this.showEditFeedback('Text selected successfully', 'success', 1000);
            }
          }
        }
      }
    },
    
    // 确认支持文本并完成添加关系
    confirmSupportingText() {
      if (this.pendingRelationData) {
        // 如果用户没有选择文本，显示确认对话框
        if (!this.selectedSupportingText) {
          this.confirmDialogTitle = 'No Supporting Text';
          this.confirmDialogMessage = 'You are about to add a relation without any supporting text. Do you want to continue?';
          this.showConfirmDialog = true;
          
          // 设置确认回调
          this.confirmDialogCallback = () => {
            this.addRelation(
              this.pendingRelationData.sourceId,
              this.pendingRelationData.targetId,
              this.pendingRelationData.label,
              ""
            );
            
            // 如果这是新节点添加流程的一部分，显示成功消息
            if (this.isAddingNode) {
              this.showEditFeedback('New node and relation added successfully', 'success');
              this.isAddingNode = false;
              this.pendingNodeData = null;
            } else {
              this.showEditFeedback('Relation added successfully', 'success');
            }
            
            this.cancelSupportingTextSelection();
            this.cancelConnectionCreation();
          };
          
          return;
        }
        
        // 正常添加关系，并包含支持文本
        this.addRelation(
          this.pendingRelationData.sourceId,
          this.pendingRelationData.targetId,
          this.pendingRelationData.label,
          this.selectedSupportingText
        );
        
        // 显示成功提示
        if (this.isAddingNode) {
          this.showEditFeedback('New node and relation added with supporting text', 'success');
          this.isAddingNode = false;
          this.pendingNodeData = null;
        } else {
          this.showEditFeedback('Relation added with supporting text', 'success');
        }
        
        // 清理状态
        this.cancelSupportingTextSelection();
        this.cancelConnectionCreation();
      }
    },
    
    // 确认对话框的确认操作
    confirmDialogAction() {
      if (this.confirmDialogCallback) {
        this.confirmDialogCallback();
      }
      this.showConfirmDialog = false;
      this.confirmDialogTitle = '';
      this.confirmDialogMessage = '';
      this.confirmDialogCallback = null;
    },
    
    // 取消确认对话框
    cancelConfirm() {
      this.showConfirmDialog = false;
      this.confirmDialogTitle = '';
      this.confirmDialogMessage = '';
      this.confirmDialogCallback = null;
    },
    
    // 取消支持文本选择
    cancelSupportingTextSelection() {
      this.showSupportingTextSelection = false;
      this.selectedSupportingText = '';
      this.selectionStartOffset = -1;
      this.selectionEndOffset = -1;
      this.pendingRelationData = null;
      
      // 不管是否在添加新节点，都取消连接创建状态
      this.cancelConnectionCreation();
      
      // 如果是在创建meta-relation，也一并取消
      if (this.isCreatingMetaRelation) {
        this.cancelMetaRelationCreation();
      }
    },
    
    // 开始文本选择
    startTextSelection() {
      // 清除之前的选择
      this.selectedSupportingText = '';
      this.selectionStartOffset = -1;
      this.selectionEndOffset = -1;
    },
    
    // 添加startAddNode方法
    startAddNode() {
      // 检查用户是否有权限编辑
      if (!this.canEdit) {
        const message = this.isAdmin ? 'View mode, cannot edit' : 'Only the owner user can edit';
        this.showEditFeedback(message, 'error');
        return;
      }
      
      // 显示节点名称输入对话框
      this.editDialogTitle = 'Enter Node Name';
      this.editDialogValue = '';
      this.showEditDialog = true;
      this.editDialogCallback = (nodeName) => {
        if (nodeName.trim() === '') {
          this.showEditFeedback('Node name cannot be empty', 'error');
          return false;
        }
        
        // 创建新节点
        const newNodeId = nodeName.trim();
        
        // 检查ID是否已存在
        const existingNode = this.graphData.nodes.find(node => node.id === newNodeId);
        if (existingNode) {
          this.showEditFeedback('Node with this ID already exists', 'error');
          return false;
        }
        
        // 创建节点但不立即添加到图上
        this.pendingNodeData = {
          id: newNodeId,
          label: newNodeId,
          x: this.width / 2, // 放在视图中央
          y: this.height / 2
        };
        
        // 立即开始连接创建流程
        this.startConnectionFromNewNode();
        return true;
      };
    },
    
    // 添加从新节点开始连接的方法
    startConnectionFromNewNode() {
      // 首先添加节点到图中以便可视化
      this.graphData.nodes.push(this.pendingNodeData);
      this.renderGraph(); // 重新渲染图以显示新节点
      
      // 模拟点击该节点以开始连接流程
      this.isCreatingConnection = true;
      this.sourceNode = this.pendingNodeData;
      
      // 添加视觉提示表明我们在连接模式
      this.svg.style('cursor', 'crosshair');
      
      // 添加临时预览线
      this.connectionPreview = this.svg.append('path')
        .attr('class', 'preview-connection')
        .attr('stroke', '#4a90e2')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('fill', 'none')
        .style('opacity', 0)
        .attr('marker-end', 'url(#end)');
        
      // 添加鼠标移动处理器
      this.svg.on('mousemove', (event) => {
        if (this.isCreatingConnection) {
          const [x, y] = d3.pointer(event);
          this.updateConnectionPreview(x, y);
        }
      });
      
      // 更新节点点击处理器来选择目标
      this.svg.selectAll('.node')
        .style('cursor', 'pointer')
        .on('click.connect', (event, d) => {
          if (this.isCreatingConnection && d.id !== this.sourceNode.id) {
            // 如果这是一个新节点连接，则设置isAddingNode标志
            this.isAddingNode = true;
            this.showRelationLabelDialog(d);
          }
        });
      
      // 显示连接取消按钮
      // 已经在模板中实现了
      
      // 显示成功消息
      this.showEditFeedback('New node added. Now connect it to another node.', 'success');
    },
    // Add undo, redo, and history tracking methods
    recordCurrentState() {
      // Create a deep copy of the current graph data to store in history
      const currentState = JSON.parse(JSON.stringify(this.graphData));
      
      // Add to history stack
      this.historyStack.push(currentState);
      
      // If history stack exceeds max size, remove oldest item
      if (this.historyStack.length > this.maxHistorySize) {
        this.historyStack.shift();
      }
      
      // Clear redo stack when new changes are made
      this.redoStack = [];
      
      // Set unsaved changes flag
      this.hasUnsavedChanges = true;
    },
    
    undo() {
      // Check if we have history to undo
      if (this.historyStack.length <= 1) return;
      
      // Get current state and save to redo stack
      const currentState = this.historyStack.pop();
      this.redoStack.push(currentState);
      
      // Apply previous state from history
      const previousState = this.historyStack[this.historyStack.length - 1];
      this.graphData = JSON.parse(JSON.stringify(previousState));
      
      // Set unsaved changes flag
      this.hasUnsavedChanges = true;
      
      // Re-render graph with previous state
      this.renderGraph();
      
      // Show feedback
      this.showEditFeedback('Undo successful', 'success');
    },
    
    redo() {
      // Check if we have changes to redo
      if (this.redoStack.length === 0) return;
      
      // Get next state from redo stack
      const nextState = this.redoStack.pop();
      
      // Add current state to history stack
      this.historyStack.push(nextState);
      
      // Apply the next state
      this.graphData = JSON.parse(JSON.stringify(nextState));
      
      // Set unsaved changes flag
      this.hasUnsavedChanges = true;
      
      // Re-render graph
      this.renderGraph();
      
      // Show feedback
      this.showEditFeedback('Redo successful', 'success');
    },
    // Handle keyboard shortcuts
    handleKeyDown(event) {
      // Only enable shortcuts if user has edit permission
      if (!this.canEdit) return;
      
      // Ctrl+Z: Undo
      if (event.ctrlKey && event.key === 'z') {
        event.preventDefault();
        this.undo();
      }
      
      // Ctrl+Y: Redo
      if (event.ctrlKey && event.key === 'y') {
        event.preventDefault();
        this.redo();
      }
    },
  },
  computed: {
    // 检查当前用户是否有权限编辑图表
    canEdit() {
      // 如果是管理员且处于view模式，不允许编辑
      if (this.isAdmin && this.getQueryParam('mode') === 'view') {
        return false;
      }
      
      // 如果是temp模式，允许编辑
      if (this.getQueryParam('mode') === 'temp') {
        return true;
      }
      
      // 否则检查当前用户是否是所属用户
      return this.getQueryParam('user') === this.currentUserName;
    },
    highlightedAbstract() {
      if (!this.paperAbstract || !this.selectedRelationText) {
        return this.paperAbstract;
      }
      
      // Escape special characters in the text for regex
      const escapedText = this.selectedRelationText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      
      // Create regex to match the text (case insensitive)
      const regex = new RegExp(`(${escapedText})`, 'gi');
      
      // Replace matches with highlighted version
      return this.paperAbstract.replace(regex, '<mark>$1</mark>');
    },
    highlightedAbstractForSelection() {
      if (!this.paperAbstract || this.selectionStartOffset === -1 || this.selectionEndOffset === -1) {
        return this.paperAbstract;
      }
      
      // 分成三部分：选择前、选择部分、选择后
      const beforeSelection = this.paperAbstract.substring(0, this.selectionStartOffset);
      const selectedPortion = this.paperAbstract.substring(this.selectionStartOffset, this.selectionEndOffset);
      const afterSelection = this.paperAbstract.substring(this.selectionEndOffset);
      
      // 使用更简单的标签包裹来减少布局影响
      return `${beforeSelection}<mark class="highlighted-text">${selectedPortion}</mark>${afterSelection}`;
    },
  }
};
</script>

<style>
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

/* Node highlighting */
.node.highlighted text {
  fill: #E74C3C !important;
  font-weight: bold;
}

/* Connected nodes */
.node.connected text {
  fill: #3498DB !important;
  font-weight: bold;
}

.node.dimmed {
  opacity: 0.4;
}

/* More aggressive circle hiding */
.node circle {
  display: none !important;
  opacity: 0 !important;
  r: 0 !important;
  visibility: hidden !important;
  pointer-events: none !important;
  stroke: none !important;
  fill: none !important;
}

/* Target all circles within the SVG */
svg circle {
  display: none !important;
  opacity: 0 !important;
  r: 0 !important;
  visibility: hidden !important;
}

/* Override D3.js default styles with higher specificity */
#graph svg .node circle,
.graph-container svg .node circle,
svg .nodes .node circle {
  display: none !important;
  opacity: 0 !important;
  r: 0 !important;
  visibility: hidden !important;
  pointer-events: none !important;
}

/* Link highlighting */
.link.highlighted {
  stroke: #E74C3C !important;
  stroke-width: 2px !important;
}

.link.dimmed {
  opacity: 0.2;
}

/* Meta link styling */
.meta-link {
  stroke: #9b59b6;
  stroke-width: 1.5px;
  stroke-dasharray: 3,3;
  cursor: pointer;
}

.meta-link.highlighted {
  stroke: #8e44ad !important;
  stroke-width: 2px !important;
}

.meta-link.dimmed {
  opacity: 0.2;
}

.meta-link-label {
  fill: #9b59b6;
  font-size: 10px;
  font-style: italic;
  cursor: pointer;
}

.meta-link-label.highlighted {
  fill: #8e44ad !important;
  font-weight: bold;
}

.meta-link-group {
  cursor: pointer;
}

.meta-link-group.highlighted path {
  stroke-width: 2px !important;
}

.meta-link-group.highlighted text {
  font-weight: bold;
}

.btn {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.btn:hover {
  background-color: #3a7bc8;
}

.btn:active {
  background-color: #2a6cb8;
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

.save-btn {
  background-color: #27ae60;
}

.save-btn:hover {
  background-color: #219a52;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* 确保确认对话框总是显示在最上层 */
.confirmation-dialog-overlay {
  z-index: 1100; /* 高于其他所有元素 */
}

.dialog {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  min-width: 300px;
}

.dialog h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.dialog input {
  width: 100%;
  padding: 8px;
  margin-bottom: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.dialog-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.dialog-buttons .btn {
  padding: 6px 12px;
}

.preview-connection {
  pointer-events: none;
}

.save-container {
  position: relative;
  display: flex;
  align-items: center;
}

.unsaved-indicator {
  color: #e74c3c;
  font-size: 20px;
  margin-left: 4px;
}

.save-message {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
}

.save-message.saved {
  background-color: #27ae60;
  color: white;
}

.save-message.error {
  background-color: #e74c3c;
  color: white;
}

.save-message.saving {
  background-color: #f1c40f;
  color: #2c3e50;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.connection-mode {
  position: absolute;
  top: 10px; /* 与controls对齐 */
  left: 10px; /* 放在左侧 */
  background-color: rgba(74, 144, 226, 0.9);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  pointer-events: none; /* 防止干扰鼠标事件 */
  max-width: calc(100% - 500px); /* 限制最大宽度，避免与右侧按钮重叠 */
}

/* 水平内联显示所有文本 */
.connection-message-inline {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none; /* 确保文本不会捕获鼠标事件 */
  user-select: none; /* 防止文本被选择 */
}

/* 只有Cancel按钮可以接收鼠标事件 */
.connection-mode .btn {
  pointer-events: auto;
}

.connection-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cancel-btn {
  background-color: #e74c3c;
}

.cancel-btn:hover {
  background-color: #c0392b;
}

.edit-feedback {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 10px 16px;
  border-radius: 4px;
  color: white;
  font-weight: bold;
  z-index: 1000;
  animation: fadeIn 0.3s ease-out;
}

.edit-feedback.success {
  background-color: #27ae60;
}

.edit-feedback.error {
  background-color: #e74c3c;
}

.edit-feedback.warning {
  background-color: #f39c12;
  color: #1e1e1e;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Relation text window styles */
.relation-text-window {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 600px;
  height: 520px;
  background-color: rgba(255, 255, 255, 0.6); /* 调整透明度以保持可读性 */
  border-radius: 8px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
  animation: fadeIn 0.3s ease-out;
  padding: 15px;
  border: 1px solid rgba(0, 0, 0, 0.2); /* 加深边框颜色增加边界可见度 */
}

.relation-text-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.2);
}

.paper-title {
  font-size: 16px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.95); /* 加深文字颜色 */
  line-height: 1.4;
  margin-right: 20px;
  flex: 1;
  max-height: 60px;
  overflow-y: auto;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8); /* 增强文字阴影 */
}

.relation-text-content {
  height: calc(100% - 70px);
  overflow-y: auto;
  line-height: 1.6;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.9); /* 加深文字颜色 */
  padding-right: 5px;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8); /* 增强文字阴影 */
}

/* 更新mark样式 */
mark {
  background-color: rgba(255, 215, 0, 0.5); /* 增加高亮背景不透明度 */
  padding: 2px 4px; /* 增加水平内边距 */
  border-radius: 3px;
  transition: background-color 0.2s;
  text-shadow: none;
  color: rgba(0, 0, 0, 1); /* 完全不透明的文字颜色 */
  box-shadow: 0 0 2px rgba(255, 255, 255, 0.5); /* 添加微弱阴影 */
}

mark:hover {
  background-color: rgba(255, 215, 0, 0.7);
}

/* 更新滚动条样式 */
.relation-text-content::-webkit-scrollbar-track,
.paper-title::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.relation-text-content::-webkit-scrollbar-thumb,
.paper-title::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.3);
}

.relation-text-content::-webkit-scrollbar-thumb:hover,
.paper-title::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.4);
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
  flex-shrink: 0;
  margin-top: -2px;
}

.close-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Meta-relation mode indicator styles */
.connection-mode.meta-relation-mode {
  background-color: rgba(142, 68, 173, 0.9);
  color: white;
}

.connection-message.meta-relation-mode {
  color: white;
}

.cancel-btn.meta-relation-mode {
  background-color: #c0392b;
}

.cancel-btn.meta-relation-mode:hover {
  background-color: #e74c3c;
}

/* 添加支持文本选择相关样式 */
.supporting-text-window {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 800px;
  height: 80%;
  max-height: 600px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.text-selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background-color: #4a90e2;
  color: white;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.text-selection-title {
  font-size: 18px;
  font-weight: 500;
}

.text-selection-content {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.text-selection-relation-info {
  text-align: center;
  margin-bottom: 10px;
  font-size: 15px;
  color: #333;
  padding: 6px;
  background-color: #f1f8ff;
  border-radius: 4px;
  border: 1px dashed #4a90e2;
}

.abstract-container {
  flex: 1;
  padding: 12px;
  background-color: #ffffff; /* 修改为纯白色背景 */
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 12px;
  overflow-y: auto;
  white-space: pre-wrap;
  user-select: text;
}

.text-selection-instruction {
  text-align: center;
  color: #666;
  margin-bottom: 16px;
  font-style: italic;
}

.text-selection-feedback {
  text-align: center;
  color: #27ae60;
  margin-bottom: 16px;
  font-weight: 500;
}

.selection-indicator {
  display: inline-block;
  width: 20px;
  height: 20px;
  background-color: #27ae60;
  color: white;
  border-radius: 50%;
  text-align: center;
  line-height: 20px;
  margin-right: 4px;
}

.text-selection-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 高亮文本样式 */
.highlighted-text {
  background-color: rgba(255, 165, 0, 0.35); /* 浅橙色背景 */
  border-radius: 2px;
  display: inline; /* 确保不影响文本流 */
  padding: 0; /* 移除内边距防止文本位置移动 */
  font-weight: normal; /* 保持原有字体粗细，不改变字体特性 */
  box-shadow: none; /* 移除阴影，防止影响布局 */
  color: inherit; /* 保持原有文本颜色 */
  text-shadow: none; /* 移除文本阴影 */
  white-space: pre-wrap; /* 保持原有的空白符处理 */
  pointer-events: auto; /* 允许鼠标事件 */
  transition: background-color 0.2s; /* 平滑过渡效果 */
}

.dialog p.confirm-message {
  margin-bottom: 16px;
  color: #555;
  line-height: 1.4;
}

/* Add UNDO/REDO buttons */
.history-controls {
  position: absolute;
  top: 50%;
  left: 20px;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 8px rgba(0,0,0,0.3);
  font-size: 24px;
  font-weight: bold;
  transition: all 0.2s ease;
}

.history-btn:not(:disabled):hover {
  transform: scale(1.1);
  box-shadow: 0 5px 12px rgba(0,0,0,0.3);
}

.undo-btn {
  background-color: #e74c3c; /* Red */
  color: white;
}

.undo-btn::before {
  content: '↩';
}

.redo-btn {
  background-color: #2ecc71; /* Green */
  color: white;
}

.redo-btn::before {
  content: '↪'; /* Unicode right arrow */
  font-size: 24px;
  line-height: 1;
}

.history-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style> 
