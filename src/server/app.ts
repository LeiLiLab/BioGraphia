/**
 * 后端服务器入口文件
 * 
 * 功能说明：
 * 1. 提供论文分析系统的后端 API 服务
 * 2. 处理前端的数据请求
 * 3. 管理模拟数据（在实际生产环境中应替换为数据库）
 * 
 * 数据流向：
 * 1. 前端发起 HTTP GET 请求到 /api/paper-analysis
 * 2. 后端接收请求并返回 paperData 数据
 * 3. 前端接收数据并在界面上展示
 */

// 导入必要的依赖包
import express from 'express';  // Express.js 框架，用于构建 REST API
import cors from 'cors';        // CORS 中间件，用于处理跨域请求

// 初始化 Express 应用
const app = express();

// 配置中间件
app.use(cors());           // 启用跨域请求支持，允许前端访问
app.use(express.json());   // 解析 JSON 格式的请求体，支持 POST 请求

/**
 * 论文内容数据结构定义
 * 
 * 字段说明：
 * - id: 唯一标识符
 * - type: 内容类型（标题、摘要或分析）
 * - content: 主要文本内容
 * - analysis: 分析结果（仅在 type 为 'analysis' 时存在）
 */
interface PaperContent {
  id: number;                                // 内容项的唯一标识符
  type: 'title' | 'abstract' | 'analysis';   // 内容类型：标题、摘要或分析
  content: string;                           // 主要文本内容
  analysis?: {                               // 可选的分析对象（仅用于 analysis 类型）
    key_points: string;                      // 关键要点
    implications: string;                    // 影响和意义
    suggestions: string;                     // 建议和未来方向
  };
}

/**
 * 模拟数据库内容
 * 
 * 说明：
 * 1. 当前使用静态数据模拟数据库
 * 2. 在实际生产环境中，应该替换为真实的数据库连接
 * 3. 数据结构遵循 PaperContent 接口定义
 */
const paperData: PaperContent[] = [
  {
    id: 1,
    type: 'title',
    content: "APPLeNet: Visual Attention Parameterized Prompt Learning for Few-Shot Remote Sensing Image Generalization using CLIP"
  },
  {
    id: 2,
    type: 'abstract',
    content: `In recent years, the success of large-scale vision-language models (VLMs) such as CLIP has led to their increased usage in various computer vision tasks. These models enable zero-shot inference through carefully crafted instructional text prompts without task-specific supervision. However, the potential of VLMs for generalization tasks in remote sensing (RS) has not been fully realized. To address this research gap, we propose a novel image-conditioned prompt learning strategy called the Visual Attention Parameterized Prompts Learning Network (APPLeNet). APPLeNet emphasizes the importance of multi-scale feature learning in RS scene classification and disentangles visual style and content primitives for domain generalization tasks. To achieve this, APPLeNet combines visual content features obtained from different layers of the vision encoder and style properties obtained from feature statistics of domain-specific batches. An attention-driven injection module is further introduced to generate visual tokens from this information. We also introduce an anti-correlation regularizer to ensure discrimination among the token embeddings, as this visual information is combined with the textual tokens. To validate APPLeNet, we curated four available RS benchmarks and introduced experimental protocols and datasets for three domain generalization tasks. Our results consistently outperform the relevant literature and code is available at https://github.com/mainaksingha01/APPLeNet`
  },
  // 论文的结构化分析部分
  {
    id: 3,
    type: 'analysis',
    content: "State of the Art",
    analysis: {
      key_points: "Recent advances in vision-language models, particularly CLIP, have revolutionized computer vision tasks",
      implications: "Zero-shot learning capabilities through text prompts reduce need for task-specific training",
      suggestions: "Investigate applications in specialized domains beyond general computer vision"
    }
  },
  {
    id: 4,
    type: 'analysis',
    content: "Research Problem",
    analysis: {
      key_points: "Limited exploration of VLMs in remote sensing domain despite their potential",
      implications: "Current approaches may not fully leverage domain-specific characteristics",
      suggestions: "Develop specialized architectures for remote sensing applications"
    }
  },
  {
    id: 5,
    type: 'analysis',
    content: "Methodology",
    analysis: {
      key_points: "Novel APPLeNet architecture with attention-parameterized prompt learning",
      implications: "Enhanced feature extraction through multi-scale learning and style-content separation",
      suggestions: "Consider incorporating domain adaptation techniques"
    }
  },
  {
    id: 6,
    type: 'analysis',
    content: "Technical Contribution",
    analysis: {
      key_points: "Integration of visual attention mechanism with prompt learning framework",
      implications: "Improved token discrimination through anti-correlation regularization",
      suggestions: "Explore additional regularization techniques for token optimization"
    }
  },
  {
    id: 7,
    type: 'analysis',
    content: "Empirical Validation",
    analysis: {
      key_points: "Comprehensive evaluation on multiple RS benchmarks with domain generalization focus",
      implications: "Superior performance demonstrates effectiveness of proposed approach",
      suggestions: "Extend validation to additional remote sensing scenarios and applications"
    }
  }
];

/**
 * API 路由定义
 * 
 * 当前支持的接口：
 * 1. GET /api/paper-analysis - 获取论文分析数据
 * 
 * 如何修改/新增接口：
 * 1. 新增 GET 接口：使用 app.get('/api/新路径', (req, res) => { ... })
 * 2. 新增 POST 接口：使用 app.post('/api/新路径', (req, res) => { ... })
 * 3. 新增其他 HTTP 方法的接口：使用对应的 app.method() 函数
 */
app.get('/api/paper-analysis', (req, res) => {
  res.json(paperData);  // 返回模拟数据作为 JSON 响应
});

// 服务器配置
import { BACKEND_PORT } from '../config/api'
const PORT = BACKEND_PORT;  // 服务器监听的端口号

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器已在端口 ${PORT} 上启动`);  // 输出服务器启动确认信息
}); 