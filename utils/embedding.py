from typing import List, Dict, Any, Tuple
import re
import numpy as np
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

class PatientDocumentManager:
    def __init__(self):
        self.patient_docs = {}  # 存储患者名称和对应的文档内容
        self.symptom_patterns = {
            "头晕": ["头晕", "眩晕", "晕厥"],
            "过敏": ["过敏", "海鲜过敏", "食物过敏"],
            "白细胞": ["白细胞", "WBC"]
            # 可以添加更多症状模式
        }

    def add_document(self, filename: str, content: str):
        """添加文档并关联到患者"""
        # 从文件名提取患者姓名
        patient_name = filename.split('.')[0]
        self.patient_docs[patient_name] = content

    def get_patient_content(self, patient_name: str) -> str:
        """获取指定患者的文档内容"""
        return self.patient_docs.get(patient_name, "")

    def search_by_symptom(self, symptom: str) -> List[Tuple[str, str]]:
        """根据症状搜索患者"""
        matching_patients = []
        patterns = self.symptom_patterns.get(symptom, [symptom])
        
        for patient, content in self.patient_docs.items():
            for pattern in patterns:
                if pattern in content:
                    matching_patients.append((patient, content))
                    break
        
        return matching_patients

def get_llm_response(query: str, patient_docs: PatientDocumentManager) -> Tuple[str, List[Tuple[str, str]]]:
    """根据查询类型生成回答，同时返回引用的文档"""
    try:
        referenced_docs = []  # 存储引用的文档
        
        # 1. 处理指定患者的查询
        patient_match = re.search(r'[患者]*(\w+某某)', query)
        if patient_match:
            patient_name = patient_match.group(1)
            content = patient_docs.get_patient_content(patient_name)
            if not content:
                return f"未找到{patient_name}的病历记录。", []
            
            # 添加到引用文档
            referenced_docs.append((f"{patient_name}.pdf", content))
            
            # 构建提示词
            if "住院期间的情况" in query or "住院期间" in query:
                prompt = f"""请分析以下病历，总结{patient_name}住院期间的整体情况：
                1. 入院时的主要症状和诊断
                2. 住院期间的治疗过程
                3. 出院时的情况和效果
                
                病历内容：
                {content}
                """
            elif "诊断符合率" in query:
                prompt = f"""请分析以下病历，对比{patient_name}的入院诊断和出院诊断：
                1. 列出入院诊断和出院诊断
                2. 分析两者的符合程度
                3. 给出具体的符合率数值
                
                病历内容：
                {content}
                """
            elif "出院时情况" in query or "好转" in query:
                prompt = f"""请分析以下病历，详细说明{patient_name}出院时的情况：
                1. 症状改善情况
                2. 治疗效果
                3. 是否有未解决的问题
                
                病历内容：
                {content}
                """
            elif "白细胞数值" in query:
                prompt = f"""请从以下病历中提取{patient_name}的白细胞检验结果：
                1. 入院时的白细胞值
                2. 复查时的白细胞值
                3. 对比两次结果的变化
                
                病历内容：
                {content}
                """
            else:
                # 处理一般性查询
                prompt = f"""请根据以下病历回答问题：
                问题：{query}
                患者：{patient_name}
                
                病历内容：
                {content}
                
                请提供详细的分析和回答。
                """
        
        # 2. 处理症状相关的查询
        elif any(keyword in query for keyword in ["头晕症状", "海鲜过敏", "白细胞数值", "得了什么病"]):
            # 确定要搜索的症状或关键词
            if "头晕症状" in query:
                symptom = "头晕"
            elif "海鲜过敏" in query:
                symptom = "过敏"
            elif "白细胞数值" in query:
                symptom = "白细胞"
            else:
                # 处理"得了什么病"的查询
                patient_name = query.split("得了什么病")[0].strip()
                if patient_name:
                    content = patient_docs.get_patient_content(patient_name)
                    if content:
                        prompt = f"""请分析以下病历，总结{patient_name}的主要疾病和症状：
                        1. 主要诊断结果
                        2. 主要症状表现
                        3. 相关检查结果
                        
                        病历内容：
                        {content}
                        """
                        response = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {"role": "system", "content": "你是一个专业的医疗文档分析助手，请基于提供的病历内容进行分析和回答。"},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=2000
                        )
                        return response.choices[0].message.content, []
                return "请指定具体的患者姓名。", []
            
            # 搜索相关患者并添加到引用文档
            matching_patients = patient_docs.search_by_symptom(symptom)
            referenced_docs.extend([(f"{patient}.pdf", content) for patient, content in matching_patients])
            
            # 构建提示词
            prompt = f"""请分析以下患者的病历记录，回答问题：{query}

            找到的相关病历：
            """ + "\n\n".join([f"患者{patient}的记录：\n{content}" for patient, content in matching_patients])
        
        else:
            return "无法理解的查询类型，请使用以下格式提问：\n1. 询问具体患者：'患者XXX的...' \n2. 查询症状：'哪些患者有头晕症状' \n3. 查询病情：'XXX得了什么病'", []
        
        # 调用LLM生成回答
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个专业的医疗文档分析助手，请基于提供的病历内容进行分析和回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content, referenced_docs
        
    except Exception as e:
        return f"处理出错：{str(e)}", []
