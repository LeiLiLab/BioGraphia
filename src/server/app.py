from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import json
import os
import sys
import shutil
from urllib.parse import urlparse
import time
from queue import Queue
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
import pytz
import re
import io
import zipfile
import uuid
import traceback
import requests
import hashlib
import glob
import random
import string
from io import BytesIO
import concurrent.futures
from bs4 import BeautifulSoup

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("ROOT_DIR:", ROOT_DIR)
sys.path.append(ROOT_DIR)

# 导入爬虫模块
from utils.scraper import extract_article_to_json

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 创建任务队列
scraping_queue = Queue()
AVERAGE_SCRAPE_TIME = 15  # 预估每篇论文爬取时间（秒）

# 用户数据文件路径
USERS_FILE = os.path.join(ROOT_DIR, 'data', 'users.json')

# 添加新的路径常量
MAIN_DIR = os.path.join(ROOT_DIR, 'data', 'Main_dir')
TEMP_DIR = os.path.join(ROOT_DIR, 'data', 'Temp_dir')  # 改为 Temp_dir
# 添加统计数据文件路径
STATISTICS_FILE = os.path.join(ROOT_DIR, 'data', 'statistic.json')

# 添加全局变量来跟踪爬取进度
completed_papers = []
in_progress_papers = set()  # 新增：跟踪正在处理中的论文
total_papers_to_scrape = 0
# 添加锁来保护共享数据访问
progress_lock = Lock()  # 用于保护completed_papers和in_progress_papers

# 添加新的常量
TYPE_NAME_CONFIG_FILE = os.path.join(ROOT_DIR, 'data', 'type_name_database.json')

# 设置prompt配置文件的路径常量
PROMPT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'prompt.json')

def ensure_directory_exists(path):
    """确保目录存在，如果不存在则创建"""
    try:
        if not os.path.exists(path):
            print(f"Creating directory: {path}")  # 添加日志
            os.makedirs(path, exist_ok=True)
            print(f"Directory created successfully: {path}")  # 添加日志
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {str(e)}")
        return False

def load_statistics():
    """加载统计数据文件，如果不存在则创建空的统计数据"""
    try:
        if os.path.exists(STATISTICS_FILE):
            with open(STATISTICS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 确保目录存在
            ensure_directory_exists(os.path.dirname(STATISTICS_FILE))
            # 创建空的统计数据
            return {}
    except Exception as e:
        print(f"Error loading statistics file: {str(e)}")
        return {}

def save_statistics(statistics):
    """保存统计数据到文件"""
    try:
        # 确保目录存在
        ensure_directory_exists(os.path.dirname(STATISTICS_FILE))
        # 保存统计数据
        with open(STATISTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving statistics file: {str(e)}")
        return False

def record_edit_duration(pmid, username, edit_duration):
    """记录编辑时间到统计文件
    
    Args:
        pmid: 论文ID
        username: 用户名
        edit_duration: 编辑时长(毫秒)
    """
    try:
        # 加载统计数据
        statistics = load_statistics()
        
        # 获取当前时间的Unix时间戳
        submit_time_unix = int(time.time())
        
        # 确保pmid存在于统计数据中
        if pmid not in statistics:
            statistics[pmid] = {}
        
        # 确保Edit_Information存在
        if "Edit_Information" not in statistics[pmid]:
            statistics[pmid]["Edit_Information"] = {}
        
        # 确保username存在
        if username not in statistics[pmid]["Edit_Information"]:
            statistics[pmid]["Edit_Information"][username] = []
        
        # 添加编辑记录，使用字典格式
        record = {
            "Edit_Time_As_Unix": submit_time_unix,
            "Edit_Time_Record_As_ms": edit_duration
        }
        statistics[pmid]["Edit_Information"][username].append(record)
        
        # 保存统计数据
        save_statistics(statistics)
        
        print(f"Recorded edit duration {edit_duration}ms for user {username} on paper {pmid} at {submit_time_unix}")
        return True
    except Exception as e:
        print(f"Error recording edit duration: {str(e)}")
        return False

# 确保基本目录存在
ensure_directory_exists(MAIN_DIR)
ensure_directory_exists(TEMP_DIR)

def get_main_data_path(pmid):
    """获取论文主数据路径"""
    return os.path.join(MAIN_DIR, pmid, 'original_data')

def get_temp_data_path(username, pmid):
    """获取用户临时数据路径"""
    return os.path.join(TEMP_DIR, username, pmid)

def get_user_data_path_in_main(username, pmid):
    """获取用户在主目录中的数据路径"""
    return os.path.join(MAIN_DIR, pmid, 'User_dir', username)

def get_queue_position(target_pmid: str) -> tuple[int, int]:
    """
    获取论文在队列中的位置
    
    Args:
        target_pmid: 目标论文ID
        
    Returns:
        tuple[int, int]: (队列位置, 队列总长度)
        队列位置从1开始，如果不在队列中返回(0, 总长度)
    """
    return (0, scraping_queue.qsize())

def scrape_paper(pmid: str, paper_url: str):
    """爬取论文并保存数据"""
    try:
        main_data_path = get_main_data_path(pmid)
        data_json_path = os.path.join(main_data_path, 'data.json')
        
        print(f"Scraping paper {pmid}...")
        article_json = extract_article_to_json(paper_url)
        article_data = json.loads(article_json)
        
        utc_time = datetime.now(pytz.UTC)
        article_data["extraction_time"] = utc_time.strftime("%B %d, %Y %I:%M %p %Z")
        
        ensure_directory_exists(main_data_path)
        with open(data_json_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)
            
        print(f"Paper {pmid} basic data scraped successfully")
        
        # 生成初始分析
        generate_initial_analysis(article_data, pmid)
        
        # 等待分析完全生成
        max_wait = 60  # 最大等待时间（秒）
        wait_time = 0
        while not is_paper_fully_processed(pmid) and wait_time < max_wait:
            time.sleep(1)
            wait_time += 1
            if wait_time % 5 == 0:
                print(f"Waiting for paper {pmid} analysis to complete... ({wait_time}s)")
        
        if wait_time >= max_wait:
            print(f"Warning: Timeout waiting for paper {pmid} analysis to complete")
            raise TimeoutError(f"Timeout waiting for paper {pmid} analysis to complete")
        else:
            print(f"Paper {pmid} processing completed successfully")
            return True
            
    except Exception as e:
        print(f"Error processing paper {pmid}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_paper_data_path(pmid):
    """获取论文数据文件路径"""
    return os.path.join(get_main_data_path(pmid), 'data.json')

def get_paper_output_path(pmid):
    """获取论文分析输出文件路径"""
    return os.path.join(get_main_data_path(pmid), 'original_output.json')

def is_paper_fully_processed(pmid):
    """检查论文是否完全处理完成（包括数据爬取和分析生成）"""
    data_path = get_paper_data_path(pmid)
    output_path = get_paper_output_path(pmid)
    return os.path.exists(data_path) and os.path.exists(output_path)

def load_paper_data(pmid):
    """加载论文数据（包括评论）"""
    data_path = get_paper_data_path(pmid)
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保评论字段存在
            if 'comments' not in data:
                data['comments'] = []
            return data
    return {"title": "", "abstract": "", "comments": []}

def save_paper_data(pmid, data):
    """保存论文数据（包括评论）"""
    data_path = get_paper_data_path(pmid)
    ensure_directory_exists(os.path.dirname(data_path))
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def initialize_paper_data(paper_url):
    """初始化论文数据，如果不存在则爬取"""
    try:
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # 检查数据是否存在
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保评论字段存在
                if 'comments' not in data:
                    data['comments'] = []
                    save_paper_data(pmid, data)
                return data
        
        # 直接开始爬取
        return scrape_paper(pmid, paper_url)
            
    except Exception as e:
        print(f"Error initializing paper data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def generate_initial_analysis(article_data, pmid):
    """生成初始分析数据"""
    try:
        main_data_path = get_main_data_path(pmid)
        output_path = os.path.join(main_data_path, 'original_output.json')
        
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 使用extractor模块代替generator模块
        from utils.extractor import process_paper
        process_paper(
            title=article_data["title"],
            abstract=article_data["abstract"], 
            output_path=output_path,
            pmid=pmid
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        return json_data
        
    except Exception as e:
        print(f"Error generating initial analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def convert_frontend_to_graph_format(frontend_data):
    """将前端表格数据转换为图形可视化所需的格式"""
    # 收集所有实体
    entities = set()
    relations = []
    
    for row in frontend_data:
        if not isinstance(row, dict) or 'head' not in row or 'tail' not in row:
            continue
            
        # 跳过已删除的关系
        if row.get('isDeleted'):
            continue
            
        # 添加头尾实体
        entities.add(row['head'])
        entities.add(row['tail'])
        
        # 构建关系对象
        relation = {
            "head": row['head'],
            "tail": row['tail'],
            "label": row['label'],
            "text": row.get('text', '')
        }
        
        # 添加 metaRelations（如果存在）
        if 'metaRelations' in row and row['metaRelations']:
            relation['metaRelations'] = row['metaRelations']
            # 从 metaRelations 中收集额外的实体
            for meta in row['metaRelations']:
                if 'target' in meta:
                    entities.add(meta['target'])
        
        relations.append(relation)
    
    # 返回一个新的字典，包含entities和relations
    # 这样有助于确保不会丢失其他字段（如context）
    return {
        "entities": list(entities),
        "relations": relations
    }

def find_text_position(text: str, abstract: str) -> int:
    """
    查找文本在abstract中的位置
    如果找不到返回-1
    
    Args:
        text: 要查找的文本
        abstract: 摘要文本
    
    Returns:
        int: 文本在abstract中的位置,找不到返回-1
    """
    if not text or not abstract:
        return -1
        
    # 标准化文本,移除多余空格,转小写
    def normalize_text(s: str) -> str:
        return ' '.join(s.lower().split())
    
    text = normalize_text(text)
    abstract = normalize_text(abstract)
    
    # 直接查找完整文本
    pos = abstract.find(text)
    if pos != -1:
        return pos
        
    # 如果找不到完整匹配,尝试查找文本的关键部分
    # 将文本分成词,查找最长的连续词组
    words = text.split()
    if len(words) < 3:  # 如果词太少,返回-1
        return -1
        
    # 尝试不同长度的词组
    for length in range(len(words), 2, -1):
        for i in range(len(words) - length + 1):
            phrase = ' '.join(words[i:i+length])
            pos = abstract.find(phrase)
            if pos != -1:
                return pos
                
    return -1

def sort_relations_by_text_position(relations: list, abstract: str) -> list:
    """
    根据supporting text在abstract中的位置对relations进行排序
    
    Args:
        relations: relations列表
        abstract: 摘要文本
    
    Returns:
        list: 排序后的relations列表
    """
    def get_position(relation):
        text = relation.get('text', '')
        pos = find_text_position(text, abstract)
        return pos if pos != -1 else float('inf')  # 找不到位置的放到最后
    
    # 根据position进行排序
    return sorted(relations, key=get_position)

@app.route('/api/paper-analysis', methods=['GET'])
def get_paper_analysis():
    """获取论文分析数据的 API 端点"""
    try:
        # 从请求参数中获取 URL 和用户名
        paper_url = request.args.get('url')
        username = request.args.get('username')
        mode = request.args.get('mode', 'view')  # 新增mode参数
        target_user = request.args.get('user', username)  # 修改这里：默认使用当前用户
        
        print(f"Received request - URL: {paper_url}, Username: {username}, Mode: {mode}, Target User: {target_user}")
        
        # 参数验证
        if not paper_url:
            return jsonify({"error": "URL parameter is required"}), 400
            
        if not username:
            return jsonify({
                "error": "Username is missing",
                "message": "Please ensure you have selected a valid user."
            }), 400

        pmid = paper_url.rstrip('/').split('/')[-1]
        main_path = get_main_data_path(pmid)
        print(f"Main path: {main_path}")
        
        # 读取论文基本数据
        data_file = os.path.join(main_path, 'data.json')
        if not os.path.exists(data_file):
            print(f"Data file not found: {data_file}")
            return jsonify({
                "error": "Paper data not found",
                "message": "No data found for this paper"
            }), 404
            
        with open(data_file, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
        
        # 根据模式决定读取路径
        if mode == 'temp':
            print("Processing in temp mode")
            # 如果是 temp 模式，检查临时目录
            temp_path = get_temp_data_path(username, pmid)
            temp_output_json = os.path.join(temp_path, 'last_modify_output.json')
            temp_note_json = os.path.join(temp_path, 'notes.json')  # 添加临时note.json路径
            
            # 只有当临时目录不存在或文件不存在时才复制
            if not os.path.exists(temp_output_json):
                print(f"Temporary file not found, copying from original")
                # 确保临时目录存在
                ensure_directory_exists(temp_path)
                
                # 设置源文件路径
                src_json = os.path.join(main_path, 'original_output.json')
                src_note = os.path.join(main_path, 'notes.json')  # 添加note.json源文件路径
                
                # 复制output.json文件
                try:
                    shutil.copy2(src_json, temp_output_json)
                    print(f"Successfully copied JSON file to: {temp_output_json}")
                    
                    # 复制note.json文件（如果存在）
                    if os.path.exists(src_note):
                        shutil.copy2(src_note, temp_note_json)
                        print(f"Successfully copied notes.json file to: {temp_note_json}")
                    else:
                        # 如果原始notes.json不存在，创建一个空的notes.json
                        with open(temp_note_json, 'w', encoding='utf-8') as f:
                            json.dump({}, f, indent=2, ensure_ascii=False)
                        print(f"Created empty notes.json file at: {temp_note_json}")
                        
                except Exception as e:
                    print(f"Error copying files: {str(e)}")
                    return jsonify({
                        "error": "File copy failed",
                        "message": f"Failed to copy files: {str(e)}"
                    }), 500
            else:
                print(f"Using existing temporary files: {temp_output_json}")
                
                # 确保notes.json也存在
                if not os.path.exists(temp_note_json):
                    src_note = os.path.join(main_path, 'notes.json')
                    if os.path.exists(src_note):
                        try:
                            shutil.copy2(src_note, temp_note_json)
                            print(f"Successfully copied notes.json file to: {temp_note_json}")
                        except Exception as e:
                            print(f"Error copying notes.json: {str(e)}")
                    else:
                        # 如果原始notes.json不存在，创建一个空的notes.json
                        with open(temp_note_json, 'w', encoding='utf-8') as f:
                            json.dump({}, f, indent=2, ensure_ascii=False)
                        print(f"Created empty notes.json file at: {temp_note_json}")
            
            # 使用临时目录的文件
            output_path = temp_output_json
            
            # 验证文件是否成功复制
            if not os.path.exists(output_path):
                print(f"Failed to verify copied file: {output_path}")
                return jsonify({
                    "error": "File copy failed",
                    "message": "Failed to copy original data to temp directory"
                }), 500

            print("*************** temp mode copy file complete. ***************")
            
        else:
            print("Processing in view mode")
            # view 模式，使用目标用户的数据
            user_path = get_user_data_path_in_main(target_user, pmid)
            output_path = os.path.join(user_path, 'last_modify_output.json')
            print(f"Target user path: {user_path}")
            print(f"Output path: {output_path}")
            
            # 如果用户目录下没有文件，使用原始数据
            if not os.path.exists(output_path):
                print(f"User version not found at: {output_path}, falling back to original data")
                output_path = os.path.join(main_path, 'original_output.json')
                if not os.path.exists(output_path):
                    print(f"Original data not found at: {output_path}")
                    return jsonify({
                        "error": "Data not found",
                        "message": "No data found for this paper"
                    }), 404

            print("*************** view mode read file complete. ***************")

        # 读取分析数据
        try:
            print(f"Reading analysis data from: {output_path}")
            with open(output_path, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
                relations_data = output_data.get('relations', [])
                context_data = output_data.get('context', [])  # 获取context数据
                entities_data = output_data.get('entities', {})  # 获取entities数据
                
                # 获取abstract用于排序
                abstract = article_data.get("abstract", "")
                
                # 对relations进行排序
                relations_data = sort_relations_by_text_position(relations_data, abstract)
                
            print(f"Successfully read and sorted relations data: {len(relations_data)} relations found")
            print(f"Successfully read entities data: {len(entities_data) if isinstance(entities_data, dict) or isinstance(entities_data, list) else 0} entities found")
        except Exception as e:
            print(f"Error reading output file: {str(e)}")
            return jsonify({
                "error": "Failed to read analysis data",
                "message": str(e)
            }), 500
            
        # 构造返回数据
        paper_data = [
            {
                "id": 1,
                "type": "title",
                "content": article_data["title"],
                "extraction_time": article_data.get("extraction_time", "")
            },
            {
                "id": 2,
                "type": "abstract",
                "content": article_data["abstract"]
            }
        ]
        
        # 添加context数据
        if context_data:
            paper_data.append({
                "id": "context",
                "type": "context",
                "context": context_data
            })
            
        # 添加entities数据
        if entities_data:
            paper_data.append({
                "id": "entities",
                "type": "entities",
                "entities": entities_data
            })

        # 添加关系数据
        for idx, relation in enumerate(relations_data, start=3):
            analysis_item = {
                "id": idx,
                "type": "analysis",
                "content": f"Relation {idx-2}",
                "analysis": {
                    "key_points": relation["head"],
                    "implications": relation["label"],
                    "suggestions": relation["tail"]
                },
                "text": relation.get("text", ""),
                "metaRelations": relation.get("metaRelations", [])
            }
            paper_data.append(analysis_item)
            
        print("Successfully prepared response data")
        return jsonify(paper_data)
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to load data",
            "message": str(e)
        }), 500

@app.route('/api/update-analysis', methods=['POST'])
def update_analysis():
    """处理前端提交的编辑后的数据并生成新的可视化图形"""
    try:
        # 获取前端发送的数据
        frontend_data = request.json.get('data', [])
        paper_url = request.json.get('url')
        username = request.json.get('username')
        mode = request.json.get('mode', 'view')
        target_user = request.json.get('user')  # 获取目标用户
        context_data = request.json.get('context', [])  # 获取context数据
        edit_duration = request.json.get('editDuration')  # 获取编辑用时
        
        if not paper_url or not username:
            return jsonify({"error": "URL and username are required"}), 400
        
        # 获取 PMID
        pmid = paper_url.rstrip('/').split('/')[-1]
        
        # 如果提供了编辑用时，仅记录到统计文件中
        if edit_duration is not None:
            # 记录编辑时长到统计文件
            record_edit_duration(pmid, username, edit_duration)
            print(f"Recorded edit duration {edit_duration}ms for user {username} on paper {pmid}")
        
        # 根据模式决定保存路径和读取现有文件
        if mode == 'temp':
            # 临时模式：保存到临时目录
            save_path = get_temp_data_path(username, pmid)
            print(f"Saving to temp directory: {save_path}")
            
            # 检查临时目录中是否已有文件
            existing_file = os.path.join(save_path, 'last_modify_output.json')
            if os.path.exists(existing_file):
                try:
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    print(f"Error reading existing file: {str(e)}")
                    existing_data = {}
            else:
                # 如果临时目录没有文件，查找原始文件
                original_file = os.path.join(get_main_data_path(pmid), 'original_output.json')
                if os.path.exists(original_file):
                    try:
                        with open(original_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except Exception as e:
                        print(f"Error reading original file: {str(e)}")
                        existing_data = {}
                else:
                    existing_data = {}
        else:
            # Check mode: verify permissions
            if target_user and target_user != username:
                # If viewing another user's file, don't allow saving
                return jsonify({
                    "error": "Permission denied",
                    "message": "You can only edit your own analysis"
                }), 403
            
            # Use current user's path
            save_path = get_user_data_path_in_main(username, pmid)
            print(f"Saving to user directory: {save_path}")
            
            # Check if file already exists in user directory
            existing_file = os.path.join(save_path, 'last_modify_output.json')
            if os.path.exists(existing_file):
                try:
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    print(f"Error reading existing file: {str(e)}")
                    existing_data = {}
            else:
                # If first save, ensure directory exists and copy original file as base
                ensure_directory_exists(save_path)
                original_file = os.path.join(get_main_data_path(pmid), 'original_output.json')
                if os.path.exists(original_file):
                    try:
                        with open(original_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except Exception as e:
                        print(f"Error reading original file: {str(e)}")
                        existing_data = {}
                    
                else:
                    existing_data = {}
        
        # Ensure directory exists
        ensure_directory_exists(save_path)
        
        # Convert frontend data to graph visualization format
        graph_data = convert_frontend_to_graph_format(frontend_data)
        
        # Merge existing data with new data
        # Keep all fields in existing_data, but replace entities and relations with those from graph_data
        final_data = existing_data.copy()
        
        # 只有在没有提供entities数据时，才使用convert_frontend_to_graph_format生成的entities
        # 这样可以保留原始的entities结构（对象格式而非数组）
        entities_from_request = request.json.get('entities')
        if entities_from_request is not None:
            # 如果请求中包含entities数据，直接使用
            final_data["entities"] = entities_from_request
            print(f"Using entities from request ({type(entities_from_request).__name__} format)")
        else:
            # 否则使用从前端数据转换得到的entities列表
            final_data["entities"] = graph_data["entities"]
            print("Using entities from graph_data conversion (list format)")
            
        # 更新relations数据
        final_data["relations"] = graph_data["relations"]
        
        # If context data provided, replace or add to final_data
        if context_data:
            final_data['context'] = context_data
            print(f"Updated context data: {context_data}")
        
        # 在保存前对relations进行排序
        # 获取abstract
        main_path = get_main_data_path(pmid)
        data_file = os.path.join(main_path, 'data.json')
        abstract = ""
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
                abstract = paper_data.get("abstract", "")
        
        # 对relations进行排序
        if "relations" in final_data:
            final_data["relations"] = sort_relations_by_text_position(final_data["relations"], abstract)
        
        # Save modified JSON
        output_path = os.path.join(save_path, 'last_modify_output.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print(f"Saved sorted JSON to: {output_path}")
        
        # Get timestamp
        timestamp = time.time()  # Use current time instead of HTML file modification time
        
        return jsonify({
            "message": "Update received and graph regenerated successfully",
            "data": frontend_data,
            "timestamp": timestamp
        })
        
    except Exception as e:
        print(f"Error processing update: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/load-notes', methods=['GET'])
def load_notes():
    """加载笔记数据"""
    try:
        paper_url = request.args.get('url')
        username = request.args.get('username')
        mode = request.args.get('mode', 'view')
        target_user = request.args.get('target_user', username)  # Get target user, default is current user
        
        if not paper_url or not username:
            return jsonify({"error": "URL and username are required"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        
        # Determine where to load notes based on mode and target user
        if mode == 'temp':
            # Temp mode: load from temporary directory
            notes_path = os.path.join(get_temp_data_path(username, pmid), 'notes.json')
        else:
            # View mode: if target user is Main, load from original_data directory
            if target_user == 'Main':
                notes_path = os.path.join(get_main_data_path(pmid), 'notes.json')
            else:
                # Other users: load from their respective directories
                notes_path = os.path.join(get_user_data_path_in_main(target_user, pmid), 'notes.json')
        
        print(f"Loading notes from: {notes_path}")  # Add log
        
        if os.path.exists(notes_path):
            with open(notes_path, 'r', encoding='utf-8') as f:
                notes = json.load(f)
                # Ensure notes is a dictionary with keys in "head|label|tail" format
                if not isinstance(notes, dict):
                    notes = {}
            return jsonify({"success": True, "notes": notes})
        else:
            return jsonify({"success": True, "notes": {}})
            
    except Exception as e:
        print(f"Error loading notes: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/api/save-notes', methods=['POST'])
def save_notes():
    """Save notes data"""
    try:
        notes = request.json.get('notes')
        paper_url = request.json.get('url')
        username = request.json.get('username')
        mode = request.json.get('mode', 'view')
        target_user = request.json.get('target_user', username)  # Get target user, default is current user
        
        if not paper_url or not username:
            return jsonify({"error": "URL and username are required"}), 400
            
        # Validate notes format
        if not isinstance(notes, dict):
            return jsonify({"error": "Invalid notes format"}), 400
            
        # Validate each key follows "head|label|tail" format
        for key in notes.keys():
            parts = key.split('|')
            if len(parts) != 3:
                return jsonify({"error": f"Invalid key format: {key}"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        
        # Determine save path based on mode and target user
        if mode == 'temp':
            # Temp mode: save to temporary directory
            save_path = get_temp_data_path(username, pmid)
        else:
            # View mode: save to target user directory
            # Validate permissions: only allow saving if current user is target user
            if username != target_user:
                return jsonify({
                    "error": "Permission denied",
                    "message": "You can only save notes to your own directory"
                }), 403
            save_path = get_user_data_path_in_main(target_user, pmid)
            
        ensure_directory_exists(save_path)
        
        notes_path = os.path.join(save_path, 'notes.json')
        print(f"Saving notes to: {notes_path}") 
        
        with open(notes_path, 'w', encoding='utf-8') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
            
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Error saving notes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/original-relations', methods=['GET'])
def get_original_relations():
    """API endpoint to retrieve original relation data"""
    try:
        # Get PMID from request parameters
        pmid = request.args.get('pmid')
        
        if not pmid:
            return jsonify({"error": "PMID parameter is required"}), 400
            
        # Build path to original data file
        main_path = get_main_data_path(pmid)
        output_path = os.path.join(main_path, 'original_output.json')
        
        # Check if file exists
        if not os.path.exists(output_path):
            return jsonify({
                "error": "Original data not found",
                "message": f"No original data found for PMID: {pmid}"
            }), 404
            
        # Read original data
        with open(output_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
            
        return jsonify(original_data)
        
    except Exception as e:
        print(f"Error fetching original relations: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to fetch original relations",
            "message": str(e)
        }), 500
def ensure_users_file():
    """Ensure the user data file exists; if not, create a default file."""
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        default_data = {
            "users": [
                {
                    "id": 1,
                    "username": "Admin"
                }
            ]
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)
    else:
        # Check if the file content is correct
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not data.get('users'):
                data['users'] = [{"id": 1, "username": "Admin"}]
                with open(USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception:
            # If the file is corrupted or incorrectly formatted, recreate it
            default_data = {
                "users": [
                    {
                        "id": 1,
                        "username": "Admin"
                    }
                ]
            }
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get the list of all users"""
    try:
        ensure_users_file()
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure the returned data format is correct
            if not isinstance(data, dict) or 'users' not in data:
                data = {"users": [{"id": 1, "username": "Admin"}]}
            # Ensure the Admin user always exists
            admin_exists = any(user['username'] == 'Admin' for user in data['users'])
            if not admin_exists:
                data['users'].insert(0, {"id": 1, "username": "Admin"})
            return jsonify(data)
    except Exception as e:
        print(f"Error loading users: {str(e)}")
        # Return default data in case of an error
        return jsonify({"users": [{"id": 1, "username": "Admin"}]})

@app.route('/api/users', methods=['POST'])
def add_user():
    """Add a new user"""
    try:
        username = request.json.get('username')
        if not username:
            return jsonify({"error": "Username is required"}), 400

        ensure_users_file()
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if the username already exists
        if any(user['username'] == username for user in data['users']):
            return jsonify({"error": "Username already exists"}), 400

        # Generate a new user ID
        new_id = max([user['id'] for user in data['users']], default=0) + 1
        
        # Add the new user
        data['users'].append({
            "id": new_id,
            "username": username
        })

        # Save the updated data
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "User added successfully"})

    except Exception as e:
        print(f"Error adding user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['GET'])
def get_comments():
    """Get paper comments"""
    try:
        paper_url = request.args.get('url')
        if not paper_url:
            return jsonify({"error": "URL parameter is required"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # Read comments directly from the original data file
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({"comments": data.get('comments', [])})
        return jsonify({"comments": []})
        
    except Exception as e:
        print(f"Error loading comments: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['POST'])
def add_comment():
    """Add a new comment"""
    try:
        data = request.json
        paper_url = data.get('url')
        username = data.get('username')
        content = data.get('content')
        parent_id = data.get('parent_id')
        is_main_comment = data.get('is_main_comment', False)
        
        if not all([paper_url, username, content]):
            return jsonify({"error": "Missing required fields"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # Read original data
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
                if 'comments' not in paper_data:
                    paper_data['comments'] = []
        else:
            return jsonify({"error": "Paper data not found"}), 404
        
        # Generate new comment ID
        if is_main_comment:
            # Main comment ID format: c_1, c_2, ...
            comment_ids = [int(c['id'].split('_')[1]) for c in paper_data['comments'] if c['id'].startswith('c_')]
            new_id = f"c_{max(comment_ids, default=0) + 1}"
        else:
            # Reply ID format: r_i_j
            if not parent_id:
                return jsonify({"error": "Parent ID is required for replies"}), 400
                
            if parent_id.startswith('c_'):
                # Reply to main comment
                comment_num = parent_id.split('_')[1]
                parent_comment = next((c for c in paper_data['comments'] if c['id'] == parent_id), None)
                if not parent_comment:
                    return jsonify({"error": "Parent comment not found"}), 404
                reply_nums = [int(r['id'].split('_')[2]) for r in parent_comment['replies'] if r['id'].startswith(f'r_{comment_num}_')]
                new_id = f"r_{comment_num}_{max(reply_nums, default=0) + 1}"
            else:
                # Reply to other replies
                comment_num = parent_id.split('_')[1]
                parent_comment = next((c for c in paper_data['comments'] if c['id'] == f'c_{comment_num}'), None)
                if not parent_comment:
                    return jsonify({"error": "Parent comment not found"}), 404
                reply_nums = [int(r['id'].split('_')[2]) for r in parent_comment['replies'] if r['id'].startswith(f'r_{comment_num}_')]
                new_id = f"r_{comment_num}_{max(reply_nums, default=0) + 1}"
        
        # Create new comment
        new_comment = {
            "id": new_id,
            "username": username,
            "content": content,
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "parent_id": parent_id,
            "replies": [] if is_main_comment else None,
            "is_deleted": False
        }
        
        # If replying to another reply, add quoted content
        if data.get('quoted_username') and data.get('quoted_content'):
            new_comment['quoted_username'] = data['quoted_username']
            new_comment['quoted_content'] = data['quoted_content']
            new_comment['quoted_id'] = data.get('quoted_id')
        
        if is_main_comment:
            # If it's a main comment, directly add to the comments list
            paper_data['comments'].append(new_comment)
        else:
            # If it's a reply, add to the parent comment's replies
            parent_comment = next((c for c in paper_data['comments'] if c['id'] == f"c_{new_id.split('_')[1]}"), None)
            if parent_comment:
                if not parent_comment.get('replies'):
                    parent_comment['replies'] = []
                parent_comment['replies'].append(new_comment)
            else:
                return jsonify({"error": "Parent comment not found"}), 404
        
        # Save directly to the original data file
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)
            
        return jsonify({"success": True, "comment": new_comment})
        
    except Exception as e:
        print(f"Error adding comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>', methods=['DELETE'])
def delete_comment_by_id(comment_id):
    """Delete comment"""
    try:
        paper_url = request.args.get('url')
        username = request.args.get('username')
        
        if not all([paper_url, username]):
            return jsonify({"error": "Missing required parameters"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # Read original data
        if not os.path.exists(data_path):
            return jsonify({"error": "Paper data not found"}), 404
            
        with open(data_path, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)
        
        def find_comment_recursive(comments, target_id):
            """Recursively find comment"""
            if target_id.startswith('c_'):
                # Find main comment
                return next((c for c in comments if c['id'] == target_id), None)
            else:
                # Find reply
                comment_num = target_id.split('_')[1]
                parent_comment = next((c for c in comments if c['id'] == f'c_{comment_num}'), None)
                if parent_comment and parent_comment.get('replies'):
                    return next((r for r in parent_comment['replies'] if r['id'] == target_id), None)
            return None

        def delete_comment_recursive(comments, target_id, user):
            """Recursively delete comment"""
            if target_id.startswith('c_'):
                # Delete main comment
                for i, comment in enumerate(comments):
                    if comment['id'] == target_id:
                        if comment['username'] != user:
                            return False, "Unauthorized"
                        
                        if comment.get('replies'):
                            active_replies = [r for r in comment['replies'] if not r.get('is_deleted', False)]
                            if active_replies:
                                comment['is_deleted'] = True
                                return True, "Comment marked as deleted"
                            else:
                                comments.pop(i)
                                return True, "Comment and all replies deleted"
                        else:
                            comments.pop(i)
                            return True, "Comment deleted"
            else:
                # Delete reply
                comment_num = target_id.split('_')[1]
                parent_comment = next((c for c in comments if c['id'] == f'c_{comment_num}'), None)
                if parent_comment and parent_comment.get('replies'):
                    for i, reply in enumerate(parent_comment['replies']):
                        if reply['id'] == target_id:
                            if reply['username'] != user:
                                return False, "Unauthorized"
                            parent_comment['replies'].pop(i)
                            # If parent comment is marked deleted and has no other undeleted replies, delete parent comment
                            if parent_comment.get('is_deleted') and not [r for r in parent_comment['replies'] if not r.get('is_deleted', False)]:
                                comments.remove(parent_comment)
                            return True, "Reply deleted"
            return False, "Comment not found"

        success, message = delete_comment_recursive(paper_data['comments'], comment_id, username)
        if success:
            # Save directly to the original data file
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, indent=2, ensure_ascii=False)
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"error": message}), 403
            
    except Exception as e:
        print(f"Error deleting comment: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>', methods=['PUT'])
def update_comment_by_id(comment_id):
    """Update comment content"""
    try:
        data = request.json
        paper_url = data.get('url')
        username = data.get('username')
        content = data.get('content')
        
        if not all([paper_url, username, content]):
            return jsonify({"error": "Missing required fields"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # Read original data
        if not os.path.exists(data_path):
            return jsonify({"error": "Paper data not found"}), 404
            
        with open(data_path, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)
        
        def update_comment_recursive(comments, target_id, user, new_content):
            """Recursively update comment"""
            if target_id.startswith('c_'):
                # Update main comment
                comment = next((c for c in comments if c['id'] == target_id), None)
                if comment and comment['username'] == user:
                    comment['content'] = new_content
                    comment['timestamp'] = datetime.now(pytz.UTC).isoformat()
                    return True
            else:
                # Update reply
                comment_num = target_id.split('_')[1]
                parent_comment = next((c for c in comments if c['id'] == f'c_{comment_num}'), None)
                if parent_comment and parent_comment.get('replies'):
                    reply = next((r for r in parent_comment['replies'] if r['id'] == target_id), None)
                    if reply and reply['username'] == user:
                        reply['content'] = new_content
                        reply['timestamp'] = datetime.now(pytz.UTC).isoformat()
                        return True
            return False
        
        if update_comment_recursive(paper_data['comments'], comment_id, username, content):
            # Save directly to the original data file
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, indent=2, ensure_ascii=False)
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Comment not found or unauthorized"}), 403
            
    except Exception as e:
        print(f"Error updating comment: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/complete-analysis', methods=['POST'])
def complete_analysis():
    """完成论文分析，将临时目录的内容复制到用户目录"""
    try:
        data = request.json
        paper_url = data.get('url')
        username = data.get('username')
        
        if not paper_url or not username:
            return jsonify({"error": "URL and username are required"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        temp_path = get_temp_data_path(username, pmid)
        user_path = get_user_data_path_in_main(username, pmid)
        
        # 验证临时目录是否存在
        if not os.path.exists(temp_path):
            return jsonify({
                "error": "No temporary data found",
                "message": "Please save your changes before completing the analysis"
            }), 400
            
        # 验证必要文件是否存在
        required_files = ['last_modify_output.json']
        missing_files = [f for f in required_files if not os.path.exists(os.path.join(temp_path, f))]
        if missing_files:
            return jsonify({
                "error": "Missing required files",
                "message": f"The following files are missing: {', '.join(missing_files)}"
            }), 400
        
        # 确保目标目录存在
        ensure_directory_exists(user_path)
        
        # 复制文件
        files_to_copy = [
            'last_modify_output.json',
            'notes.json'  # 笔记文件是可选的
        ]
        
        for file_name in files_to_copy:
            src = os.path.join(temp_path, file_name)
            dst = os.path.join(user_path, file_name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {file_name} from {src} to {dst}")
        
        # 删除临时目录
        shutil.rmtree(temp_path)
        print(f"Removed temporary directory: {temp_path}")
        
        # 记录完成信息到统计文件
        try:
            # 加载统计数据
            statistics = load_statistics()
            
            # 获取当前时间的Unix时间戳
            complete_time_unix = int(time.time())
            
            # 确保pmid存在于统计数据中
            if pmid not in statistics:
                statistics[pmid] = {}
            
            # 确保Complete_Information存在
            if "Complete_Information" not in statistics[pmid]:
                statistics[pmid]["Complete_Information"] = {}
            
            # 记录用户完成时间
            statistics[pmid]["Complete_Information"][username] = complete_time_unix
            
            # 保存统计数据
            save_statistics(statistics)
            
            print(f"Recorded completion for user {username} on paper {pmid} at {complete_time_unix}")
        except Exception as e:
            print(f"Error recording completion information: {str(e)}")
            # 不返回错误，继续执行
            
        return jsonify({"success": True, "message": "Analysis completed successfully"})
        
    except Exception as e:
        print(f"Error completing analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/papers', methods=['GET'])
def get_papers():
    """Get the list of papers. If a username is provided, only return the papers that the user has access to."""
    try:
        username = request.args.get('username')  # Get username parameter
        papers = []
        
        # Load user access data
        user_access = load_user_access()
        
        # Iterate through the Main_dir directory
        for pmid in os.listdir(MAIN_DIR):
            paper_path = os.path.join(MAIN_DIR, pmid)
            if os.path.isdir(paper_path):
                # Check if the paper is fully processed
                if not is_paper_fully_processed(pmid):
                    continue
                    
                # If a username is specified, check if the user has access to this paper
                if username and username != 'Admin':  # Admin can see all papers
                    # Check user access
                    if pmid not in user_access or username not in user_access[pmid].get('access_users', []):
                        continue
                
                # Read paper data
                data_file = os.path.join(paper_path, 'original_data', 'data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r', encoding='utf-8') as f:
                        paper_data = json.load(f)
                        
                    # Get the list of assigned users
                    assigned_users = ['Main']  # Default includes Main
                    user_dir = os.path.join(paper_path, 'User_dir')
                    if os.path.exists(user_dir):
                        # Add all users under User_dir
                        for user in os.listdir(user_dir):
                            if os.path.isdir(os.path.join(user_dir, user)):
                                assigned_users.append(user)
                    
                    # Construct paper information and add extraction_time
                    paper_info = {
                        'pmid': pmid,
                        'title': paper_data.get('title', ''),
                        'assigned_user': assigned_users,
                        'extraction_time': paper_data.get('extraction_time', '')  # Add extraction_time
                    }
                    papers.append(paper_info)
        
        return jsonify({'papers': papers})
        
    except Exception as e:
        print(f"Error getting papers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
@app.route('/api/initialize-paper', methods=['POST'])
def initialize_paper():
    """API endpoint to initialize paper data"""
    try:
        # Get paper URL and username from the request
        data = request.json
        paper_url = data.get('url')
        username = data.get('username')
        
        if not paper_url:
            return jsonify({"error": "URL is required"}), 400
            
        if not username:
            return jsonify({"error": "Username is required"}), 400
            
        # Get PMID
        pmid = paper_url.rstrip('/').split('/')[-1]
        data_path = get_paper_data_path(pmid)
        
        # Check if the paper already exists
        if os.path.exists(data_path):
            # Even if the paper exists, add user access permissions
            try:
                access_data = load_user_access()
                if pmid not in access_data:
                    access_data[pmid] = {"access_users": []}
                if username not in access_data[pmid]["access_users"] and username != "Admin" and username != "Main":
                    access_data[pmid]["access_users"].append(username)
                    save_user_access(access_data)
                    print(f"Added access for user {username} to existing paper {pmid}")
                else:
                    print(f"Skipped adding access for user {username} to existing paper {pmid} (Admin/Main user or already has access)")
            except Exception as e:
                print(f"Error updating user access for existing paper: {str(e)}")
            
            return jsonify({
                "error": "Paper already exists",
                "message": "Paper already scraped"
            }), 409
            
        # Call the initialization function
        try:
            article_data = initialize_paper_data(paper_url)
            if article_data is None:
                return jsonify({
                    "error": "Failed to initialize paper",
                    "message": "Paper is already being processed"
                }), 409
                
            # Generate initial analysis
            analysis_data = generate_initial_analysis(article_data, pmid)
            
            # After processing the paper, add user access permissions
            try:
                access_data = load_user_access()
                if pmid not in access_data:
                    access_data[pmid] = {"access_users": []}
                if username not in access_data[pmid]["access_users"] and username != "Admin" and username != "Main":
                    access_data[pmid]["access_users"].append(username)
                    save_user_access(access_data)
                    print(f"Added access for user {username} to new paper {pmid}")
                else:
                    print(f"Skipped adding access for user {username} to new paper {pmid} (Admin/Main user or already has access)")
            except Exception as e:
                print(f"Error updating user access: {str(e)}")
            
            return jsonify({
                "success": True,
                "message": "Paper initialized successfully",
                "data": article_data,
                "analysis": analysis_data
            })
            
        except Exception as e:
            print(f"Error initializing paper: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to initialize paper",
                "message": str(e)
            }), 500
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

def validate_pubmed_url(url):
    """Validate PubMed URL format"""
    url = url.strip()
    if not url:  # Skip empty lines
        return None
    url_pattern = r'^https:\/\/pubmed\.ncbi\.nlm\.nih\.gov\/\d+\/?$'
    if re.match(url_pattern, url):
        return url
    return False

def process_queue():
    """Process all papers in the queue, directly calling the single paper processing method"""
    global completed_papers, total_papers_to_scrape
    
    # 使用锁保护对共享资源的访问
    with progress_lock:
        # Reset progress tracking
        completed_papers.clear()
        total_papers_to_scrape = scraping_queue.qsize()
        print(f"Initialized queue processing with {total_papers_to_scrape} papers")

def process_paper_with_retry(url, max_retries=3, retry_delay=5):
    """Process a single paper with retry mechanism
    
    Args:
        url: Paper URL
        max_retries: Maximum number of retries
        retry_delay: Retry interval (seconds)
    
    Returns:
        tuple: (success, article_data, error_message)
    """
    pmid = url.rstrip('/').split('/')[-1]
    print(f"Starting to process paper: {pmid} (URL: {url})")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"Retrying paper {pmid} (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                
            # Wait for scraping and analysis to complete
            print(f"Scraping paper {pmid}...")
            success = scrape_paper(pmid, url)
            
            if success:
                print(f"Paper {pmid} scraped successfully, checking if fully processed...")
                if is_paper_fully_processed(pmid):  # Ensure the paper is fully processed
                    # Read the generated data
                    data_path = get_paper_data_path(pmid)
                    print(f"Reading data for paper {pmid} from {data_path}")
                    with open(data_path, 'r', encoding='utf-8') as f:
                        article_data = json.load(f)
                    print(f"Paper {pmid} processing completed successfully")
                    return True, article_data, None
                else:
                    print(f"Paper {pmid} is not fully processed after scraping")
                    raise Exception(f"Paper {pmid} processing incomplete")
            else:
                print(f"Failed to scrape paper {pmid}")
                raise Exception(f"Failed to scrape paper {pmid}")
                
        except Exception as e:
            error_message = str(e)
            print(f"Attempt {attempt + 1}/{max_retries} for paper {pmid} failed: {error_message}")
            if attempt == max_retries - 1:  # Last attempt
                print(f"All attempts failed for paper {pmid}: {error_message}")
                return False, None, error_message
            
    return False, None, "Maximum retries exceeded"

def process_papers_async():
    """Asynchronously process the paper queue with parallel execution"""
    # 设置最大并发数
    MAX_CONCURRENT_PAPERS = 30
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PAPERS) as executor:
        # 收集所有任务
        future_to_paper = {}
        paper_info = {}  # 存储URL和用户名的映射
        
        # 从队列中获取所有论文并提交到线程池
        while not scraping_queue.empty():
            url, username = scraping_queue.get()
            pmid = url.rstrip('/').split('/')[-1]
            
            # 使用锁保护对in_progress_papers的访问
            with progress_lock:
                in_progress_papers.add(pmid)  # 添加到处理中集合
            
            # 存储URL和用户名信息以便后续使用
            paper_info[pmid] = {'url': url, 'username': username}
            
            # 提交任务到线程池
            future = executor.submit(process_paper_with_retry, url)
            future_to_paper[future] = pmid
            
        # 处理完成的任务结果
        for future in concurrent.futures.as_completed(future_to_paper):
            pmid = future_to_paper[future]
            url = paper_info[pmid]['url']
            username = paper_info[pmid]['username']
            
            try:
                success, article_data, error_message = future.result()
                
                # 使用锁保护对completed_papers的访问
                with progress_lock:
                    if success:
                        print(f"Successfully processed paper: {url}")
                        # 处理成功，添加用户访问权限
                        try:
                            access_data = load_user_access()
                            if pmid not in access_data:
                                access_data[pmid] = {"access_users": []}
                            if username not in access_data[pmid]["access_users"] and username != "Admin" and username != "Main":
                                access_data[pmid]["access_users"].append(username)
                                save_user_access(access_data)
                                print(f"Added access for user {username} to batch paper {pmid}")
                            else:
                                print(f"Skipped adding access for user {username} to batch paper {pmid} (Admin/Main user or already has access)")
                        except Exception as e:
                            print(f"Error updating user access: {str(e)}")
                        
                        # 添加到成功列表
                        completed_papers.append({
                            'url': url,
                            'pmid': pmid,
                            'status': 'success'
                        })
                    else:
                        print(f"Failed to process paper: {url}")
                        # 记录失败的论文
                        completed_papers.append({
                            'url': url,
                            'pmid': pmid,
                            'status': 'failed',
                            'error': error_message
                        })
            except Exception as e:
                print(f"Error processing paper {url}: {str(e)}")
                # 使用锁保护对completed_papers的访问
                with progress_lock:
                    # 记录处理出错的论文
                    completed_papers.append({
                        'url': url,
                        'pmid': pmid,
                        'status': 'error',
                        'error': str(e)
                    })
            finally:
                # 使用锁保护对in_progress_papers的访问
                with progress_lock:
                    # 从处理中集合移除并标记队列任务完成
                    in_progress_papers.remove(pmid)
                scraping_queue.task_done()

@app.route('/api/scraping-status', methods=['GET'])
def get_scraping_status():
    """Get current scraping status"""
    try:
        # 使用锁保护对共享资源的访问
        with progress_lock:
            # Calculate the actual number of remaining papers: in the queue + in progress
            remaining_papers = scraping_queue.qsize() + len(in_progress_papers)
            
            # 创建返回数据的副本，避免在返回过程中修改数据
            status_data = {
                "total_papers": total_papers_to_scrape,
                "completed_papers": list(completed_papers),  # 创建副本
                "remaining_papers": remaining_papers,
                "in_progress": list(in_progress_papers)  # 创建副本
            }
            
        return jsonify(status_data)
    except Exception as e:
        print(f"Error getting scraping status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch-initialize', methods=['POST'])
def batch_initialize():
    """API endpoint to batch initialize paper data"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
            
        file = request.files['file']
        username = request.form.get('username')
        
        if not username:
            return jsonify({"error": "Username is required"}), 400
            
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        if not file.filename.endswith('.txt'):
            return jsonify({"error": "Only .txt files are allowed"}), 400
            
        # Read and validate all URLs
        urls = []
        invalid_line = None
        line_number = 0
        
        for line in file:
            line_number += 1
            url = line.decode('utf-8').strip()
            if not url:  # Skip empty lines
                continue
                
            result = validate_pubmed_url(url)
            if result is False:  # Invalid URL format
                invalid_line = line_number
                break
            elif result is not None:  # Valid and non-empty URL
                urls.append(url)
        
        if invalid_line is not None:
            return jsonify({
                "error": f"Invalid URL format at line {invalid_line}",
                "message": "Please ensure all URLs are valid PubMed URLs"
            }), 400
        
        # Add all URLs to the queue
        for url in urls:
            scraping_queue.put((url, username))  # Put username and URL into the queue together
        
        # Initialize progress tracking
        process_queue()
        
        # Start processing the queue in a new thread
        processing_thread = Thread(target=process_papers_async)
        processing_thread.daemon = True
        processing_thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Started processing {len(urls)} papers in parallel",
            "total": len(urls),
            "processing": len(urls)
        })
        
    except Exception as e:
        print(f"Error processing batch initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get graph data"""
    try:
        # Get request parameters
        pmid = request.args.get('pmid')
        username = request.args.get('username')
        mode = request.args.get('mode', 'view')
        target_user = request.args.get('target_user', username)
        
        # Determine JSON file path based on mode and target user
        if mode == 'temp':
            # Temporary mode: load from temporary directory
            graph_file_path = os.path.join(get_temp_data_path(username, pmid), 'last_modify_output.json')
        else:
            # View mode: load from target user's directory
            graph_file_path = os.path.join(get_user_data_path_in_main(target_user, pmid), 'last_modify_output.json')
            
            # If the target user's directory does not have the file, use the original data
            if not os.path.exists(graph_file_path):
                graph_file_path = os.path.join(get_main_data_path(pmid), 'original_output.json')
        
        print(f"Loading graph data from: {graph_file_path}")
        
        # Check if the file exists
        if not os.path.exists(graph_file_path):
            return jsonify({"error": "Graph data file not found"}), 404
            
        # Read and return graph data
        with open(graph_file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        # Only return the relations field
        response_data = {"relations": graph_data.get("relations", [])}
        
        # Add CORS headers directly to the response
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
        
    except Exception as e:
        print(f"Error loading graph data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Add static file route
@app.route('/api/lib/<path:filename>')
def serve_lib(filename):
    """Provide static file service for visualization library"""
    try:
        # Assume the lib folder is in the project root directory
        return send_from_directory(os.path.join(ROOT_DIR, 'lib'), filename)
    except Exception as e:
        print(f"Error serving static file: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/api/reset-to-main', methods=['POST'])
def reset_to_main():
    """Reset user's temporary directory to the original version in the main directory"""
    try:
        data = request.json
        paper_url = data.get('url')
        username = data.get('username')
        
        if not paper_url or not username:
            return jsonify({"error": "URL and username are required"}), 400
            
        pmid = paper_url.rstrip('/').split('/')[-1]
        temp_path = get_temp_data_path(username, pmid)
        main_path = get_main_data_path(pmid)
        
        # Ensure the temporary directory exists
        ensure_directory_exists(temp_path)
        
        # Copy original files to the temporary directory
        files_to_copy = [
            ('original_output.json', 'last_modify_output.json'),
        ]
        
        for src_name, dst_name in files_to_copy:
            src = os.path.join(main_path, src_name)
            dst = os.path.join(temp_path, dst_name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {src_name} to {dst}")
            else:
                return jsonify({
                    "error": f"Original file {src_name} not found",
                    "message": "Could not find original files to reset to"
                }), 404
                
        # Delete notes file if it exists
        notes_file = os.path.join(temp_path, 'notes.json')
        if os.path.exists(notes_file):
            os.remove(notes_file)
            print(f"Removed notes file: {notes_file}")
            
        return jsonify({
            "success": True,
            "message": "Successfully reset to Main version"
        })
        
    except Exception as e:
        print(f"Error resetting to main: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-papers', methods=['POST'])
def download_papers():
    """Package selected papers into a ZIP file for download"""
    try:
        data = request.json
        pmids = data.get('pmids', [])
        
        if not pmids:
            return jsonify({"error": "No papers selected"}), 400
            
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Iterate through all selected PMIDs
            for pmid in pmids:
                paper_path = os.path.join(MAIN_DIR, pmid)
                
                # Check if the paper directory exists
                if not os.path.exists(paper_path):
                    print(f"Warning: Paper directory not found for PMID {pmid}")
                    continue
                    
                # Iterate through all files and subdirectories in the paper directory
                for root, dirs, files in os.walk(paper_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate the relative path of the file in the ZIP
                        arcname = os.path.join(f"Papers/{pmid}", os.path.relpath(file_path, paper_path))
                        # Add the file to the ZIP
                        zf.write(file_path, arcname)
                        
        # Move the file pointer to the beginning
        memory_file.seek(0)
        
        # Return the ZIP file
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='Papers.zip'
        )
        
    except Exception as e:
        print(f"Error creating ZIP file: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/type-name-config', methods=['GET'])
def get_type_name_config():
    """Get Type and Name configuration data"""
    try:
        # Ensure the configuration file exists
        if not os.path.exists(TYPE_NAME_CONFIG_FILE):
            # If the file does not exist, create a default configuration file
            default_config = {
                "type": ["General Information", "Disease", "Cell/Tissue-Specific"],
                "name": ["Cancer", "Inflammation", "Cell-Type Specific"]
            }
            with open(TYPE_NAME_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            return jsonify(default_config)
        
        # Read the configuration file
        with open(TYPE_NAME_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify(config_data)
    
    except Exception as e:
        print(f"Error loading type-name configuration: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/type-name-config', methods=['PUT'])
def update_type_name_config():
    """Update Type and Name configuration data"""
    try:
        # Get the configuration data from the request
        config_data = request.json
        
        # Validate the data structure
        if 'type' not in config_data or 'name' not in config_data:
            return jsonify({"error": "Invalid configuration format. 'type' and 'name' fields are required."}), 400
        
        if not isinstance(config_data['type'], list) or not isinstance(config_data['name'], list):
            return jsonify({"error": "Invalid configuration format. 'type' and 'name' must be arrays."}), 400
        
        # Save the configuration to the file
        with open(TYPE_NAME_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        return jsonify({"success": True, "message": "Configuration updated successfully"})
    
    except Exception as e:
        print(f"Error updating type-name configuration: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompt-config', methods=['GET'])
def get_prompt_config():
    """Get prompt configuration"""
    try:
        if not os.path.exists(PROMPT_CONFIG_FILE):
            # If the file does not exist, return default configuration
            default_config = {
                "PROMPT_TEMPLATE": "Default prompt template",
                "JSON_PROMPT_TEMPLATE": "Default JSON prompt template"
            }
            return jsonify(default_config)
        
        with open(PROMPT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return jsonify(config)
    except Exception as e:
        print(f"Error loading prompt configuration: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompt-config', methods=['PUT'])
def update_prompt_config():
    """Update prompt configuration"""
    try:
        data = request.get_json()
        
        # Validate the data structure
        if 'PROMPT_TEMPLATE' not in data or 'JSON_PROMPT_TEMPLATE' not in data:
            return jsonify({"error": "Invalid data structure"}), 400
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(PROMPT_CONFIG_FILE), exist_ok=True)
        
        # Save the configuration to the file
        with open(PROMPT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating prompt configuration: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get statistics data for the admin dashboard"""
    try:
        print("Starting to retrieve dashboard statistics...")
        result = {
            "total_papers": 0,
            "papers_need_curation": 0,
            "total_edit_papers": 0,
            "edit_submissions_today": 0,
            "last_7_days_submissions": [0, 0, 0, 0, 0, 0, 0]  # Initialize data for the last 7 days
        }
        
        # 1. Calculate Total Papers: Number of directories under MAIN_DIR
        try:
            if os.path.exists(MAIN_DIR):
                result["total_papers"] = len([name for name in os.listdir(MAIN_DIR) if os.path.isdir(os.path.join(MAIN_DIR, name))])
                print(f"Total Papers calculation completed: {result['total_papers']}")
            else:
                print(f"Warning: Main_dir path does not exist: {MAIN_DIR}")
        except Exception as e:
            print(f"Error calculating Total Papers: {str(e)}")
        
        # 2. Calculate Papers Need Curation: Number of papers with User_dir and at least 2 folders under User_dir
        try:
            if os.path.exists(MAIN_DIR):
                for pmid in os.listdir(MAIN_DIR):
                    pmid_path = os.path.join(MAIN_DIR, pmid)
                    user_dir_path = os.path.join(pmid_path, 'User_dir')
                    if os.path.isdir(pmid_path) and os.path.exists(user_dir_path):
                        # Count the number of directories under User_dir
                        user_count = len([name for name in os.listdir(user_dir_path) 
                                         if os.path.isdir(os.path.join(user_dir_path, name))])
                        if user_count >= 2:
                            result["papers_need_curation"] += 1
                print(f"Papers Need Curation calculation completed: {result['papers_need_curation']}")
        except Exception as e:
            print(f"Error calculating Papers Need Curation: {str(e)}")
        
        # 3. Calculate Total Edit Papers: Number of papers with Edit_Information in statistic.json
        try:
            statistics = load_statistics()
            # Count the number of papers with Edit_Information
            result["total_edit_papers"] = sum(1 for pmid in statistics.keys() 
                                            if 'Edit_Information' in statistics[pmid])
            
            # Count the number of papers that have completed curation
            result["curated_papers"] = sum(1 for pmid in statistics.keys() 
                                         if 'curation_merge_time' in statistics[pmid])
            
            print(f"Total Edit Papers calculation completed: {result['total_edit_papers']}")
            print(f"Curated Papers calculation completed: {result['curated_papers']}")
        except Exception as e:
            print(f"Error calculating Papers statistics: {str(e)}")
        
        # 4. Calculate Edit Submissions Today: Number of edit submissions today (count each paper only once per day)
        try:
            # Get today's start timestamp (00:00:00, using UTC time)
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_timestamp = int(today_start.timestamp())
            print(f"Today's start timestamp: {today_start_timestamp}")
            
            # Use a set to track papers edited today, ensuring each paper is counted only once
            edited_papers_today = set()
            
            # Iterate through all edit records
            for pmid, paper_data in statistics.items():
                if "Edit_Information" in paper_data:
                    for username, edits in paper_data["Edit_Information"].items():
                        for edit in edits:
                            # Check if it is a dictionary format
                            if isinstance(edit, dict) and "Edit_Time_As_Unix" in edit:
                                # Check if it is an edit today
                                edit_time = edit["Edit_Time_As_Unix"]
                                if edit_time >= today_start_timestamp and pmid not in edited_papers_today:
                                    edited_papers_today.add(pmid)
                                    result["edit_submissions_today"] += 1
                                    print(f"Found today's edit: Paper ID {pmid}, Timestamp {edit_time}")
                                    break  # After finding one edit for today, do not continue checking other edits for this paper
            
            print(f"Edit Submissions Today calculation completed: {result['edit_submissions_today']}")
        except Exception as e:
            print(f"Error calculating Edit Submissions Today: {str(e)}")
            
        # 5. Calculate the number of edit submissions in the past 7 days (count each paper only once per day)
        try:
            print("Starting to calculate the number of paper edits in the past 7 days...")
            
            # Calculate the start timestamp for the past 7 days (UTC time)
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            day_timestamps = []
            
            # Generate date boundaries for the past 7 days (from oldest to most recent)
            for i in range(7, 0, -1):
                day_date = today - timedelta(days=i-1)
                day_timestamps.append(int(day_date.timestamp()))
            
            # Timestamp for the next day (as a boundary)
            next_day = today + timedelta(days=1)
            next_day_timestamp = int(next_day.timestamp())
            day_timestamps.append(next_day_timestamp)
            
            print(f"Calculated timestamp boundaries for the past 7 days: {day_timestamps}")
            
            # Initialize count array
            daily_counts = [0, 0, 0, 0, 0, 0, 0]
            
            # Use a set to track papers edited each day, ensuring each paper is counted only once
            daily_edited_papers = [set() for _ in range(7)]
            
            # Iterate through all edit records
            for pmid, paper_data in statistics.items():
                if "Edit_Information" in paper_data:
                    for username, edits in paper_data["Edit_Information"].items():
                        for edit in edits:
                            # Check if it is a dictionary format
                            if isinstance(edit, dict) and "Edit_Time_As_Unix" in edit:
                                edit_time = edit["Edit_Time_As_Unix"]
                                
                                # Determine which day the edit belongs to
                                for i in range(7):
                                    if day_timestamps[i] <= edit_time < day_timestamps[i+1]:
                                        # If this paper has not been counted for this day, increment the count
                                        if pmid not in daily_edited_papers[i]:
                                            daily_counts[i] += 1
                                            daily_edited_papers[i].add(pmid)
                                        break
            
            result["last_7_days_submissions"] = daily_counts
            print(f"Calculation of the number of paper edits in the past 7 days completed: {daily_counts}")
            
        except Exception as e:
            print(f"Error calculating the number of paper edits in the past 7 days: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"Dashboard statistics calculation completed, returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error occurred while retrieving dashboard statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        # Even if an error occurs, return a valid data structure
        return jsonify({
            "total_papers": 0,
            "papers_need_curation": 0,
            "total_edit_papers": 0,
            "edit_submissions_today": 0,
            "last_7_days_submissions": [0, 0, 0, 0, 0, 0, 0],
            "error": str(e)
        })

@app.route('/api/user-completion-overview', methods=['GET'])
def get_user_completion_overview():
    """获取用户完成论文的进度概览"""
    try:
        """
        # Mock data for test.
        mock_data = {
            'users': [
                {
                    'username': 'Xi Xu',
                    'assigned_papers': 20,
                    'completed_papers': 20,
                    'completion_rate': 100.00
                },
                {
                    'username': 'Sumin',
                    'assigned_papers': 18,
                    'completed_papers': 15,
                    'completion_rate': 83.33
                },
                {
                    'username': 'Yufei',
                    'assigned_papers': 12,
                    'completed_papers': 6,
                    'completion_rate': 50.00
                },
                {
                    'username': 'LeiLi',
                    'assigned_papers': 10,
                    'completed_papers': 3,
                    'completion_rate': 30.00
                },
                {
                    'username': 'ado',
                    'assigned_papers': 20,
                    'completed_papers': 1,
                    'completion_rate': 5.00
                },
                {
                    'username': 'user1',
                    'assigned_papers': 15,
                    'completed_papers': 0,
                    'completion_rate': 0.00
                },
                {
                    'username': 'user2',
                    'assigned_papers': 0,
                    'completed_papers': 0,
                    'completion_rate': 0.00
                }
            ]
        }
        return jsonify(mock_data)
        """
        # 1. 获取所有用户
        users_data = []
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_data = json.load(f).get('users', [])
        
        # 2. 获取用户访问权限数据
        user_access_data = load_user_access()
        
        # 3. 获取统计数据
        statistics = load_statistics()
        
        # 4. 计算每个用户的完成率
        result = []
        for user in users_data:
            username = user.get('username')
            if username == 'Admin':  # 跳过Admin用户
                continue
                
            # 获取分配给该用户的论文列表
            assigned_papers = []
            for pmid, paper_data in user_access_data.items():
                if username in paper_data.get('access_users', []):
                    assigned_papers.append(pmid)
            
            # 获取该用户已完成的论文列表
            completed_papers = []
            for pmid, paper_stats in statistics.items():
                if "Complete_Information" in paper_stats and username in paper_stats["Complete_Information"]:
                    # 只有当这篇论文也分配给了该用户时才计算
                    if pmid in assigned_papers:
                        completed_papers.append(pmid)
            
            # 计算完成率
            total_assigned = len(assigned_papers)
            total_completed = len(completed_papers)
            completion_rate = 0
            if total_assigned > 0:
                completion_rate = (total_completed / total_assigned) * 100
            
            # 添加到结果中
            user_data = {
                'username': username,
                'assigned_papers': total_assigned,
                'completed_papers': total_completed,
                'completion_rate': round(completion_rate, 2)  # 保留两位小数
            }
            result.append(user_data)
        
        # 5. 按完成率从高到低排序
        result.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return jsonify({'users': result})
        
    except Exception as e:
        print(f"Error getting user completion overview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/curation-papers', methods=['GET'])
def get_curation_papers():
    """Get the list of papers that need curation
    The papers must have a folder under Main_dir, and the User_dir folder must have >=2 subfolders
    """
    try:
        papers = []
        
        # Check if Main_dir exists
        if not os.path.exists(MAIN_DIR):
            print(f"Warning: Main_dir path does not exist: {MAIN_DIR}")
            return jsonify({"papers": [], "message": "Main directory not found"})
        
        # Iterate through all paper folders under Main_dir
        for pmid in os.listdir(MAIN_DIR):
            pmid_path = os.path.join(MAIN_DIR, pmid)
            user_dir_path = os.path.join(pmid_path, 'User_dir')
            
            # Check if it is a directory and has a User_dir subdirectory
            if os.path.isdir(pmid_path) and os.path.exists(user_dir_path):
                # Get the list of subfolders under User_dir (user list)
                users = []
                user_creation_times = []
                
                for user in os.listdir(user_dir_path):
                    user_folder_path = os.path.join(user_dir_path, user)
                    if os.path.isdir(user_folder_path):
                        users.append(user)
                        # Try to get the folder creation time
                        try:
                            creation_time = os.path.getctime(user_folder_path)
                            user_creation_times.append((user, creation_time))
                        except Exception as e:
                            print(f"Error getting user folder creation time: {str(e)}")
                            user_creation_times.append((user, 0))  # Default timestamp
                
                # Check if there are >=2 user folders
                if len(users) >= 2:
                    # Sort users by creation time
                    sorted_users = [user for user, _ in sorted(user_creation_times, key=lambda x: x[1])]
                    
                    # Try to load paper data to get the title
                    paper_data = {}
                    try:
                        paper_data_path = os.path.join(pmid_path,'original_data','data.json')
                        if os.path.exists(paper_data_path):
                            with open(paper_data_path, 'r', encoding='utf-8') as f:
                                paper_data = json.load(f)
                    except Exception as e:
                        print(f"Error loading paper data {pmid}: {str(e)}")
                    
                    # Get the paper creation time
                    try:
                        extraction_time = os.path.getctime(pmid_path)
                    except Exception:
                        extraction_time = 0
                    
                    # Add to the paper list
                    papers.append({
                        "pmid": pmid,
                        "title": paper_data.get("title", f"Paper {pmid}"),
                        "assigned_user": sorted_users,
                        "extraction_time": datetime.fromtimestamp(extraction_time).isoformat()
                    })
        
        # Sort papers by creation time
        papers.sort(key=lambda x: x.get("extraction_time", ""))
        
        return jsonify({"papers": papers})
    except Exception as e:
        print(f"Error occurred while retrieving the list of papers needing curation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"papers": [], "error": str(e)})

@app.route('/api/curation-paper-detail', methods=['GET'])
def get_curation_paper_detail():
    """Get the details of the paper for data review"""
    try:
        pmid = request.args.get('pmid')
        if not pmid:
            return jsonify({"error": "Missing pmid parameter"}), 400
        
        print(f"Getting detailed information for paper, PMID: {pmid}")
        
        # Get the paper data path
        data_path = get_paper_data_path(pmid)
        if not os.path.exists(data_path):
            return jsonify({"error": f"Paper data not found for PMID: {pmid}"}), 404
        
        # Read paper data
        with open(data_path, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)
        
        # Extract required information
        result = {
            "pmid": pmid,
            "title": paper_data.get("title", ""),
            "abstract": paper_data.get("abstract", "")
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error occurred while getting paper detailed information: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/curation-data', methods=['GET'])
def get_curation_data():
    """Get the curation data of the paper (same and different relations)"""
    try:
        pmid = request.args.get('pmid')
        if not pmid:
            return jsonify({"error": "Missing pmid parameter"}), 400
            
        # Construct the curation data file path
        curation_data_path = os.path.join(MAIN_DIR, pmid, "curation_data.json")
        
        # Check if the file exists and is not empty
        file_exists = os.path.exists(curation_data_path)
        file_empty = False
        if file_exists:
            try:
                with open(curation_data_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    file_empty = not file_content or file_content == "{}" or file_content == "[]"
            except Exception as e:
                print(f"Error reading file: {str(e)}")
                file_empty = True
        
        # Construct User_dir path
        user_dir_path = os.path.join(MAIN_DIR, pmid, "User_dir")
        if not os.path.exists(user_dir_path):
            return jsonify({
                "same_relations": [],
                "different_relations": []
            }), 200
            
        # Get all users
        users = [d for d in os.listdir(user_dir_path) if os.path.isdir(os.path.join(user_dir_path, d))]
        total_users = len(users)
        
        # If there are no users, return empty result
        if total_users == 0:
            return jsonify({
                "same_relations": [],
                "different_relations": []
            }), 200
        
        # If the file does not exist or is empty, regenerate completely
        if not file_exists or file_empty:
            curation_data = generate_full_curation_data(pmid, users, total_users)
            save_curation_data_with_metadata(curation_data_path, curation_data, users)
            return jsonify(curation_data), 200
            
        # If the file exists and is not empty, try incremental update
        with open(curation_data_path, 'r', encoding='utf-8') as f:
            curation_data = json.load(f)
        
        # Check if an update is needed
        users_to_update = []
        
        # Check if metadata exists, create if not
        if "metadata" not in curation_data:
            curation_data["metadata"] = {
                "last_update": datetime.now().isoformat(),
                "user_data_hashes": {}
            }
        
        # Calculate the current hash value of each user's data and check for updates
        for user in users:
            current_hash = calculate_user_data_hash(pmid, user)
            stored_hash = curation_data["metadata"].get("user_data_hashes", {}).get(user, "")
            
            # User is new or data has changed
            if not stored_hash or current_hash != stored_hash:
                users_to_update.append(user)
        
        # Remove users that no longer exist
        existing_users = set(curation_data["metadata"].get("user_data_hashes", {}).keys())
        current_users = set(users)
        removed_users = existing_users - current_users
        
        for user in removed_users:
            # Remove user from metadata
            if user in curation_data["metadata"]["user_data_hashes"]:
                del curation_data["metadata"]["user_data_hashes"][user]
            # Remove user information from relations
            curation_data = remove_user_from_relations(curation_data, user)
        
        # If there are users to update, perform incremental update
        if users_to_update:
            print(f"Detected updates for users: {', '.join(users_to_update)}, updates completed")
            # Perform incremental update
            for user in users_to_update:
                # First remove all traces of that user
                curation_data = remove_user_from_relations(curation_data, user)
                
                # Add the latest relations for that user
                curation_data = add_user_relations(curation_data, pmid, user)
                
                # Update the user's hash value
                current_hash = calculate_user_data_hash(pmid, user)
                curation_data["metadata"]["user_data_hashes"][user] = current_hash
            
            # Reclassify relations
            curation_data = reclassify_relations(curation_data, total_users)
            
            # Update timestamp
            curation_data["metadata"]["last_update"] = datetime.now().isoformat()
            
            # Save the updated data
            save_curation_data_with_metadata(curation_data_path, curation_data, users)
        else:
            print("Detection complete, no updates needed")
        
        # When returning data, remove the metadata field to maintain API compatibility
        api_response = {
            "same_relations": curation_data.get("same_relations", []),
            "different_relations": curation_data.get("different_relations", [])
        }
        
        # Apply sorting to API response
        api_response = sort_relations(api_response)
        
        return jsonify(api_response), 200
        
    except Exception as e:
        print(f"Error occurred while getting curation data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Helper function: Calculate the hash value of user data
def calculate_user_data_hash(pmid, username):
    """Calculate the combined hash value of user's last_modify_output.json and notes.json"""
    import hashlib
    
    user_path = os.path.join(MAIN_DIR, pmid, "User_dir", username)
    last_modify_path = os.path.join(user_path, "last_modify_output.json")
    notes_path = os.path.join(user_path, "notes.json")
    
    hasher = hashlib.md5()
    
    # Add last_modify_output.json content to hash
    if os.path.exists(last_modify_path):
        with open(last_modify_path, 'rb') as f:
            hasher.update(f.read())
    
    # Add notes.json content to hash
    if os.path.exists(notes_path):
        with open(notes_path, 'rb') as f:
            hasher.update(f.read())
    
    return hasher.hexdigest()
# Helper function: Remove user information from relations
def remove_user_from_relations(curation_data, target_user):
    """Remove specified user's information from all relations"""
    # Merge same_relations and different_relations
    all_relations = curation_data.get("same_relations", []) + curation_data.get("different_relations", [])
    
    # Clear original lists
    curation_data["same_relations"] = []
    curation_data["different_relations"] = []
    
    for relation in all_relations:
        # If the user is in the relation's user list
        if target_user in relation["users"]:
            # Remove the target user from the user list
            relation["users"].remove(target_user)
            
            # Process note content
            if relation["note"]:
                # Parse existing notes, grouped by user
                user_notes = {}
                current_user = None
                current_note = []
                
                # Process note content line by line
                for line in relation["note"].split("\n"):
                    # If it's an empty line and there is a current user, it indicates the end of a user's note
                    if line.strip() == "" and current_user:
                        if current_user != target_user:
                            user_notes[current_user] = "\n".join(current_note)
                        current_user = None
                        current_note = []
                    # If there is no current user, this line is a username
                    elif current_user is None:
                        current_user = line.strip()
                    # Otherwise, this line is note content
                    else:
                        current_note.append(line)
                
                # Process the last note
                if current_user and current_user != target_user and current_note:
                    user_notes[current_user] = "\n".join(current_note)
                
                # Reconstruct note content, excluding the target user
                new_note = ""
                for i, (user, note) in enumerate(user_notes.items()):
                    if i > 0:
                        new_note += "\n\n"
                    new_note += f"{user}\n{note}"
                
                relation["note"] = new_note
        
        # If the relation still has users, keep it
        if relation["users"]:
            # Temporarily add to different_relations, will be reclassified later
            curation_data["different_relations"].append(relation)
    
    return curation_data

# Helper function: Add user relations
def add_user_relations(curation_data, pmid, username):
    """Add the latest relations of the user to the curation data"""
    user_dir_path = os.path.join(MAIN_DIR, pmid, "User_dir", username)
    
    # Read last_modify_output.json
    last_modify_path = os.path.join(user_dir_path, "last_modify_output.json")
    if not os.path.exists(last_modify_path):
        return curation_data
    
    with open(last_modify_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    # Read notes.json
    notes_path = os.path.join(user_dir_path, "notes.json")
    user_notes = {}
    if os.path.exists(notes_path):
        with open(notes_path, 'r', encoding='utf-8') as f:
            user_notes = json.load(f)
    
    # Create relation index
    relation_index = {}
    for relation in curation_data.get("same_relations", []) + curation_data.get("different_relations", []):
        key = create_relation_key(relation)
        relation_index[key] = relation
    
    # Process each relation of the user
    if "relations" in user_data:
        for relation in user_data["relations"]:
            # Extract relation information
            head = relation.get("head", "")
            label = relation.get("label", "")
            tail = relation.get("tail", "")
            text = relation.get("text", "")
            metaRelations = relation.get("metaRelations", [])
            
            # Build relation key
            relation_key = create_relation_key(relation)
            
            # Build note key
            note_key = f"{head}|{label}|{tail}"
            note_content = user_notes.get(note_key, "")
            
            # Check if the relation already exists
            if relation_key in relation_index:
                # Update existing relation
                existing = relation_index[relation_key]
                
                # Add user to users list
                if username not in existing["users"]:
                    existing["users"].append(username)
                
                # Update note content
                if note_content:
                    if existing["note"]:
                        existing["note"] += f"\n\n{username}\n{note_content}"
                    else:
                        existing["note"] = f"{username}\n{note_content}"
            else:
                # Create new relation
                new_relation = {
                    "head": head,
                    "label": label,
                    "tail": tail,
                    "text": text,
                    "status": "undecided",
                    "users": [username],
                    "note": f"{username}\n{note_content}" if note_content else "",
                    "metaRelations": metaRelations
                }
                
                # Add to different_relations, will be reclassified later
                curation_data["different_relations"].append(new_relation)
                
                # Update index
                relation_index[relation_key] = new_relation
    
    return curation_data

# Helper function: Create a unique key for the relation
def create_relation_key(relation):
    """Create a unique identifier key for the relation"""
    # Basic relation information
    base_key = f"{relation['head']}|{relation['label']}|{relation['tail']}"
    
    # Process metaRelations
    if "metaRelations" in relation and relation["metaRelations"]:
        # Sort and concatenate metaRelations
        meta_items = []
        for meta in relation["metaRelations"]:
            meta_items.append(f"{meta.get('target', '')}|{meta.get('label', '')}")
        
        # Sort to ensure consistency
        meta_items.sort()
        meta_key = "|".join(meta_items)
        return f"{base_key}|{meta_key}"
    
    return base_key

# Helper function: Reclassify relations
def reclassify_relations(curation_data, total_users):
    """Reclassify relations based on the number of users"""
    # Merge all relations
    all_relations = curation_data.get("same_relations", []) + curation_data.get("different_relations", [])
    
    # Clear original lists
    curation_data["same_relations"] = []
    curation_data["different_relations"] = []
    
    # Reclassify based on the number of users
    for relation in all_relations:
        if len(relation["users"]) == total_users:
            curation_data["same_relations"].append(relation)
        else:
            curation_data["different_relations"].append(relation)
    
    # Sort relations
    curation_data = sort_relations(curation_data)
    
    return curation_data

# Helper function: Sort relations
def sort_relations(curation_data):
    """Sort both same_relations and different_relations by head and tail alphabetically"""
    # Sort same_relations if it exists
    if "same_relations" in curation_data:
        curation_data["same_relations"] = sorted(
            curation_data["same_relations"], 
            key=lambda x: (x.get("head", ""), x.get("tail", ""))
        )
    
    # Sort different_relations if it exists
    if "different_relations" in curation_data:
        curation_data["different_relations"] = sorted(
            curation_data["different_relations"], 
            key=lambda x: (x.get("head", ""), x.get("tail", ""))
        )
    
    return curation_data

# Helper function: Save curation data with metadata
def save_curation_data_with_metadata(file_path, curation_data, users):
    """Save curation data and update metadata"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # If there is no metadata field, add it
    if "metadata" not in curation_data:
        curation_data["metadata"] = {
            "last_update": datetime.now().isoformat(),
            "user_data_hashes": {}
        }
    
    # Ensure all users have hash values
    for user in users:
        if user not in curation_data["metadata"]["user_data_hashes"]:
            # Calculate and save user data hash value
            curation_data["metadata"]["user_data_hashes"][user] = calculate_user_data_hash(
                os.path.dirname(file_path).split(os.path.sep)[-1],  # pmid
                user
            )
    
    # Save the file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(curation_data, f, ensure_ascii=False, indent=2)

# Helper function: Generate full curation data
def generate_full_curation_data(pmid, users, total_users):
    """Generate complete curation data"""
    # Helper function: Compare if two metaRelations lists are equal
    def are_meta_relations_equal(meta1, meta2):
        if len(meta1) != len(meta2):
            return False
            
        # Create an ordered representation containing all key-value pairs for comparison
        def get_sorted_repr(meta_list):
            meta_repr = []
            for item in meta_list:
                # Ensure the dictionary's key-value pairs are consistent
                sorted_item = {k: item.get(k, "") for k in ["label", "target"]}
                meta_repr.append(tuple(sorted(sorted_item.items())))
            return sorted(meta_repr)
            
        return get_sorted_repr(meta1) == get_sorted_repr(meta2)
    
    # Store all merged relations
    merged_relations = []
    
    # Iterate through each user's folder
    for user in users:
        user_path = os.path.join(MAIN_DIR, pmid, "User_dir", user)
        
        # Build last_modify_output.json path
        last_modify_path = os.path.join(user_path, "last_modify_output.json")
        if not os.path.exists(last_modify_path):
            continue
            
        # Read last_modify_output.json
        try:
            with open(last_modify_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except Exception as e:
            print(f"Error reading last_modify_output.json for user {user}: {str(e)}")
            continue
        
        # Build notes.json path
        notes_path = os.path.join(user_path, "notes.json")
        user_notes = {}
        if os.path.exists(notes_path):
            try:
                with open(notes_path, 'r', encoding='utf-8') as f:
                    user_notes = json.load(f)
            except Exception as e:
                print(f"Error reading notes.json for user {user}: {str(e)}")
        
        # Process user's relations
        if "relations" in user_data:
            for relation in user_data["relations"]:
                # Extract relation information
                head = relation.get("head", "")
                label = relation.get("label", "")
                tail = relation.get("tail", "")
                text = relation.get("text", "")
                metaRelations = relation.get("metaRelations", [])
                status = relation.get("status", "undecided")
                
                # Build note key
                note_key = f"{head}|{label}|{tail}"
                note_content = user_notes.get(note_key, "")
                
                # Create an enhanced relation with user information
                enhanced_relation = {
                    "head": head,
                    "label": label,
                    "tail": tail,
                    "text": text,
                    "status": status,
                    "users": [user],
                    "note": f"{user}\n{note_content}" if note_content else "",
                    "metaRelations": metaRelations
                }
                
                # Check for matching existing relations
                match_found = False
                for existing in merged_relations:
                    if (existing["head"] == head and 
                        existing["label"] == label and 
                        existing["tail"] == tail and 
                        are_meta_relations_equal(existing["metaRelations"], metaRelations)):
                        
                        # Merge users and notes
                        if user not in existing["users"]:
                            existing["users"].append(user)
                        
                        # Text field treatment logic
                        # If existing has no text but current relation has text, use current text
                        if not existing["text"] and text:
                            existing["text"] = text
                        # If both have text, keep existing one (the first one encountered)
                        
                        if note_content:
                            if existing["note"]:
                                existing["note"] += f"\n\n{user}\n{note_content}"
                            else:
                                existing["note"] = f"{user}\n{note_content}"
                        
                        match_found = True
                        break
                        
                # If no match, add as a new relation
                if not match_found:
                    merged_relations.append(enhanced_relation)
    
    # Classify relations
    same_relations = []
    different_relations = []
    
    for relation in merged_relations:
        if len(relation["users"]) == total_users:
            same_relations.append(relation)
        else:
            different_relations.append(relation)
    
    # Build result, including metadata
    from datetime import datetime
    
    curation_data = {
        "metadata": {
            "last_update": datetime.now().isoformat(),
            "user_data_hashes": {}
        },
        "same_relations": same_relations,
        "different_relations": different_relations
    }
    
    # Calculate hash values for each user's data
    for user in users:
        curation_data["metadata"]["user_data_hashes"][user] = calculate_user_data_hash(pmid, user)
    
    # Sort relations
    curation_data = sort_relations(curation_data)
    
    return curation_data

@app.route('/api/save-curation-data', methods=['POST'])
def save_curation_data():
    """Save curation data for the paper (same and different relations)"""
    try:
        data = request.get_json()
        
        if not data or 'pmid' not in data or 'data' not in data:
            return jsonify({"error": "Missing required parameters"}), 400
            
        pmid = data['pmid']
        curation_data_update = data['data']
        
        # Validate data structure
        if 'same_relations' not in curation_data_update or 'different_relations' not in curation_data_update:
            return jsonify({"error": "Invalid data structure"}), 400
            
        # Build curation data file path
        curation_data_path = os.path.join(MAIN_DIR, pmid, "curation_data.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(curation_data_path), exist_ok=True)
        
        # Read existing curation data (if it exists)
        existing_curation_data = {}
        if os.path.exists(curation_data_path):
            try:
                with open(curation_data_path, 'r', encoding='utf-8') as f:
                    existing_curation_data = json.load(f)
            except Exception as e:
                print(f"Error reading existing curation data: {str(e)}")
                # If reading fails, use an empty object
                existing_curation_data = {}
        
        # Directly update relation data without filtering any status
        existing_curation_data['same_relations'] = curation_data_update['same_relations']
        existing_curation_data['different_relations'] = curation_data_update['different_relations']
        
        # Sort relations
        existing_curation_data = sort_relations(existing_curation_data)
        
        # Update last modified time (if metadata exists)
        if 'metadata' in existing_curation_data:
            existing_curation_data['metadata']['last_update'] = datetime.now().isoformat()
        
        # Save updated data to file
        with open(curation_data_path, 'w', encoding='utf-8') as f:
            json.dump(existing_curation_data, f, indent=2, ensure_ascii=False)
            
        return jsonify({
            "success": True, 
            "message": "Curation data saved successfully",
            "total_relations": len(curation_data_update['same_relations']) + len(curation_data_update['different_relations'])
        })
        
    except Exception as e:
        print(f"Error saving curation data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph/save', methods=['POST', 'OPTIONS'])
def save_graph():
    """Save graph data and write to the corresponding file"""
    try:
        # Handle OPTIONS preflight request
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            return response
        
        # Get graph data from the request
        graph_data = request.json
        
        # Print received data to console
        print("=== Received Graph Data ===")
        print(f"Number of nodes: {len(graph_data.get('nodes', []))}")
        print(f"Number of relations: {len(graph_data.get('relations', []))}")
        print("=== Graph Data Content ===")
        print(json.dumps(graph_data, indent=2, ensure_ascii=False))
        print("=== End of Graph Data ===")
        
        # Extract key parameters
        pmid = graph_data.get('pmid')
        username = graph_data.get('username')
        mode = graph_data.get('mode', 'view')
        target_user = graph_data.get('target_user', username)
        
        # Only extract relations field
        relations = graph_data.get('relations', [])
        
        # Determine save path
        if mode == 'temp':
            # Temporary mode: save to temporary directory
            save_path = get_temp_data_path(username, pmid)
        else:
            # Ensure the current user has permission to save
            if username != target_user:
                return jsonify({
                    "success": False,
                    "message": "Permission denied: You are not allowed to edit this graph."
                }), 403
            save_path = get_user_data_path_in_main(username, pmid)
        
        # Ensure directory exists
        ensure_directory_exists(save_path)
        
        # Read existing file (if it exists)
        output_file = os.path.join(save_path, 'last_modify_output.json')
        existing_data = {}
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Unable to read existing file: {str(e)}")
                # If the file is corrupted, use an empty object
                existing_data = {}
        
        print(f"old_relations: {existing_data['relations']}")
        print(f"new_relations: {relations}")

        # Only update relations field, keeping other fields unchanged
        existing_data['relations'] = relations
        
        # Save updated file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved relations data to: {output_file}")
        
        # Add CORS headers
        response = jsonify({"success": True, "message": "Graph data received successfully"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    except Exception as e:
        print(f"Error processing graph data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/merge-curation-data', methods=['POST'])
def merge_curation_data():
    """Merge reviewed curation data into the original data, overwrite the relations field in original_output.json and notes.json, and delete User_dir"""
    try:
        import shutil  # Import shutil for file operations
        data = request.get_json()
        
        if not data or 'pmid' not in data:
            return jsonify({"error": "Missing pmid parameter"}), 400
            
        pmid = data['pmid']
        print(f"Received merge request, PMID: {pmid}")  # Add print statement
        
        # Build curation data file path
        curation_data_path = os.path.join(MAIN_DIR, pmid, "curation_data.json")
        
        # Check if the file exists
        if not os.path.exists(curation_data_path):
            return jsonify({"error": "Curation data not found"}), 404
            
        # Read curation data
        with open(curation_data_path, 'r', encoding='utf-8') as f:
            curation_data = json.load(f)
            
        # Get accepted relations
        accepted_relations = []
        paper_notes = {}
        
        # Process accepted relations in same_relations
        if 'same_relations' in curation_data:
            for relation in curation_data['same_relations']:
                if relation.get('status') == 'accept':
                    accepted_relations.append({
                        'head': relation['head'],
                        'tail': relation['tail'],
                        'label': relation['label'],
                        'text': relation.get('text', '')
                    })
                    
                    # Save note information to paper_notes
                    if 'note' in relation and relation['note']:
                        relation_key = f"{relation['head']}|{relation['label']}|{relation['tail']}"
                        paper_notes[relation_key] = relation['note']
        
        # Process accepted relations in different_relations
        if 'different_relations' in curation_data:
            for relation in curation_data['different_relations']:
                if relation.get('status') == 'accept':
                    accepted_relations.append({
                        'head': relation['head'],
                        'tail': relation['tail'],
                        'label': relation['label'],
                        'text': relation.get('text', '')
                    })
                    
                    # Save note information to paper_notes
                    if 'note' in relation and relation['note']:
                        relation_key = f"{relation['head']}|{relation['label']}|{relation['tail']}"
                        paper_notes[relation_key] = relation['note']
        
        # Build original_data folder path
        original_data_dir = os.path.join(MAIN_DIR, pmid, "original_data")
        
        # 1. Backup and update relations field in original_output.json
        original_output_path = os.path.join(original_data_dir, "original_output.json")
        old_original_output_path = os.path.join(original_data_dir, "old_original_output.json")
        
        if os.path.exists(original_output_path):
            # Remove old backup if exists
            if os.path.exists(old_original_output_path):
                os.remove(old_original_output_path)
                print(f"Removed existing old_original_output.json, path: {old_original_output_path}")
                
            # Create backup
            shutil.copy2(original_output_path, old_original_output_path)
            print(f"Created backup of original_output.json as old_original_output.json, path: {old_original_output_path}")
            
            # Read and update the file
            with open(original_output_path, 'r', encoding='utf-8') as f:
                original_output = json.load(f)
            
            # Update relations field
            original_output['relations'] = accepted_relations
            
            # Save updated original_output.json
            with open(original_output_path, 'w', encoding='utf-8') as f:
                json.dump(original_output, f, indent=2, ensure_ascii=False)
            print(f"Successfully updated relations field in original_output.json, path: {original_output_path}")
        else:
            return jsonify({"error": "original_output.json not found"}), 404
        
        # 2. Backup and update notes.json
        note_path = os.path.join(original_data_dir, "notes.json")
        old_note_path = os.path.join(original_data_dir, "old_notes.json")
        
        # Remove old backup if exists
        if os.path.exists(old_note_path):
            os.remove(old_note_path)
            print(f"Removed existing old_notes.json, path: {old_note_path}")
            
        # Create backup if original exists
        if os.path.exists(note_path):
            shutil.copy2(note_path, old_note_path)
            print(f"Created backup of notes.json as old_notes.json, path: {old_note_path}")
        
        # Write new notes.json
        with open(note_path, 'w', encoding='utf-8') as f:
            json.dump(paper_notes, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated notes.json, path: {note_path}")
        
        # 3. Add curation_merge_time field in data.json
        data_path = os.path.join(original_data_dir, "data.json")
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # Add current UTC time
            import datetime
            paper_data['curation_merge_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Save updated data.json
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully added curation_merge_time field in data.json, path: {data_path}")
            
            # Add curation_merge_time field in statistic.json
            try:
                # Read existing statistic.json
                statistics = load_statistics()
                
                # Ensure the dictionary for pmid exists
                if pmid not in statistics:
                    statistics[pmid] = {}
                
                # Add curation_merge_time field, using the same timestamp
                statistics[pmid]['curation_merge_time'] = paper_data['curation_merge_time']
                
                # Save updated statistic.json
                save_statistics(statistics)
                print(f"Successfully added curation_merge_time field in statistic.json")
                
            except Exception as e:
                print(f"Error adding curation_merge_time in statistic.json: {str(e)}")
                # Do not interrupt the process, continue with subsequent steps
        else:
            return jsonify({"error": "data.json not found"}), 404
        
        # 4. Backup User_dir folder and then delete it
        user_dir_path = os.path.join(MAIN_DIR, pmid, "User_dir")
        old_user_dir_path = os.path.join(MAIN_DIR, pmid, "old_User_dir")
        
        if os.path.exists(user_dir_path):
            # Remove old backup if exists
            if os.path.exists(old_user_dir_path):
                shutil.rmtree(old_user_dir_path)
                print(f"Removed existing old_User_dir folder, path: {old_user_dir_path}")
                
            # Create backup
            shutil.copytree(user_dir_path, old_user_dir_path)
            print(f"Created backup of User_dir as old_User_dir, path: {old_user_dir_path}")
            
            # Delete original User_dir folder
            shutil.rmtree(user_dir_path)
            print(f"Successfully deleted User_dir folder, path: {user_dir_path}")
            
        return jsonify({
            "success": True, 
            "message": "Curation data successfully merged to original data, User_dir backed up and removed, and timestamp added",
            "accepted_count": len(accepted_relations),
            "notes_count": len(paper_notes)
        })
        
    except Exception as e:
        print(f"Error merging data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/curated-papers', methods=['GET'])
def get_curated_papers():
    """Get the list of papers that have completed curation"""
    try:
        papers = []
        
        # Load statistics data
        statistics = load_statistics()
        
        # Iterate through all paper folders under Main_dir
        for pmid in os.listdir(MAIN_DIR):
            # Check if the paper has completed curation
            if pmid in statistics and 'curation_merge_time' in statistics[pmid]:
                paper_path = os.path.join(MAIN_DIR, pmid)
                
                # Read paper data
                data_file = os.path.join(paper_path, 'original_data', 'data.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r', encoding='utf-8') as f:
                        paper_data = json.load(f)
                        
                    # Construct paper information
                    paper_info = {
                        'pmid': pmid,
                        'title': paper_data.get('title', ''),
                        'curation_time': paper_data.get('curation_merge_time', ''),
                        'extraction_time': paper_data.get('extraction_time', '')
                    }
                    papers.append(paper_info)
        
        # Sort by curation completion time
        papers.sort(key=lambda x: x.get('curation_time', ''), reverse=True)
        
        return jsonify({"papers": papers})
        
    except Exception as e:
        print(f"Error getting the list of curated papers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"papers": [], "error": str(e)})

# Add new helper functions
def get_user_access_file_path():
    # 使用相对于应用根目录的路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'data')
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, 'user_access.json')

def ensure_user_access_file():
    file_path = get_user_access_file_path()
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

def load_user_access():
    ensure_user_access_file()
    with open(get_user_access_file_path(), 'r', encoding='utf-8') as f:
        return json.load(f)

def save_user_access(data):
    with open(get_user_access_file_path(), 'w', encoding='utf-8') as f:
        json.dump(data, ensure_ascii=False, indent=4, fp=f)

# Add new API endpoints
@app.route('/api/user-access', methods=['GET'])
def get_user_access():
    """Get user access data for all papers"""
    try:
        access_data = load_user_access()
        return jsonify(access_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-access', methods=['POST'])
def update_user_access():
    """Update user access for a paper"""
    try:
        data = request.get_json()
        pmid = data.get('pmid')
        access_users = data.get('access_users', [])
        
        if not pmid:
            return jsonify({"error": "PMID is required"}), 400
            
        # Load existing data
        access_data = load_user_access()
        
        # Update data - if access_users is empty, remove the pmid entry
        if access_users:
            access_data[pmid] = {
                "access_users": access_users
            }
        else:
            # Remove the pmid entry if it exists
            if pmid in access_data:
                del access_data[pmid]
        
        # Save back to file
        save_user_access(access_data)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset-curation', methods=['POST'])
def reset_curation():
    """Reset a paper to its pre-merge state by restoring from backups"""
    try:
        import shutil
        import os
        data = request.get_json()
        
        if not data or 'pmid' not in data:
            return jsonify({"error": "Missing pmid parameter"}), 400
            
        pmid = data['pmid']
        print(f"Received reset curation request, PMID: {pmid}")
        
        # 1. 处理original_data文件夹中的文件
        original_data_dir = os.path.join(MAIN_DIR, pmid, "original_data")
        
        # 检查文件夹是否存在
        if not os.path.exists(original_data_dir):
            return jsonify({"error": f"Original data directory not found for PMID: {pmid}"}), 404
        
        # 1.1 处理original_output.json文件
        original_output_path = os.path.join(original_data_dir, "original_output.json")
        old_original_output_path = os.path.join(original_data_dir, "old_original_output.json")
        
        if os.path.exists(old_original_output_path):
            # 删除当前的original_output.json
            if os.path.exists(original_output_path):
                os.remove(original_output_path)
                print(f"Removed current original_output.json, path: {original_output_path}")
            
            # 将old_original_output.json重命名为original_output.json
            os.rename(old_original_output_path, original_output_path)
            print(f"Restored original_output.json from backup, path: {original_output_path}")
        else:
            print(f"Warning: Backup file old_original_output.json not found, path: {old_original_output_path}")
        
        # 1.2 处理notes.json文件
        notes_path = os.path.join(original_data_dir, "notes.json")
        old_notes_path = os.path.join(original_data_dir, "old_notes.json")
        
        if os.path.exists(old_notes_path):
            # 删除当前的notes.json
            if os.path.exists(notes_path):
                os.remove(notes_path)
                print(f"Removed current notes.json, path: {notes_path}")
            
            # 将old_notes.json重命名为notes.json
            os.rename(old_notes_path, notes_path)
            print(f"Restored notes.json from backup, path: {notes_path}")
        else:
            print(f"Warning: Backup file old_notes.json not found, path: {old_notes_path}")
        
        # 2.1 从data.json中删除curation_merge_time字段
        data_path = os.path.join(original_data_dir, "data.json")
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                paper_data = json.load(f)
            
            # 删除curation_merge_time字段（如果存在）
            if 'curation_merge_time' in paper_data:
                del paper_data['curation_merge_time']
                print(f"Removed curation_merge_time field from data.json")
                
                # 保存修改后的data.json
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(paper_data, f, indent=2, ensure_ascii=False)
                print(f"Saved updated data.json, path: {data_path}")
        else:
            print(f"Warning: data.json not found, path: {data_path}")
        
        # 2.2 从statistic.json中删除对应pmid的curation_merge_time字段
        try:
            # 读取现有的statistic.json
            statistics = load_statistics()
            
            # 删除对应pmid的curation_merge_time字段（如果存在）
            if pmid in statistics and 'curation_merge_time' in statistics[pmid]:
                del statistics[pmid]['curation_merge_time']
                print(f"Removed curation_merge_time field for PMID {pmid} from statistic.json")
                
                # 保存更新后的statistic.json
                save_statistics(statistics)
                print(f"Saved updated statistic.json")
        except Exception as e:
            print(f"Error updating statistic.json: {str(e)}")
        
        # 3. 处理User_dir文件夹
        user_dir_path = os.path.join(MAIN_DIR, pmid, "User_dir")
        old_user_dir_path = os.path.join(MAIN_DIR, pmid, "old_User_dir")
        
        if os.path.exists(old_user_dir_path):
            # 删除当前的User_dir文件夹（如果存在）
            if os.path.exists(user_dir_path):
                shutil.rmtree(user_dir_path)
                print(f"Removed current User_dir folder, path: {user_dir_path}")
            
            # 将old_User_dir重命名为User_dir
            os.rename(old_user_dir_path, user_dir_path)
            print(f"Restored User_dir folder from backup, path: {user_dir_path}")
        else:
            print(f"Warning: Backup folder old_User_dir not found, path: {old_user_dir_path}")
        
        return jsonify({
            "success": True, 
            "message": f"Successfully reset paper {pmid} to pre-merge state"
        })
        
    except Exception as e:
        print(f"Error processing reset curation request: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 添加知识库相关API端点

@app.route('/api/knowledge-base/nodes', methods=['GET'])
def get_nodes_data():
    """获取当前知识库中的节点数据"""
    try:
        # 使用绝对路径从数据文件中读取数据
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'nodes_relations_database.json')
        print(f"Attempting to read nodes data from: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Warning: Knowledge base file not found at {file_path}")
            # 尝试使用用户提供的绝对路径
            file_path = '/home/ec2-user/work/temp_fix_folder/data/nodes_relations_database.json'
            print(f"Trying alternative path: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"Error: Knowledge base file also not found at alternative path")
                return jsonify({"error": "Knowledge base file not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({"nodes": data.get("nodes", [])})
    except Exception as e:
        print(f"Error fetching nodes data: {str(e)}")
        return jsonify({"error": f"Failed to fetch nodes data: {str(e)}"}), 500

@app.route('/api/knowledge-base/relations', methods=['GET'])
def get_relations_data():
    """获取当前知识库中的关系数据"""
    try:
        # 使用绝对路径从数据文件中读取数据
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'nodes_relations_database.json')
        print(f"Attempting to read relations data from: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Warning: Knowledge base file not found at {file_path}")
            # 尝试使用用户提供的绝对路径
            file_path = '/home/ec2-user/work/temp_fix_folder/data/nodes_relations_database.json'
            print(f"Trying alternative path: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"Error: Knowledge base file also not found at alternative path")
                return jsonify({"error": "Knowledge base file not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({"relations": data.get("relations", [])})
    except Exception as e:
        print(f"Error fetching relations data: {str(e)}")
        return jsonify({"error": f"Failed to fetch relations data: {str(e)}"}), 500

@app.route('/api/upload-knowledge-base', methods=['POST'])
def upload_knowledge_base():
    """处理上传的知识库JSON文件，追加不存在的数据项"""
    try:
        # 检查请求中是否包含文件
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['file']
        data_type = request.form.get('type', 'node')
        
        # 检查文件是否为空
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # 检查文件类型
        if not file.filename.endswith('.json'):
            return jsonify({"error": "File must be a JSON file"}), 400
        
        # 确定知识库文件路径
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'nodes_relations_database.json')
        
        if not os.path.exists(os.path.dirname(file_path)):
            print(f"Warning: Directory does not exist: {os.path.dirname(file_path)}")
            # 尝试使用用户提供的绝对路径
            file_path = '/home/ec2-user/work/temp_fix_folder/data/nodes_relations_database.json'
            print(f"Using alternative path: {file_path}")
            
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                print(f"Created directory: {os.path.dirname(file_path)}")
        
        # 读取上传的JSON文件内容
        try:
            uploaded_data = json.loads(file.read().decode('utf-8'))
            print(f"Received {data_type} knowledge base data: {json.dumps(uploaded_data, indent=2)}")
            
            # 读取当前知识库数据
            current_data = {}
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_data = json.load(f)
                except:
                    print(f"Could not read existing knowledge base file, creating a new one")
                    current_data = {"nodes": [], "relations": []}
            else:
                current_data = {"nodes": [], "relations": []}
            
            # 准备追加数据变量
            added_items = 0
            existed_items = 0
            
            # 根据类型追加数据
            if data_type == 'node' and 'nodes' in uploaded_data:
                # 确保 current_data 中有 nodes 键
                if 'nodes' not in current_data:
                    current_data['nodes'] = []
                
                # 追加不存在的节点
                for node in uploaded_data['nodes']:
                    if node not in current_data['nodes']:
                        current_data['nodes'].append(node)
                        added_items += 1
                    else:
                        existed_items += 1
                
                print(f"Added {added_items} new nodes, {existed_items} nodes already existed")
                
            elif data_type == 'relation' and 'relations' in uploaded_data:
                # 确保 current_data 中有 relations 键
                if 'relations' not in current_data:
                    current_data['relations'] = []
                
                # 追加不存在的关系
                for relation in uploaded_data['relations']:
                    if relation not in current_data['relations']:
                        current_data['relations'].append(relation)
                        added_items += 1
                    else:
                        existed_items += 1
                
                print(f"Added {added_items} new relations, {existed_items} relations already existed")
                
            else:
                return jsonify({"error": f"Invalid data format. Expected '{data_type}' key in the JSON file"}), 400
            
            # 保存更新后的数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2)
            
            print(f"Knowledge base data saved to {file_path}")
            return jsonify({
                "success": True, 
                "message": f"Added {added_items} new {data_type}s to knowledge base ({existed_items} already existed)",
                "added": added_items,
                "existed": existed_items,
                "total": len(current_data['nodes' if data_type == 'node' else 'relations'])
            })
            
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
        
    except Exception as e:
        print(f"Error uploading knowledge base: {str(e)}")
        return jsonify({"error": f"Failed to process upload: {str(e)}"}), 500
    
# Start the application
if __name__ == '__main__':
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('VITE_BACKEND_PORT')),
        debug=True
    ) 