<template>
  <q-page class="admin-dashboard">
    <div class="page-content q-pa-md">
      <!-- Statistics Cards -->
      <div class="section-title q-my-md">Dashboard Overview</div>
      <div class="row q-col-gutter-md">
        <!-- Total Papers -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card bg-blue-1 cursor-pointer" @click="navigateToPaperPermissions">
            <div class="nav-icon">
              <q-icon name="open_in_new" size="1.2rem" color="primary" />
            </div>
            <q-tooltip>Click to manage permissions</q-tooltip>
            <q-card-section>
              <div class="text-h3 text-primary text-center">{{ dashboardStats.total_papers }}</div>
              <div class="text-subtitle1 text-center" style="font-size: 18px">Total Papers</div>
            </q-card-section>
            <q-card-section class="text-center q-pt-none">
              <q-icon name="article" size="2rem" color="primary" />
            </q-card-section>
          </q-card>
        </div>

        <!-- Await Curation -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card bg-purple-1 cursor-pointer" @click="navigateToCuration">
            <div class="nav-icon">
              <q-icon name="open_in_new" size="1.2rem" color="purple" />
            </div>
            <q-tooltip class="text-body1">Click to curate paper</q-tooltip>
            <q-card-section>
              <div class="text-h3 text-purple text-center">{{ dashboardStats.papers_need_curation }}</div>
              <div class="text-subtitle1 text-center" style="font-size: 18px">Await Curation</div>
            </q-card-section>
            <q-card-section class="text-center q-pt-none">
              <q-icon name="description" size="2rem" color="purple" />
            </q-card-section>
          </q-card>
        </div>

        <!-- Curated Papers -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card bg-green-1 cursor-pointer" @click="navigateToCuratedPapers">
            <div class="nav-icon">
              <q-icon name="open_in_new" size="1.2rem" color="green" />
            </div>
            <q-tooltip class="text-body1">Click to view curated papers</q-tooltip>
            <q-card-section>
              <div class="text-h3 text-green text-center">{{ dashboardStats.curated_papers }}</div>
              <div class="text-subtitle1 text-center" style="font-size: 18px">Curated Papers</div>
            </q-card-section>
            <q-card-section class="text-center q-pt-none">
              <q-icon name="library_books" size="2rem" color="green" />
            </q-card-section>
          </q-card>
        </div>

        <!-- Edit Submissions Today-->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card bg-orange-1">
            <q-card-section>
              <div class="text-h3 text-orange text-center">{{ dashboardStats.edit_submissions_today }}</div>
              <div class="text-subtitle1 text-center" style="font-size: 18px">Edit Submissions Today</div>
            </q-card-section>
            <q-card-section class="text-center q-pt-none">
              <q-icon name="edit_note" size="2rem" color="orange" />
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Pie Charts Section -->
      <div class="q-my-xl">
        <div class="section-title q-my-md">Progress</div>
        <div class="row q-col-gutter-md">
          <!-- Pie Chart 1: Edit Papers Ratio -->
          <div class="col-12 col-md-6">
            <q-card class="chart-card">
              <q-card-section>
                <div class="text-h6 q-mb-md" style="font-size: 24px">Progress Distribution</div>
                <div class="chart-container">
                  <canvas id="editPapersRatio" ref="editPapersRatio"></canvas>
                </div>
              </q-card-section>
            </q-card>
          </div>

          <!-- Pie Chart 2: Curation Needed Ratio -->
          <div class="col-12 col-md-6">
            <q-card class="chart-card">
              <q-card-section>
                <div class="text-h6 q-mb-md" style="font-size: 24px">Await Curation</div>
                <div class="chart-container">
                  <canvas id="curationRatio" ref="curationRatio"></canvas>
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </div>
      
      <!-- User Completion Overview -->
      <div class="q-my-xl">
        <div class="section-title q-my-md">User Completion Overview</div>
        <q-card class="chart-card">
          <q-card-section>
            <div v-if="userCompletionData.length === 0" class="text-center q-pa-lg">
              <q-spinner-dots color="primary" size="40px" />
              <div class="text-subtitle1 q-mt-sm">Loading user completion data...</div>
            </div>
            <div v-else class="user-completion-container">
              <div v-for="user in userCompletionData" :key="user.username" class="user-progress-row q-mb-md">
                <div class="user-name" :style="{ width: '100px', marginLeft: '-45px' }">{{ user.username }}</div>
                <div class="progress-bar-container">
                  <div 
                    v-if="user.assigned_papers > 0"
                    class="progress-bar" 
                    :style="{ 
                      width: `${Math.max(user.completion_rate, 5)}%`,
                      background: getProgressColor(user.completion_rate)
                    }"
                  >
                    <span class="progress-text">
                      {{ user.completion_rate }}% ({{ user.completed_papers }}/{{ user.assigned_papers }})
                    </span>
                  </div>
                  <div v-else class="no-progress">
                    No assigned papers
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Submission Trend Chart -->
      <div class="q-my-xl">
        <div class="section-title q-my-md">Submission Trend</div>
        <q-card class="chart-card">
          <q-card-section>
            <div class="text-h6 q-mb-md" style="font-size: 24px">Last 7 Days Submissions</div>
            <div class="chart-container">
              <!-- 使用实际数据渲染图表 -->
              <div class="chart-placeholder">
                <div class="chart-bars">
                  <div v-for="(value, index) in dashboardStats.last_7_days_submissions" 
                       :key="index" 
                       class="chart-bar" 
                       :style="{
                         height: (value*5 + 20)+'px',
                         background: getBarGradient(value),
                         opacity: value === 0 ? 0.5 : 1
                       }">
                    <span class="bar-value">{{ value }}</span>
                  </div>
                </div>
                <div class="chart-axis">
                  <div v-for="day in 7" :key="day" class="axis-tick">
                    {{ formatDate(day) }}
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Admin Actions -->
      <div class="section-title q-my-md">Admin Actions</div>
      <div class="row q-col-gutter-md">
        <!-- Type and Name Configuration -->
        <div class="col-12 col-md-4">
          <q-card class="action-card cursor-pointer" v-ripple @click="openKnowledgeBaseSelector">
            <q-card-section class="bg-primary text-white">
              <div class="text-h6">
                <q-icon name="list_alt" size="1.5rem" class="q-mr-sm"/>
                Knowledge Base
              </div>
            </q-card-section>
            <q-card-section class="card-content" style="font-size: 18px">
              <p>Modify available Knowledge Base or add new Knowledge Base.</p>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn flat color="primary" icon="edit" label="EDIT" />
            </q-card-actions>
          </q-card>
        </div>

        <!-- Prompt Configuration -->
        <div class="col-12 col-md-4">
          <q-card class="action-card cursor-pointer" v-ripple @click="openPromptEditor">
            <q-card-section class="bg-secondary text-white">
              <div class="text-h6">
                <q-icon name="psychology" size="1.5rem" class="q-mr-sm"/>
                Prompt Config
              </div>
            </q-card-section>
            <q-card-section class="card-content" style="font-size: 18px">
              <p>Modify or add new prompt templates.</p>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn flat color="secondary" icon="edit" label="EDIT" @click.stop="openPromptEditor" />
            </q-card-actions>
          </q-card>
        </div>

        <!-- Relations Curation -> Paper Crawling -->
        <div class="col-12 col-md-4">
          <q-card class="action-card cursor-pointer" v-ripple @click="openPaperCrawlingDialog">
            <q-card-section class="bg-deep-purple text-white">
              <div class="text-h6">
                <q-icon name="cloud_download" size="1.5rem" class="q-mr-sm"/>
                Paper Crawling
              </div>
            </q-card-section>
            <q-card-section class="card-content" style="font-size: 18px">
              <p>Single paper crawling analysis or batch paper crawling analysis from PubMed.</p>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn flat color="deep-purple" icon="download" label="CRAWL" @click.stop="openPaperCrawlingDialog" />
            </q-card-actions>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
  
  <!-- Knowledge Base Selector Dialog -->
  <q-dialog v-model="showKnowledgeBaseSelector" persistent>
    <q-card style="width: 900px; max-width: 95vw; max-height: 90vh;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Knowledge Base Options</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section style="max-height: 70vh; overflow: auto;">
        <div class="row q-col-gutter-md">
          <!-- Context Knowledge Base Option -->
          <div class="col-12 col-md-4 col-sm-6">
            <q-card class="selection-card cursor-pointer" v-ripple @click="openTypeNameEditor">
              <q-card-section class="bg-primary text-white">
                <div class="text-h6">
                  <q-icon name="category" size="1.5rem" class="q-mr-sm" />
                  Context Knowledge Base
                </div>
              </q-card-section>
              <q-card-section class="selection-card-content">
                <p>Configure Types and Names for the knowledge base relationships.</p>
              </q-card-section>
            </q-card>
          </div>
          
          <!-- Reserved for future knowledge base related features -->
          <div class="col-12 col-md-4 col-sm-6">
            <q-card class="selection-card cursor-pointer disabled-card">
              <q-card-section class="bg-grey-6 text-white">
                <div class="text-h6">
                  <q-icon name="source" size="1.5rem" class="q-mr-sm" />
                  Other Knowledge Base
                </div>
              </q-card-section>
              <q-card-section class="selection-card-content">
                <p>Additional knowledge base features coming soon.</p>
                <div class="coming-soon-badge">Coming Soon</div>
              </q-card-section>
            </q-card>
          </div>
          
          <!-- Add Knowledge Base Option -->
          <div class="col-12 col-md-4 col-sm-6">
            <q-card class="selection-card cursor-pointer add-card" v-ripple @click="showKnowledgeBaseOptions">
              <q-card-section class="bg-teal text-white">
                <div class="text-h6">
                  <q-icon name="add_circle" size="1.5rem" class="q-mr-sm" />
                  Add Knowledge Base
                </div>
              </q-card-section>
              <q-card-section class="selection-card-content">
                <p>Select node or relation knowledge base to add to system.</p>
                <div class="add-kb-icon">
                  <q-icon name="add" size="3rem" color="teal" class="pulse-icon" />
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- Type & Name Editor Dialog -->
  <q-dialog v-model="showTypeNameEditor" persistent>
    <q-card style="width: 900px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Type & Name Configuration</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section>
        <div class="row q-col-gutter-md">
          <!-- Type 列表 -->
          <div class="col-12 col-md-6">
            <q-card class="editor-card">
              <q-card-section class="bg-primary text-white">
                <div class="text-h6">
                  <q-icon name="category" size="1.2rem" class="q-mr-sm" />
                  Types
                </div>
              </q-card-section>
              
              <q-card-section>
                <q-input v-model="typeFilter" dense placeholder="Search types..." class="q-mb-md" clearable>
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
                
                <q-list bordered separator style="height: 250px; overflow-y: auto">
                  <q-item v-for="(type, index) in filteredTypeList" :key="index">
                    <q-item-section>
                      <q-input v-model="typeList[typeList.indexOf(type)]" dense />
                    </q-item-section>
                    <q-item-section side>
                      <q-btn flat round color="negative" icon="delete" @click="removeType(typeList.indexOf(type))" />
                    </q-item-section>
                  </q-item>
                  <q-item v-if="filteredTypeList.length === 0">
                    <q-item-section class="text-center text-grey">
                      No matching types found
                    </q-item-section>
                  </q-item>
                </q-list>
                
                <div class="q-mt-md">
                  <q-input 
                    v-model="newType" 
                    label="New Type" 
                    dense 
                    @keyup.enter="addType"
                    :hint="newType && !newType.trim() ? 'Type cannot be empty' : ''"
                  >
                    <template v-slot:append>
                      <q-btn round flat icon="add" color="primary" @click="addType" :disable="!newType.trim()" />
                    </template>
                  </q-input>
                </div>
              </q-card-section>
            </q-card>
          </div>
          
          <!-- Name 列表 -->
          <div class="col-12 col-md-6">
            <q-card class="editor-card">
              <q-card-section class="bg-secondary text-white">
                <div class="text-h6">
                  <q-icon name="label" size="1.2rem" class="q-mr-sm" />
                  Names
                </div>
              </q-card-section>
              
              <q-card-section>
                <q-input v-model="nameFilter" dense placeholder="Search names..." class="q-mb-md" clearable>
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
                
                <q-list bordered separator style="height: 250px; overflow-y: auto">
                  <q-item v-for="(name, index) in filteredNameList" :key="index">
                    <q-item-section>
                      <q-input v-model="nameList[nameList.indexOf(name)]" dense />
                    </q-item-section>
                    <q-item-section side>
                      <q-btn flat round color="negative" icon="delete" @click="removeName(nameList.indexOf(name))" />
                    </q-item-section>
                  </q-item>
                  <q-item v-if="filteredNameList.length === 0">
                    <q-item-section class="text-center text-grey">
                      No matching names found
                    </q-item-section>
                  </q-item>
                </q-list>
                
                <div class="q-mt-md">
                  <q-input 
                    v-model="newName" 
                    label="New Name" 
                    dense 
                    @keyup.enter="addName"
                    :hint="newName && !newName.trim() ? 'Name cannot be empty' : ''"
                  >
                    <template v-slot:append>
                      <q-btn round flat icon="add" color="secondary" @click="addName" :disable="!newName.trim()" />
                    </template>
                  </q-input>
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>
        
        <!-- 将按钮上移到这里 -->
        <div class="row justify-end q-mt-md">
          <q-btn label="CANCEL" color="negative" @click="onCancel" class="q-mr-sm" />
          <q-btn label="SAVE CHANGES" color="positive" @click="saveChanges" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- Prompt Editor Dialog -->
  <q-dialog v-model="showPromptEditor" persistent>
    <q-card style="width: 900px; max-width: 95vw; max-height: 90vh;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-center full-width">
          <div class="text-primary" style="font-size: 24px;">Analysis Prompt</div>
        </div>
      </q-card-section>
      
      <q-card-section class="q-py-md">
        <div class="row justify-between items-center q-mb-md">
          <q-btn 
            icon="arrow_back" 
            color="primary" 
            round 
            :disable="!hasMultiplePrompts"
            @click="switchPromptTemplate((safeCurrentIndex - 1 + promptTemplates.length) % promptTemplates.length)" 
          />
          <div class="text-h6 text-center system-prompt-label">
            {{ promptTemplates[safeCurrentIndex]?.name || 'v1.2' }}
            <span v-if="promptTemplates[safeCurrentIndex]?.isSystemPrompt" class="system-prompt-badge">
              (Current System Prompt) <q-icon name="check" color="green" size="sm" />
            </span>
          </div>
          <q-btn 
            icon="arrow_forward" 
            color="primary" 
            round 
            :disable="!hasMultiplePrompts"
            @click="switchPromptTemplate((safeCurrentIndex + 1) % promptTemplates.length)" 
          />
        </div>
        
        <div class="text-subtitle1 q-my-sm">
          <q-icon name="info" color="info" size="sm" class="q-mr-sm" />
          {{ promptTemplates[safeCurrentIndex]?.description || 'This prompt template is used for the initial analysis of scientific articles.' }}
        </div>
        
        <div class="q-mb-md prompt-editor-container" style="position: relative;">
          <!-- 加载指示器覆盖层 -->
          <div v-if="isLoadingPrompt" class="prompt-loading-overlay">
            <q-spinner-dots color="primary" size="40px" />
            <div class="text-subtitle1 q-mt-sm">Loading prompt configuration...</div>
          </div>
        
          <div class="prompt-wrapper">
            <q-input
              v-model="currentTemplateContent"
              type="textarea"
              filled
              autogrow
              placeholder="Enter the prompt template here"
              style="font-family: monospace;"
              class="prompt-textarea"
              :hint="currentTemplateStats || ''"
            />
          </div>
        </div>
        
        <!-- 按钮区域 -->
        <div class="row justify-between q-mt-md">
          <!-- 左侧按钮 -->
          <div>
            <q-btn 
              label="ADD PROMPT" 
              color="teal" 
              icon="add" 
              @click="openAddPromptDialog" 
              :disable="isLoadingPrompt"
              class="add-prompt-btn q-mr-sm"
            />
            <q-btn 
              label="SET AS SYSTEM PROMPT" 
              color="green" 
              icon="check_circle" 
              @click="setAsSystemPrompt" 
              :disable="isLoadingPrompt || promptTemplates[safeCurrentIndex]?.isSystemPrompt"
            />
          </div>
          
          <!-- 右侧按钮 -->
          <div>
            <q-btn label="CANCEL" color="negative" @click="onPromptCancel" class="q-mr-sm" :disable="isLoadingPrompt || isSavingPrompt" />
            <q-btn 
              label="SAVE CHANGES" 
              color="positive" 
              @click="savePromptChanges" 
              :loading="isSavingPrompt"
              :disable="isLoadingPrompt" 
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- Add Prompt Dialog -->
  <q-dialog v-model="showAddPromptDialog" persistent>
    <q-card style="width: 700px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Add New Prompt</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section>
        <q-input 
          v-model="newPromptName" 
          label="Prompt Name/Version" 
          filled 
          class="q-mb-md"
          hint="For example: v1.3, Custom Prompt, etc."
          :rules="[val => !!val || 'Name is required']"
        />
        
        <q-input 
          v-model="newPromptDescription" 
          label="Prompt Description" 
          filled 
          class="q-mb-md"
          hint="Brief description of what this prompt is used for"
          :rules="[val => !!val || 'Description is required']"
        />
        
        <q-input
          v-model="newPromptContent"
          type="textarea"
          filled
          autogrow
          label="Prompt Content"
          style="font-family: monospace;"
          class="prompt-textarea q-mb-md"
          hint="Enter the prompt template content"
          :rules="[val => !!val || 'Content is required']"
        />
        
        <div class="row justify-end q-mt-lg">
          <q-btn label="CANCEL" color="negative" v-close-popup class="q-mr-sm" />
          <q-btn label="ADD" color="positive" @click="addNewPrompt" :disable="!canAddPrompt" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>

  <!-- Paper Crawling Dialog -->
  <q-dialog v-model="showPaperCrawlingDialog" persistent>
    <q-card style="width: 900px; max-width: 95vw; max-height: 90vh;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Add Papers</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section>
        <div class="row q-mb-md items-center justify-center">
          <div class="col-grow" style="max-width: 800px; display: flex; gap: 16px; align-items: center">
            <q-input
              v-model="newPaperUrl"
              outlined
              class="col-grow url-input"
              label="Enter PubMed URL"
              @keyup.enter="handleSubmit"
              :loading="submitting"
            >
              <template v-slot:append>
                <q-btn color="primary" label="Add" :loading="submitting" @click="handleSubmit">
                  <template v-slot:loading>
                    <q-spinner-dots />
                  </template>
                </q-btn>
              </template>
            </q-input>
            <q-btn
              color="primary"
              :loading="batchSubmitting"
              @click="triggerFileInput"
              class="batch-scrape-btn"
            >
              <q-icon name="upload_file" class="q-mr-xs" size="20px" />
              Batch Upload
              <template v-slot:loading>
                <q-spinner-dots />
              </template>
              <q-tooltip class="tooltip-text">
                Please upload a .txt file with one PubMed URL per line
              </q-tooltip>
            </q-btn>
          </div>
          <!-- Hidden file input -->
          <input
            type="file"
            ref="fileInput"
            accept=".txt"
            style="display: none"
            @change="handleFileSelected"
          />
        </div>

        <!-- Scraping progress section -->
        <div v-if="showProgress" class="text-h6 q-mb-md text-center">
          <div class="row items-center justify-center">
            <div class="q-mr-sm">Processing Papers: {{ currentPosition + 1 }}/{{ totalPapers }}</div>
            <q-spinner color="primary" size="1.5em" />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- Knowledge Base Type Selection Dialog -->
  <q-dialog v-model="knowledgeBaseTypeDialogVisible" persistent>
    <q-card style="min-width: 820px; max-width: 90vw;">
      <q-card-section class="row items-center justify-between q-pb-none">
        <div class="text-h6"></div>
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pt-md">
        <div class="branch-container">
          <div class="central-node">
            <q-icon name="folder" size="3rem" color="primary" class="q-mb-sm" />
            <div class="text-center text-weight-medium">Select Knowledge Base Type</div>
          </div>
          
          <div class="branch-lines">
            <div class="line-left"></div>
            <div class="line-right"></div>
          </div>
          
          <div class="branch-options">
            <div class="branch-option branch-left">
              <q-card class="branch-card cursor-pointer" @click="selectKnowledgeBaseType('node')">
                <q-card-section class="bg-blue-7 text-white text-center">
                  <div class="text-h6">Add Node</div>
                </q-card-section>
                <q-card-section>
                  <div class="text-body1 q-mb-md text-center">Add Knowledge Base For Node</div>
                </q-card-section>
              </q-card>
            </div>
            
            <div class="branch-option branch-right">
              <q-card class="branch-card cursor-pointer" @click="selectKnowledgeBaseType('relation')">
                <q-card-section class="bg-teal-7 text-white text-center">
                  <div class="text-h6">Add Relations</div>
                </q-card-section>
                <q-card-section>
                  <div class="text-body1 q-mb-md text-center">Add Knowledge Base For Relation</div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>

  <!-- Knowledge Base Upload Dialog -->
  <q-dialog v-model="showUploadDialog" persistent>
    <q-card style="min-width: 500px">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">
          {{ uploadType === 'node' ? 'Upload Node Knowledge Base' : 'Upload Relation Knowledge Base' }}
        </div>
      </q-card-section>
      <q-card-section>
        <div class="text-subtitle1 q-mb-md">
          <q-icon name="info" color="info" class="q-mr-sm" />
          {{ uploadType === 'node' ? 'Your JSON file must include a key with value "nodes" as a dictionary and value as a list type variable, representing node names.' : 'Your JSON file must include a key with value "relations" as a dictionary and value as a list type variable, representing relation names.' }}
        </div>
        
        <!-- 修改知识库上传对话框中的数据展示区域 -->
        <div class="q-pa-md q-mb-md border-1 border-solid border-grey-5 rounded-borders knowledge-base-data-container">
          <div class="row items-center justify-between q-mb-sm">
            <div class="text-subtitle1 text-weight-medium">Current system {{ uploadType }} data:</div>
            <div class="text-caption bg-primary text-white q-px-sm q-py-xs rounded-borders" v-if="!loading && currentData.length > 0">
              {{ currentData.length }} {{ uploadType }} found
            </div>
          </div>
          
          <q-separator class="q-mb-md" />
          
          <div v-if="loading" class="column items-center q-py-md">
            <q-spinner color="primary" size="40px" />
            <div class="q-mt-sm">Loading data...</div>
          </div>
          
          <div v-else-if="currentData.length === 0" class="text-center q-py-lg text-grey">
            <q-icon name="info" size="2rem" color="grey-5" />
            <div class="q-mt-sm">No {{ uploadType }} data available in the system</div>
          </div>
          
          <template v-else>
            <div class="data-display-area q-px-sm">
              <div class="row wrap">
                <div v-for="(item, index) in paginatedData" :key="index" class="col-6 data-item q-py-xs">
                  {{ item }}
                </div>
              </div>
            </div>
            
            <div class="row justify-between items-center q-mt-md">
              <div class="text-grey text-italic">
                Showing {{ ((currentPage - 1) * pageSize) + 1 }} - {{ Math.min(currentPage * pageSize, currentData.length) }} of {{ currentData.length }} items
              </div>
              
              <div>
                <q-pagination
                  v-model="currentPage"
                  :max="totalPages"
                  :max-pages="5"
                  direction-links
                  boundary-links
                  color="primary"
                  size="sm"
                  @update:model-value="goToPage"
                />
              </div>
            </div>
          </template>
        </div>
        
        <!-- 隐藏的文件input -->
        <input
          type="file"
          ref="fileInput"
          accept=".json"
          style="display: none"
          @change="onFileSelected"
        />
        
        <div v-if="errorMessage" class="text-negative q-mt-sm">
          {{ errorMessage }}
        </div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn label="CANCEL" color="negative" flat v-close-popup @click="resetUploadForm" />
        <q-btn 
          label="UPLOAD" 
          color="primary" 
          @click="triggerFileUpload"
          :loading="uploading"
          :disable="uploading"
        >
          <q-tooltip>Click to upload json file.</q-tooltip>
          <template v-slot:loading>
            <q-spinner-dots />
          </template>
        </q-btn>
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { BACKEND_URL } from '../config/api'

interface ChartContext {
  label?: string;
  raw: number;
  dataset: {
    data: number[];
  };
}

// 添加用户完成率数据接口
interface UserCompletionItem {
  username: string;
  assigned_papers: number;
  completed_papers: number;
  completion_rate: number;
}

// 声明Chart.js的类型，解决TypeScript报错
interface ChartConfig {
  type: string;
  data: {
    labels: string[];
    datasets: Array<{
      data: number[];
      backgroundColor: string[];
      borderColor: string[];
      borderWidth: number;
    }>;
  };
  options: {
    responsive: boolean;
    maintainAspectRatio: boolean;
    plugins: {
      legend: {
        display: boolean;
        position?: string;
        align?: string;
        labels?: {
          boxWidth?: number;
          font?: {
            size?: number;
          };
          color?: string;
        };
      };
      tooltip: {
        callbacks: {
          label: (context: ChartContext) => string;
        };
      };
    };
  };
}

interface ChartInstance {
  // Chart实例的最小接口
  update: () => void;
  destroy: () => void;
}

// 扩展HTMLCanvasElement，添加__chartInstance属性
interface ExtendedHTMLCanvasElement extends HTMLCanvasElement {
  __chartInstance?: ChartInstance | undefined;
}

interface ChartType {
  new(element: HTMLCanvasElement, config: ChartConfig): ChartInstance;
}

declare global {
  interface Window {
    Chart?: ChartType;
  }
}

export default defineComponent({
  name: 'AdminDashboard',

  setup() {
    const $q = useQuasar()
    const router = useRouter()
    
    const editPapersRatio = ref(null);
    const curationRatio = ref(null);
    const showTypeNameEditor = ref(false)
    const showPromptEditor = ref(false)
    const showKnowledgeBaseSelector = ref(false)
    
    // 知识库上传相关变量
    const showKbOptions = ref(false);
    const showUploadDialog = ref(false);
    const uploadType = ref<'node' | 'relation'>('node');
    const uploadFile = ref(null);
    const currentData = ref([]);
    const loading = ref(false);
    const errorMessage = ref('');
    
    // 知识库上传相关方法
    const showKnowledgeBaseOptions = () => {
      knowledgeBaseTypeDialogVisible.value = true;
      showKnowledgeBaseSelector.value = false;
    };
    
    const openUploadDialog = async (type: 'node' | 'relation') => {
      uploadType.value = type;
      knowledgeBaseTypeDialogVisible.value = false;
      showUploadDialog.value = true;
      resetUploadForm();
      await fetchKnowledgeBaseData(type);
    };
    
    const fetchKnowledgeBaseData = async (type: 'node' | 'relation') => {
      loading.value = true;
      try {
        // 根据类型调用不同的API端点
        const endpoint = type === 'node' ? '/api/knowledge-base/nodes' : '/api/knowledge-base/relations';
        console.log(`Fetching ${type} data from endpoint: ${endpoint}`);
        
        const response = await axios.get(getApiUrl(endpoint));
        currentData.value = type === 'node' ? response.data.nodes : response.data.relations;
        console.log(`Received ${currentData.value.length} ${type} items`);
      } catch (error) {
        console.error(`Failed to fetch ${type} data:`, error);
        $q.notify({
          type: 'negative',
          message: `Failed to fetch current ${type} data`,
          position: 'top',
          html: true
        });
        currentData.value = [];
      } finally {
        loading.value = false;
      }
    };
    
    const resetUploadForm = () => {
      uploadFile.value = null;
      errorMessage.value = '';
    };
    
    // 使用空函数参数，完全不关心参数内容
    const onRejected = () => {
      // 当文件被拒绝时（例如不是JSON文件）
      errorMessage.value = 'Please select a valid JSON file';
    };
    
    const uploadKnowledgeBase = async () => {
      if (!uploadFile.value) return;
      
      try {
        const formData = new FormData();
        formData.append('file', uploadFile.value);
        formData.append('type', uploadType.value);
        
        const response = await axios.post(getApiUrl('/api/upload-knowledge-base'), formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // 显示更详细的成功通知，包括新增和已存在的项目数量
        $q.notify({
          type: 'positive',
          message: response.data.message || `${uploadType.value === 'node' ? 'Node' : 'Relation'} knowledge base updated successfully`,
          position: 'top',
          html: true,
          timeout: 4000
        });
        
        // 更新显示的数据
        await fetchKnowledgeBaseData(uploadType.value);
        
        // 只重置表单状态，不关闭对话框
        resetUploadForm();
        // showUploadDialog.value = false; // 移除这行
      } catch (error: unknown) {
        console.error('Failed to upload knowledge base:', error);
        
        // 使用类型守卫检查error是否有response属性
        if (error && typeof error === 'object' && 'response' in error && 
            error.response && typeof error.response === 'object' && 'data' in error.response) {
          const response = error.response as { status: number; data: { message?: string } };
          
          // 根据不同的错误状态码提供不同的错误信息
          if (response.status === 400) {
            errorMessage.value = 'Invalid JSON file format. Please check and try again.';
          } else {
            errorMessage.value = response.data.message || 'Failed to upload knowledge base. Please try again.';
          }
        } else {
          errorMessage.value = 'An unexpected error occurred. Please try again.';
        }
        
        // 显示错误通知
        $q.notify({
          type: 'negative',
          message: errorMessage.value,
          position: 'top',
          html: true,
          timeout: 3000  // 设置为3秒后自动消失
        });
      }
    };
    
    // 添加API URL生成函数
    const getApiUrl = (endpoint: string) => {
      return `${BACKEND_URL}${endpoint}`;
    };
    
    // 添加仪表盘统计数据
    const dashboardStats = ref({
      total_papers: 0,
      papers_need_curation: 0,
      total_edit_papers: 0,
      curated_papers: 0,
      edit_submissions_today: 0,
      last_7_days_submissions: [0, 0, 0, 0, 0, 0, 0] // 添加过去7天的数据
    });
    
    // 添加加载仪表盘数据的函数
    const loadDashboardStats = async () => {
      try {
        console.log("开始加载仪表盘数据...");
        // 动态构建API URL，适应不同环境
        const apiUrl = getApiUrl('/api/admin/dashboard-stats');
        console.log("请求API地址:", apiUrl);
        
        const response = await axios.get(apiUrl);
        console.log("API响应数据:", response.data);
        
        // 确保所有需要的字段都存在，使用默认值填充缺失字段
        dashboardStats.value = {
          total_papers: response.data.total_papers || 0,
          papers_need_curation: response.data.papers_need_curation || 0,
          total_edit_papers: response.data.total_edit_papers || 0,
          curated_papers: response.data.curated_papers || 0,
          edit_submissions_today: response.data.edit_submissions_today || 0,
          last_7_days_submissions: response.data.last_7_days_submissions || [0, 0, 0, 0, 0, 0, 0]
        };
        
        console.log("处理后的仪表盘数据:", dashboardStats.value);
        
        // 数据加载完成后重新生成图表
        setTimeout(() => {
          if (window.Chart) {
            console.log("开始重绘图表...");
            try {
              // 先销毁已有的图表实例
              const chartElements = document.querySelectorAll('canvas');
              chartElements.forEach(element => {
                const chartInstance = (element as ExtendedHTMLCanvasElement).__chartInstance;
                if (chartInstance) {
                  chartInstance.destroy();
                  (element as ExtendedHTMLCanvasElement).__chartInstance = undefined;
                }
              });
              
              // 重新绘制图表
              drawEditPapersRatioChart();
              drawCurationRatioChart();
              console.log("图表绘制完成");
            } catch (chartError) {
              console.error("绘制图表时出错:", chartError);
            }
          } else {
            console.log("Chart.js未加载，无法绘制图表");
          }
        }, 200); // 设置短暂延迟确保DOM更新
      } catch (error) {
        console.error('加载仪表盘数据失败:', error);
        // 错误时显示通知
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to load dashboard statistics</span>',
          position: 'top',
          html: true,
          timeout: 3000
        });
      }
    };
    
    // Type & Name配置数据
    const typeList = ref<string[]>([]);
    const nameList = ref<string[]>([]);
    const newType = ref('');
    const newName = ref('');
    const originalTypeList = ref<string[]>([]);
    const originalNameList = ref<string[]>([]);
    const typeFilter = ref('');
    const nameFilter = ref('');

    // 使用标志位防止循环更新
    let isUpdatingType = false;
    let isUpdatingName = false;
    
    // 筛选后的类型列表
    const filteredTypeList = computed(() => {
      if (!typeFilter.value) return typeList.value;
      return typeList.value.filter(type => 
        type.toLowerCase().includes(typeFilter.value.toLowerCase())
      );
    });

    // 筛选后的名称列表  
    const filteredNameList = computed(() => {
      if (!nameFilter.value) return nameList.value;
      return nameList.value.filter(name => 
        name.toLowerCase().includes(nameFilter.value.toLowerCase())
      );
    });

    // 监听新类型输入，自动过滤类型列表
    watch(newType, (val) => {
      if (!isUpdatingType) {
        isUpdatingType = true;
        typeFilter.value = val;
        setTimeout(() => {
          isUpdatingType = false;
        }, 0);
      }
    });
    
    // 监听新名称输入，自动过滤名称列表
    watch(newName, (val) => {
      if (!isUpdatingName) {
        isUpdatingName = true;
        nameFilter.value = val;
        setTimeout(() => {
          isUpdatingName = false;
        }, 0);
      }
    });
    
    // 监听搜索框值变化，同步到新增输入框
    watch(typeFilter, (val) => {
      if (!isUpdatingType) {
        isUpdatingType = true;
        newType.value = val;
        setTimeout(() => {
          isUpdatingType = false;
        }, 0);
      }
    });
    
    watch(nameFilter, (val) => {
      if (!isUpdatingName) {
        isUpdatingName = true;
        newName.value = val;
        setTimeout(() => {
          isUpdatingName = false;
        }, 0);
      }
    });

    // 格式化日期函数，将天数转换为近7天的日期 (MM-DD格式)
    const formatDate = (day: number) => {
      const date = new Date();
      date.setDate(date.getDate() - (7 - day));
      return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
    };

    // Navigation functions
    const navigateToTypeAndName = () => {
      // router.push('/admin/type-name-config')
    }

    const navigateToPrompt = () => {
      // 已弃用，改为直接在页面打开对话框
    }

    const navigateToCuration = () => {
      router.push('/relations-curation')
    }

    const navigateToCuratedPapers = () => {
      router.push('/curated-papers')
    }

    const navigateToPaperPermissions = () => {
      router.push('/paper-permissions')
    }

    // 打开知识库选择器
    const openKnowledgeBaseSelector = () => {
      showKnowledgeBaseSelector.value = true
    }

    const openTypeNameEditor = () => {
      showTypeNameEditor.value = true
      showKnowledgeBaseSelector.value = false
      // 打开对话框时加载配置数据
      loadConfig()
    }
    
    // 加载配置数据
    const loadConfig = async () => {
      try {
        const response = await axios.get(getApiUrl('/api/type-name-config'));
        typeList.value = [...response.data.type];
        nameList.value = [...response.data.name];
        // 保存原始数据以便取消时恢复
        originalTypeList.value = [...response.data.type];
        originalNameList.value = [...response.data.name];
      } catch (error) {
        console.error('Failed to load configuration:', error);
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to load configuration</span>',
          position: 'top',
          html: true
        });
      }
    };
    
    // 添加新的Type
    const addType = () => {
      if (newType.value.trim()) {
        typeList.value.push(newType.value.trim());
        newType.value = '';
        typeFilter.value = ''; // 清除筛选，显示完整列表
      }
    };
    
    // 移除Type
    const removeType = (index: number) => {
      typeList.value.splice(index, 1);
    };
    
    // 添加新的Name
    const addName = () => {
      if (newName.value.trim()) {
        nameList.value.push(newName.value.trim());
        newName.value = '';
        nameFilter.value = ''; // 清除筛选，显示完整列表
      }
    };
    
    // 移除Name
    const removeName = (index: number) => {
      nameList.value.splice(index, 1);
    };
    
    // 保存更改
    const saveChanges = async () => {
      try {
        await axios.put(getApiUrl('/api/type-name-config'), {
          type: typeList.value,
          name: nameList.value
        });
        
        $q.notify({
          type: 'positive',
          message: '<span style="font-size: 18px;">Type & Name configuration saved successfully</span>',
          position: 'top',
          html: true
        });
        
        // 更新原始数据
        originalTypeList.value = [...typeList.value];
        originalNameList.value = [...nameList.value];
        
        // 关闭对话框
        showTypeNameEditor.value = false;
      } catch (error) {
        console.error('Failed to save configuration:', error);
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to save configuration</span>',
          position: 'top',
          html: true
        });
      }
    };
    
    // 取消编辑
    const onCancel = () => {
      // 恢复原始数据
      typeList.value = [...originalTypeList.value];
      nameList.value = [...originalNameList.value];
      // 关闭对话框
      showTypeNameEditor.value = false;
    };

    const onTypeNameSaved = () => {
      $q.notify({
        type: 'positive',
        message: '<span style="font-size: 18px;">Type & Name configuration saved successfully</span>',
        position: 'top',
        html: true
      })
      showTypeNameEditor.value = false
    }

    // Prompt配置数据
    const promptTemplate = ref('');
    const jsonPromptTemplate = ref('');
    const originalPromptTemplate = ref('');
    const originalJsonPromptTemplate = ref('');
    const currentPromptIndex = ref(0);
    const isLoadingPrompt = ref(false);
    const isSavingPrompt = ref(false);
    
    // 新的提示模板数据结构
    const promptTemplates = ref<Array<{
      name: string;
      description: string;
      content: string;
      isDefault?: boolean;
      isSystemPrompt?: boolean;
    }>>([
      {
        name: 'v1.2',
        description: 'This prompt template is used for the initial analysis of scientific articles.',
        content: '',
        isDefault: true,
        isSystemPrompt: true
      }
    ]);
    
    // 确保当前模板索引始终有效
    const safeCurrentIndex = computed(() => {
      if (currentPromptIndex.value >= 0 && currentPromptIndex.value < promptTemplates.value.length) {
        return currentPromptIndex.value;
      }
      return 0; // 默认返回第一个
    });
    
    // 获取当前模板内容的计算属性
    const currentTemplateContent = computed({
      get: () => {
        const template = promptTemplates.value[safeCurrentIndex.value];
        return template ? template.content : '';
      },
      set: (newValue: string) => {
        if (safeCurrentIndex.value < promptTemplates.value.length) {
          const template = promptTemplates.value[safeCurrentIndex.value];
          if (template) {
            template.content = newValue;
          }
        }
      }
    });
    
    // 计算当前模板的行数和字符数
    const currentTemplateStats = computed(() => {
      const content = currentTemplateContent.value;
      if (!content) return '';
      
      const lines = content.split('\n').length;
      const chars = content.length;
      return `${lines} lines, ${chars} characters`;
    });
    
    // 添加新提示相关
    const showAddPromptDialog = ref(false);
    const newPromptName = ref('');
    const newPromptDescription = ref('');
    const newPromptContent = ref('');
    
    // 检查是否可以添加新的提示
    const canAddPrompt = computed(() => {
      return newPromptName.value.trim() !== '' && 
             newPromptDescription.value.trim() !== '' && 
             newPromptContent.value.trim() !== '';
    });
    
    // 计算是否有多个prompt模板可供切换
    const hasMultiplePrompts = computed(() => {
      return promptTemplates.value.length > 1;
    });
    
    // 打开添加提示对话框
    const openAddPromptDialog = () => {
      newPromptName.value = '';
      newPromptDescription.value = '';
      newPromptContent.value = '';
      showAddPromptDialog.value = true;
    };
    
    // 添加新的提示模板
    const addNewPrompt = () => {
      if (canAddPrompt.value) {
        // 添加新模板到前端内存中
        promptTemplates.value.push({
          name: newPromptName.value,
          description: newPromptDescription.value,
          content: newPromptContent.value,
          isSystemPrompt: false
        });
        
        // 切换到新添加的提示
        currentPromptIndex.value = promptTemplates.value.length - 1;
        
        // 关闭对话框
        showAddPromptDialog.value = false;
        
        // 记录到控制台
        console.log('添加新的提示模板（仅前端临时存储）:', {
          name: newPromptName.value,
          description: newPromptDescription.value,
          contentLength: newPromptContent.value.length
        });
        
        // 提示添加成功
        $q.notify({
          type: 'positive',
          message: '<span style="font-size: 18px;">New prompt added successfully</span>',
          position: 'top',
          html: true,
          timeout: 2000
        });
      }
    };

    // 打开Prompt编辑器
    const openPromptEditor = () => {
      showPromptEditor.value = true
      loadPromptConfig()
      // 不再强制显示第一个模板，而是让loadPromptConfig自动选择System Prompt
    }
    
    // 加载Prompt配置
    const loadPromptConfig = async () => {
      isLoadingPrompt.value = true;
      try {
        // 从后端获取初始配置
        const response = await axios.get(getApiUrl('/api/prompt-config'));
        
        // 保存原始数据
        originalPromptTemplate.value = response.data.PROMPT_TEMPLATE;
        originalJsonPromptTemplate.value = response.data.JSON_PROMPT_TEMPLATE || '';
        
        // 获取保存在localStorage中的系统Prompt名称
        const savedSystemPromptName = localStorage.getItem('currentSystemPromptName') || 'v1.2';
        
        // 更新默认提示模板的内容
        if (promptTemplates.value.length > 0 && promptTemplates.value[0]) {
          promptTemplates.value[0].content = response.data.PROMPT_TEMPLATE;
          // 只有在首次加载时（仅有一个默认模板）才自动设置v1.2为系统Prompt
          if (promptTemplates.value.length === 1) {
            promptTemplates.value[0].isSystemPrompt = true;
            localStorage.setItem('currentSystemPromptName', 'v1.2');
          } else {
            // 否则根据保存的设置恢复系统Prompt状态
            promptTemplates.value.forEach(template => {
              template.isSystemPrompt = template.name === savedSystemPromptName;
            });
          }
        }
        
        // 保存到临时变量备用
        promptTemplate.value = response.data.PROMPT_TEMPLATE;
        jsonPromptTemplate.value = response.data.JSON_PROMPT_TEMPLATE || '';
        
        console.log('从后端加载了初始Prompt配置，当前系统Prompt：', savedSystemPromptName);
        
        // 找到并显示系统Prompt模板
        const systemPromptIndex = promptTemplates.value.findIndex(template => template.isSystemPrompt);
        if (systemPromptIndex !== -1) {
          // 设置当前索引为系统Prompt的索引
          currentPromptIndex.value = systemPromptIndex;
          console.log('自动切换到系统Prompt模板，索引：', systemPromptIndex);
        }
        
      } catch (error) {
        console.error('Failed to load prompt configuration:', error);
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to load prompt configuration</span>',
          position: 'top',
          html: true
        });
      } finally {
        isLoadingPrompt.value = false;
      }
    };
    
    // 保存Prompt更改
    const savePromptChanges = async () => {
      isSavingPrompt.value = true;
      try {
        // 从当前选择的提示模板中获取内容
        const currentContent = currentTemplateContent.value;
        
        // 查找当前设置为系统Prompt的模板
        const systemPromptTemplate = promptTemplates.value.find(t => t.isSystemPrompt);
        const systemPromptName = systemPromptTemplate?.name || 'v1.2';
        
        // 保存当前系统Prompt名称到localStorage
        if (systemPromptTemplate) {
          localStorage.setItem('currentSystemPromptName', systemPromptName);
        }
        
        // 模拟保存延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 不实际发送到后端，只在前端内存中保存
        console.log('模拟保存到后端，当前内容：', currentContent);
        console.log('当前系统Prompt：', systemPromptName);
        console.log('注意：这只是前端缓存，刷新页面后将恢复到原始状态');
        
        // 更新原始数据（仅UI展示用）
        originalPromptTemplate.value = currentContent;
        
        $q.notify({
          type: 'positive',
          message: '<span style="font-size: 18px;">Prompt configuration saved Successfully</span>',
          position: 'top',
          html: true,
          timeout: 2000
        });
        
        // 关闭对话框
        showPromptEditor.value = false;
      } catch (error) {
        console.error('Failed to save prompt configuration:', error);
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to save prompt configuration</span>',
          position: 'top',
          html: true
        });
      } finally {
        isSavingPrompt.value = false;
      }
    };
    
    // 取消Prompt编辑
    const onPromptCancel = () => {
      console.log('取消编辑，恢复初始状态');
      
      // 获取保存在localStorage中的系统Prompt名称
      const savedSystemPromptName = localStorage.getItem('currentSystemPromptName') || 'v1.2';
      
      // 恢复原始数据
      if (promptTemplates.value.length > 0 && promptTemplates.value[0]) {
        promptTemplates.value[0].content = originalPromptTemplate.value;
        // 恢复系统Prompt状态
        promptTemplates.value.forEach(template => {
          template.isSystemPrompt = template.name === savedSystemPromptName;
        });
      }
      jsonPromptTemplate.value = originalJsonPromptTemplate.value;
      
      // 移除所有非默认的提示模板（只保留第一个）
      promptTemplates.value = promptTemplates.value.filter(template => template.isDefault);
      
      // 重置当前索引
      currentPromptIndex.value = 0;
      
      // 如果默认模板是系统Prompt，则恢复其状态
      if (savedSystemPromptName === 'v1.2' && promptTemplates.value.length > 0 && promptTemplates.value[0]) {
        promptTemplates.value[0].isSystemPrompt = true;
      }
      
      // 关闭对话框
      showPromptEditor.value = false;
      
      // 提示用户操作已取消
      $q.notify({
        type: 'info',
        message: '<span style="font-size: 18px;">Edit cancelled</span>',
        position: 'top',
        html: true,
        timeout: 1000
      });
    };
    
    // 切换提示模板
    const switchPromptTemplate = (index: number) => {
      if (index >= 0 && index < promptTemplates.value.length) {
        currentPromptIndex.value = index;
        // 使用nextTick确保DOM更新完成后再计算提示信息
        setTimeout(() => {
          // 强制重新计算内容高度
          const event = new Event('input');
          document.querySelector('.prompt-textarea textarea')?.dispatchEvent(event);
        }, 50);
      }
    };

    // 添加用户完成率数据
    const userCompletionData = ref<UserCompletionItem[]>([]);
    
    // 获取用户完成率数据
    const loadUserCompletionData = async () => {
      try {
        const response = await axios.get(getApiUrl('/api/user-completion-overview'));
        userCompletionData.value = response.data.users || [];
        console.log("用户完成率数据:", userCompletionData.value);
      } catch (error) {
        console.error('加载用户完成率数据失败:', error);
        // 错误时显示通知
        $q.notify({
          type: 'negative',
          message: '<span style="font-size: 18px;">Failed to load user completion data</span>',
          position: 'top',
          html: true,
          timeout: 3000
        });
      }
    };
    
    // 获取进度条颜色
    const getProgressColor = (rate: number) => {
      if (rate >= 80) {
        return 'linear-gradient(to right, #4caf50, #8bc34a)'; // 绿色
      } else if (rate >= 50) {
        return 'linear-gradient(to right, #8bc34a, #ffeb3b)'; // 黄绿色
      } else if (rate >= 30) {
        return 'linear-gradient(to right, #ffeb3b, #ff9800)'; // 橙黄色
      } else {
        return 'linear-gradient(to right, #ff9800, #f44336)'; // 红橙色
      }
    };

    // Create pie charts
    onMounted(() => {
      // 加载仪表盘统计数据
      loadDashboardStats();
      
      // 加载用户完成率数据
      loadUserCompletionData();
      
      // Make sure Chart.js is loaded
      if (typeof window.Chart !== 'undefined') {
        // Create pie charts when component is mounted
        drawEditPapersRatioChart();
        drawCurationRatioChart();
      } else {
        // Load Chart.js if not available
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js';
        script.onload = () => {
          drawEditPapersRatioChart();
          drawCurationRatioChart();
        };
        document.head.appendChild(script);
      }
    });
    
    // 添加组件卸载时清理计时器的逻辑
    onUnmounted(() => {
      if (statusCheckInterval !== null) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
      }
    });

    // Draw Edit Papers Ratio Chart - 使用实际数据
    const drawEditPapersRatioChart = () => {
      console.log("绘制Edit Papers Ratio图表");
      const ctx = document.getElementById('editPapersRatio') as HTMLCanvasElement;
      if (!ctx || !window.Chart) {
        console.error("无法获取图表canvas元素或Chart.js未加载");
        return;
      }
      
      try {
        // 使用实际数据
        const editPapers = dashboardStats.value.total_edit_papers || 0;
        const totalPapers = dashboardStats.value.total_papers || 1; // 至少为1，防止除以0
        const otherPapers = Math.max(0, totalPapers - editPapers); // 防止负数
        
        console.log(`图表数据: editPapers=${editPapers}, otherPapers=${otherPapers}`);
        
        // 如果两个值都为0，设置一个默认值以显示空图表
        const chartData = (editPapers === 0 && otherPapers === 0) ? 
          [1, 1] : [editPapers, otherPapers];
        
        const chartInstance = new window.Chart(ctx, {
          type: 'pie',
          data: {
            labels: ['Edit Papers', 'Unedited Papers'],
            datasets: [{
              data: chartData,
              backgroundColor: [
                'rgba(80, 165, 220, 0.7)',  // light blue for edit papers
                'rgba(255, 183, 77, 0.7)'   // light orange for unedited papers
              ],
              borderColor: [
                'rgba(80, 165, 220, 1)',
                'rgba(255, 183, 77, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true,
                position: 'top',
                align: 'end',
                labels: {
                  boxWidth: 15,
                  font: {
                    size: 14
                  },
                  color: '#333'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context: ChartContext) {
                    const label = context.label || '';
                    const value = context.raw;
                    const total = context.dataset.data.reduce((acc: number, data: number) => acc + data, 0);
                    const percentage = total === 0 ? 0 : Math.round((value / total) * 100);
                    return `${label}: ${value} (${percentage}%)`;
                  }
                }
              }
            }
          }
        });
        
        // 保存图表实例以便后续销毁
        (ctx as ExtendedHTMLCanvasElement).__chartInstance = chartInstance;
      } catch (e) {
        console.error("绘制Edit Papers Ratio图表时出错:", e);
      }
    };

    // Draw Curation Ratio Chart - 使用实际数据
    const drawCurationRatioChart = () => {
      console.log("绘制Curation Ratio图表");
      const ctx = document.getElementById('curationRatio') as HTMLCanvasElement;
      if (!ctx || !window.Chart) {
        console.error("无法获取图表canvas元素或Chart.js未加载");
        return;
      }
      
      try {
        // 使用实际数据
        const needCuration = dashboardStats.value.papers_need_curation || 0;
        const alreadyCurated = dashboardStats.value.curated_papers || 0;
        // 计算Pending Curation: 已编辑但未进入curation流程的论文
        const pendingCuration = Math.max(0, 
          dashboardStats.value.total_edit_papers - needCuration - alreadyCurated
        );
        
        console.log(`图表数据: needCuration=${needCuration}, alreadyCurated=${alreadyCurated}, pendingCuration=${pendingCuration}`);
        
        // 如果所有值都为0，设置一个默认值以显示空图表
        const chartData = (needCuration === 0 && alreadyCurated === 0 && pendingCuration === 0) ? 
          [1, 1, 1] : [needCuration, alreadyCurated, pendingCuration];
        
        const chartInstance = new window.Chart(ctx, {
          type: 'pie',
          data: {
            labels: ['Need Curation', 'Already Curated', 'Pending Curation'],
            datasets: [{
              data: chartData,
              backgroundColor: [
                'rgba(186, 104, 200, 0.7)',  // light purple for need curation
                'rgba(105, 195, 120, 0.7)',   // light green for already curated
                'rgba(244, 201, 8, 0.7)'    // light yellow for pending curation
              ],
              borderColor: [
                'rgba(186, 104, 200, 1)',
                'rgba(105, 195, 120, 1)',
                'rgba(255, 235, 150, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true,
                position: 'top',
                align: 'end',
                labels: {
                  boxWidth: 15,
                  font: {
                    size: 14
                  },
                  color: '#333'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context: ChartContext) {
                    const label = context.label || '';
                    const value = context.raw;
                    const total = context.dataset.data.reduce((acc: number, data: number) => acc + data, 0);
                    const percentage = total === 0 ? 0 : Math.round((value / total) * 100);
                    return `${label}: ${value} (${percentage}%)`;
                  }
                }
              }
            }
          }
        });
        
        // 保存图表实例以便后续销毁
        (ctx as ExtendedHTMLCanvasElement).__chartInstance = chartInstance;
      } catch (e) {
        console.error("绘制Curation Ratio图表时出错:", e);
      }
    };

    // 添加获取图表柱子渐变色的函数
    const getBarGradient = (value: number) => {
      if (value === 0) {
        return 'linear-gradient(to top, #9e9e9e, #e0e0e0)'; // 灰色，表示无数据
      }
      
      // 所有非零值都使用相同的浅蓝色渐变
      return 'linear-gradient(to top, #1976d2, #64b5f6)'; // 统一使用浅蓝色
    };

    // 设置当前Prompt为系统Prompt
    const setAsSystemPrompt = () => {
      // 确保索引有效
      if (safeCurrentIndex.value < promptTemplates.value.length) {
        // 先取消所有模板的系统Prompt标志
        promptTemplates.value.forEach(template => {
          template.isSystemPrompt = false;
        });
        
        // 设置当前模板为系统Prompt
        const currentTemplate = promptTemplates.value[safeCurrentIndex.value];
        if (currentTemplate) {
          currentTemplate.isSystemPrompt = true;
          
          // 保存当前系统Prompt名称到localStorage
          localStorage.setItem('currentSystemPromptName', currentTemplate.name);
          
          // 模拟保存延迟
          setTimeout(() => {
            // 提示设置成功
            $q.notify({
              type: 'positive',
              message: '<span style="font-size: 18px;">System prompt updated successfully</span>',
              position: 'top',
              html: true,
              timeout: 2000
            });
            
            console.log('设置系统Prompt（仅前端临时存储）:', {
              name: currentTemplate.name,
              description: currentTemplate.description,
              contentLength: currentTemplate.content.length
            });
          }, 500);
        }
      }
    };

    // Paper Crawling Dialog
    const showPaperCrawlingDialog = ref(false);
    const openPaperCrawlingDialog = () => {
      showPaperCrawlingDialog.value = true;
    };
    const newPaperUrl = ref('');
    const submitting = ref(false);
    const batchSubmitting = ref(false);
    const showProgress = ref(false);
    const currentPosition = ref(0);
    const totalPapers = ref(0);
    const fileInput = ref<HTMLInputElement | null>(null);
    
    // 添加状态检查计时器变量
    let statusCheckInterval: number | NodeJS.Timeout | null = null;
    
    // 爬取论文相关方法
    const handleSubmit = async () => {
      if (!newPaperUrl.value) {
        $q.notify({
          type: 'negative',
          message: 'Please enter a URL',
          position: 'top',
          html: true,
          classes: 'notification-message',
          timeout: 3000,
        });
        return;
      }

      // 验证 URL 格式
      const urlPattern = /^https:\/\/pubmed\.ncbi\.nlm\.nih\.gov\/\d+\/?$/;
      if (!urlPattern.test(newPaperUrl.value)) {
        $q.notify({
          type: 'negative',
          message: 'Invalid URL format, please check and try again.',
          position: 'top',
          html: true,
          classes: 'notification-message',
          timeout: 3000,
        });
        return;
      }

      submitting.value = true;

      try {
        // 获取当前用户名
        const currentUser = localStorage.getItem('currentUser');
        let username = currentUser || 'Guest'; // 确保username不为null
        try {
          const userObj = JSON.parse(currentUser || '{}');
          if (userObj && userObj.username) {
            username = userObj.username;
          }
        } catch (error) {
          console.log('Failed to parse user object, using original value:', error);
        }
        
        console.log('Single paper upload using username:', username);

        // 创建一个通知引用
        const notifyRef = $q.notify({
          type: 'ongoing',
          message: 'Processing paper, please wait...',
          position: 'top',
          timeout: 0,
          html: true,
          classes: 'notification-message',
          spinner: true,
        });

        try {
          // 调用初始化 API，传入用户名
          const initResponse = await axios.post(`${BACKEND_URL}/api/initialize-paper`, {
            url: newPaperUrl.value,
            username: username
          });

          // 确保处理中的通知被清除
          notifyRef();

          if (initResponse.data.success) {
            // 清空输入框
            newPaperUrl.value = '';

            // 显示成功消息
            $q.notify({
              type: 'positive',
              message: 'Paper scraped successfully',
              position: 'top',
              html: true,
              classes: 'notification-message',
              timeout: 3000,
            });
            
            // 更新仪表盘统计数据
            loadDashboardStats();
          }
        } catch (error) {
          // 确保处理中的通知被清除
          notifyRef();
          throw error;
        }
      } catch (error: unknown) {
        console.error('Error initializing paper:', error);

        // 类型断言并检查是否是已存在的论文错误
        const err = error as { response?: { status: number, data: { message: string } } };
        if (err.response?.status === 409) {
          $q.notify({
            type: 'warning',
            message: 'Paper already scraped',
            position: 'top',
            html: true,
            classes: 'notification-message',
            color: 'warning',
            timeout: 3000,
          });
          newPaperUrl.value = ''; // 清空输入框
        } else {
          const errorMessage = err.response
            ? err.response.data.message || 'Error initializing paper. Please try again.'
            : 'Error initializing paper. Please try again.';

          $q.notify({
            type: 'negative',
            message: errorMessage,
            position: 'top',
            html: true,
            classes: 'notification-message',
            timeout: 3000,
          });
        }
      } finally {
        submitting.value = false;
      }
    };
    
    const triggerFileInput = () => {
      fileInput.value?.click();
    };
    
    const handleFileSelected = async (event: Event) => {
      const input = event.target as HTMLInputElement;
      if (!input.files?.length) return;

      const file = input.files[0];
      if (file instanceof File) {
        batchSubmitting.value = true;
        const formData = new FormData();
        formData.append('file', file);
        
        // 获取并添加当前用户名
        const currentUser = localStorage.getItem('currentUser');
        let username = currentUser || 'Guest'; // 确保username不为null
        try {
          const userObj = JSON.parse(currentUser || '{}');
          if (userObj && userObj.username) {
            username = userObj.username;
          }
        } catch (error) {
          console.log('Failed to parse user object, using original value:', error);
        }
        
        console.log('Batch upload using username:', username);
        
        // 将用户名添加到表单数据
        formData.append('username', username);

        try {
          const response = await axios.post(`${BACKEND_URL}/api/batch-initialize`, formData);

          if (response.data.success) {
            $q.notify({
              type: 'positive',
              message: response.data.message,
              position: 'top',
              html: true,
              classes: 'notification-message',
              timeout: 3000,
            });

            // 开始检查进度
            showProgress.value = true;
            totalPapers.value = response.data.total;
            currentPosition.value = 0;

            // 清除可能存在的旧计时器
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval);
              statusCheckInterval = null;
            }

            // 启动新的状态检查，改为每2.5秒检查一次
            if (statusCheckInterval === null) {
              statusCheckInterval = setInterval(checkScrapingStatus, 2500) as unknown as number | NodeJS.Timeout;
            }
          }
        } catch (error: unknown) {
          console.error('Error uploading file:', error);
          const err = error as { response?: { status: number, data: { message?: string, error?: string } } };
          const errorMessage = err.response
            ? err.response.data.message || err.response.data.error || 'Unknown error'
            : 'Error uploading file. Please try again.';

          $q.notify({
            type: 'negative',
            message: errorMessage,
            position: 'top',
            html: true,
            classes: 'notification-message',
            timeout: 3000,
          });
        } finally {
          batchSubmitting.value = false;
          // Reset file input
          input.value = '';
        }
      }
    };
    
    const checkScrapingStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/scraping-status`);
        const { total_papers, completed_papers, remaining_papers } = response.data;

        // 如果有总数大于0，说明有爬取任务在进行
        if (total_papers > 0) {
          showProgress.value = true;
          totalPapers.value = total_papers;

          // 更新当前进度
          const completedCount = completed_papers.length;
          if (completedCount > currentPosition.value) {
            // 有新完成的论文
            const newCompletedPapers = completed_papers.slice(currentPosition.value);

            // 更新进度（保持从0开始计数，但显示时会+1）
            currentPosition.value = completedCount;

            // 处理每个新完成的论文
            for (const paper of newCompletedPapers) {
              if (paper.status === 'success') {
                // 成功时刷新仪表盘统计数据
                loadDashboardStats();
              } else if (paper.status === 'error' || paper.status === 'failed') {
                // 显示错误通知
                $q.notify({
                  type: 'negative',
                  message: `Failed to process paper ${paper.pmid}: ${paper.error || 'Unknown error'}`,
                  position: 'top',
                  timeout: 3000,
                  html: true,
                  classes: 'notification-message',
                });
              }
            }
          }

          // 如果所有论文都处理完毕
          if (remaining_papers === 0) {
            showProgress.value = false;
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval);
              statusCheckInterval = null;
            }

            // 显示完成通知
            $q.notify({
              type: 'positive',
              message: `Completed processing all papers`,
              position: 'top',
              timeout: 3000,
              html: true,
              classes: 'notification-message',
            });

            // 最后再刷新一次统计数据
            loadDashboardStats();
          }
        } else {
          // 如果没有正在处理的论文，重置状态
          showProgress.value = false;
          currentPosition.value = 0;
          totalPapers.value = 0;
          if (statusCheckInterval !== null) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
          }
        }
      } catch (error: unknown) {
        console.error('Error checking scraping status:', error);
      }
    };

    // 知识库类型选择对话框
    const knowledgeBaseTypeDialogVisible = ref(false);
    const selectKnowledgeBaseType = (type: 'node' | 'relation') => {
      uploadType.value = type;
      knowledgeBaseTypeDialogVisible.value = false;
      showUploadDialog.value = true;
      resetUploadForm();
      fetchKnowledgeBaseData(type);
    };

    const showImportOptions = () => {
      knowledgeBaseTypeDialogVisible.value = true;
    };

    // 添加分页相关变量
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 计算当前页数据的计算属性
    const paginatedData = computed(() => {
      const startIndex = (currentPage.value - 1) * pageSize.value;
      const endIndex = startIndex + pageSize.value;
      return currentData.value.slice(startIndex, endIndex);
    });

    // 计算总页数
    const totalPages = computed(() => {
      return Math.ceil(currentData.value.length / pageSize.value);
    });

    // 翻页方法
    const goToPage = (page: number) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
      }
    };

    // 添加上传状态变量
    const uploading = ref(false);

    // 修改文件选择和上传相关方法
    const triggerFileUpload = () => {
      fileInput.value?.click();
    };
    
    const onFileSelected = async (event: Event) => {
      const input = event.target as HTMLInputElement;
      if (!input.files?.length) return;
      
      const file = input.files[0];
      // Add type check to ensure file is defined and is a File object
      if (!(file instanceof File)) {
        errorMessage.value = 'Invalid file selected';
        return;
      }

      uploading.value = true;
      errorMessage.value = '';
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', uploadType.value);
        
        const response = await axios.post(getApiUrl('/api/upload-knowledge-base'), formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // 显示更详细的成功通知
        $q.notify({
          type: 'positive',
          message: response.data.message || `${uploadType.value === 'node' ? 'Node' : 'Relation'} knowledge base updated successfully`,
          position: 'top',
          html: true,
          timeout: 4000
        });
        
        // 更新显示的数据
        await fetchKnowledgeBaseData(uploadType.value);
        
        // 重置表单状态
        resetUploadForm();
        
      } catch (error: unknown) {
        console.error('Failed to upload knowledge base:', error);
        
        if (error && typeof error === 'object' && 'response' in error && 
            error.response && typeof error.response === 'object' && 'data' in error.response) {
          const response = error.response as { status: number; data: { message?: string } };
          
          if (response.status === 400) {
            errorMessage.value = 'Invalid JSON file format. Please check and try again.';
          } else {
            errorMessage.value = response.data.message || 'Failed to upload knowledge base. Please try again.';
          }
        } else {
          errorMessage.value = 'An unexpected error occurred. Please try again.';
        }
        
        $q.notify({
          type: 'negative',
          message: errorMessage.value,
          position: 'top',
          html: true,
          timeout: 3000
        });
      } finally {
        uploading.value = false;
        // 清空文件输入框
        input.value = '';
      }
    };

    return {
      navigateToTypeAndName,
      navigateToPrompt,
      navigateToCuration,
      navigateToCuratedPapers,
      navigateToPaperPermissions,
      formatDate,
      editPapersRatio,
      curationRatio,
      showTypeNameEditor,
      openTypeNameEditor,
      onTypeNameSaved,
      // 添加API URL工具函数
      getApiUrl,
      // 添加仪表盘统计数据
      dashboardStats,
      // 添加图表渐变颜色函数
      getBarGradient,
      // Type & Name配置相关
      typeList,
      nameList,
      newType,
      newName,
      addType,
      removeType,
      addName, 
      removeName,
      saveChanges,
      onCancel,
      typeFilter,
      nameFilter,
      filteredTypeList,
      filteredNameList,
      showPromptEditor,
      openPromptEditor,
      onPromptCancel,
      promptTemplate,
      jsonPromptTemplate,
      currentPromptIndex,
      savePromptChanges,
      isLoadingPrompt,
      isSavingPrompt,
      switchPromptTemplate,
      showKnowledgeBaseSelector,
      openKnowledgeBaseSelector,
      hasMultiplePrompts,
      // 添加新的提示相关
      promptTemplates,
      showAddPromptDialog,
      newPromptName,
      newPromptDescription,
      newPromptContent,
      openAddPromptDialog,
      addNewPrompt,
      canAddPrompt,
      // 添加安全访问计算属性
      safeCurrentIndex,
      currentTemplateContent,
      currentTemplateStats,
      // 设置系统Prompt
      setAsSystemPrompt,
      // 添加用户完成率数据
      userCompletionData,
      // 获取用户完成率数据
      loadUserCompletionData,
      // 获取进度条颜色
      getProgressColor,
      // Paper Crawling Dialog
      showPaperCrawlingDialog,
      openPaperCrawlingDialog,
      // 爬取论文相关变量
      newPaperUrl,
      submitting,
      batchSubmitting,
      showProgress,
      currentPosition,
      totalPapers,
      fileInput,
      
      // 爬取论文相关方法
      handleSubmit,
      triggerFileInput,
      handleFileSelected,
      checkScrapingStatus,
      showKbOptions,
      showUploadDialog,
      uploadType,
      uploadFile,
      currentData,
      loading,
      errorMessage,
      showKnowledgeBaseOptions,
      openUploadDialog,
      fetchKnowledgeBaseData,
      resetUploadForm,
      onRejected,
      uploadKnowledgeBase,
      knowledgeBaseTypeDialogVisible,
      selectKnowledgeBaseType,
      showImportOptions,
      currentPage,
      pageSize,
      paginatedData,
      totalPages,
      goToPage,
      uploading,
      triggerFileUpload,
      onFileSelected
    }
  }
})
</script>

<style lang="scss" scoped>
.admin-dashboard {
  min-height: 100vh;
  background: #f5f7fa;
  position: relative;
}

.header-section {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
}

.page-content {
  padding-top: 20px;
  padding-bottom: 40px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  border-left: 4px solid var(--q-primary);
  padding-left: 12px;
  margin-bottom: 24px;
}

.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  position: relative;  /* 添加相对定位 */

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }

  .nav-icon {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 1;
    opacity: 0.7;
    transition: opacity 0.2s;
  }

  &:hover .nav-icon {
    opacity: 1;
  }
}

.action-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;

  .card-content {
    flex-grow: 1;
  }

  .q-card-actions {
    margin-top: auto;
    padding: 12px;
    display: flex;
    justify-content: flex-end;
  }

  .q-btn {
    margin: 0;
    text-transform: uppercase;
    font-weight: 500;
  }

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
}

.chart-card {
  border-radius: 12px;
  height: 100%;
}

.chart-container {
  height: 300px;
  position: relative;
  margin-top: 20px;
}

.chart-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .chart-bars {
    height: calc(100% - 40px);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 0;
    width: 100%;
    
    .chart-bar {
      position: relative;
      width: 13%;
      background: linear-gradient(to top, #1976d2, #64b5f6);
      border-radius: 3px 3px 0 0;
      transition: height 0.3s ease, background 0.3s ease;
      min-height: 20px;
      
      .bar-value {
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        color: #000000;
        font-size: 24px;
        font-weight: normal;
      }
      
      // 添加动态颜色效果
      &:hover {
        background: linear-gradient(to top, #1565c0, #42a5f5);
        box-shadow: 0 0 8px rgba(25, 118, 210, 0.5);
        transform: translateY(-3px);
      }
    }
  }
  
  .chart-axis {
    height: 40px;
    display: flex;
    justify-content: space-between;
    width: 100%;
    margin-top: 5px;
    
    .axis-tick {
      width: 13%;
      display: flex;
      justify-content: center;
      align-items: center;
      text-align: center;
      color: #666;
      font-size: 24px;
    }
  }
}

.activity-card {
  border-radius: 12px;
}

// 添加Type & Name配置相关样式
.editor-card {
  height: 100%;
  
  .q-list {
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 4px;
    height: 250px !important; // 强制固定高度
  }
  
  // 设置输入框一致样式
  .q-input {
    margin-bottom: 8px;
    
    &:deep(.q-field__control) {
      height: 36px;
    }
  }
}

// 添加Prompt编辑器相关样式
.prompt-editor-container {
  position: relative;
  min-height: 400px;
}

.prompt-wrapper {
  width: 100%;
}

.prompt-textarea {
  font-size: 14px;
  width: 100%;
  
  :deep(.q-field__native) {
    min-height: 400px;
    line-height: 1.5;
    padding: 12px;
    white-space: pre-wrap;
  }
  
  :deep(.q-field__messages) {
    font-size: 18px !important;
    min-height: 24px; /* 确保消息区域有固定高度 */
    opacity: 1 !important;
    visibility: visible !important;
  }
  
  :deep(.q-field__bottom) {
    min-height: 24px; /* 确保底部区域有固定高度 */
    padding-top: 4px;
  }
}

.prompt-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 4px;
}

// 添加选择卡片样式
.selection-card {
  height: 100%;
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
  
  .selection-card-content {
    padding: 16px;
    font-size: 16px;
    min-height: 120px;
    position: relative;
  }
  
  &.disabled-card {
    opacity: 0.8;
    pointer-events: none;
  }
  
  &.add-card {
    .add-kb-icon {
      position: absolute;
      right: 15px;
      bottom: 10px;
      background: rgba(255, 255, 255, 0.9);
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      
      .pulse-icon {
        animation: pulse 1.5s infinite;
      }
    }
  }
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(0.95);
    opacity: 0.7;
  }
}

.coming-soon-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: #ff9800;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* 用户完成进度区域的样式 */
.user-completion-container {
  width: 100%;
  padding: 10px 0;
}

.user-progress-row {
  display: flex;
  align-items: center;
  width: 100%;
  margin-bottom: 12px;
}

.user-name {
  font-weight: 500;
  text-align: right;
  padding-right: 15px;
  min-width: 100px;
  color: #333;
}

.progress-bar-container {
  flex-grow: 1;
  height: 30px;
  background-color: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 10px;
  transition: width 0.5s ease;
  position: relative;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  min-width: 40px;
}

.progress-text {
  color: #333;
  font-weight: 500;
  text-shadow: none;
  padding: 0 10px;
  white-space: nowrap;
  position: absolute;
  left: 10px;
  z-index: 2;
}

.no-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-style: italic;
}

// 添加Prompt按钮样式
.add-prompt-btn {
  background: #26a69a;
  color: white;
}

// 系统Prompt标签样式
.system-prompt-label {
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-prompt-badge {
  margin-left: 5px;
  font-size: 16px;
  font-weight: normal;
  color: #4caf50;
}

.url-input {
  :deep(.q-field__label) {
    font-size: 18px;
  }
  :deep(.q-field__native) {
    font-size: 18px;
  }
  :deep(.q-field__marginal) {
    font-size: 18px;
  }
  :deep(.q-field__control) {
    height: 56px;
  }
}

/* Update batch scrape button styles */
.batch-scrape-btn {
  height: 40px;
  font-size: 14px;
  padding: 0 12px;
  min-height: unset;
  align-self: center;
}

/* Update tooltip styles */
:deep(.tooltip-text) {
  font-size: 18px !important;
}

/* 全局通知样式 */
:global(.q-notification) {
  min-height: 50px !important;
  padding: 12px 24px !important;
}

:global(.q-notification__message) {
  font-size: 18px !important;
}

:global(.q-notification--warning) {
  background-color: #ffd700 !important;
  color: #000000 !important;
}

:deep(.notification-message) {
  font-size: 18px !important;
}

/* 知识库选择分支样式 */
.branch-container {
  position: relative;
  padding: 20px 0 80px;
  width: 100%;
}

.central-node {
  position: relative;
  margin: 0 auto 50px;
  width: 120px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  border-radius: 50%;
  z-index: 2;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.branch-lines {
  position: absolute;
  top: 100px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  z-index: 1;
  width: 100%;
}

.line-left, .line-right {
  height: 2px;
  width: 36%;
  background: linear-gradient(90deg, rgba(25, 118, 210, 0.1), rgba(25, 118, 210, 0.8));
  position: relative;
}

.line-left {
  transform: translateX(-40px) rotate(-15deg);
}

.line-right {
  transform: translateX(40px) rotate(15deg);
  background: linear-gradient(90deg, rgba(65, 174, 157, 0.8), rgba(65, 174, 157, 0.1));
}

.line-left::after, .line-right::after {
  content: '';
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  bottom: -4px;
}

.line-left::after {
  right: 0;
  background-color: rgba(25, 118, 210, 0.8);
}

.line-right::after {
  left: 0;
  background-color: rgba(65, 174, 157, 0.8);
}

.branch-options {
  display: flex;
  justify-content: space-between;
  width: 90%;
  margin: 0 auto;
  position: relative;
}

.branch-option {
  width: 260px;
  transition: transform 0.3s;
  position: relative;
}

.branch-left {
  margin-right: auto;
  margin-left: 5%;
}

.branch-right {
  margin-left: auto;
  margin-right: 5%;
}

.branch-option:hover {
  transform: translateY(-10px);
}

.branch-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s;
  cursor: pointer;
}

.branch-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.knowledge-base-data-container {
  min-height: 200px;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.data-display-area {
  overflow-y: auto;
  flex-grow: 1;
}

.data-item {
  border-bottom: 1px dotted rgba(0, 0, 0, 0.1);
}
</style>