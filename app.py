import streamlit as st
from utils.embedding import PatientDocumentManager, get_llm_response
from utils.document_processor import process_documents
from utils.document_store import DocumentStore
import pandas as pd
from typing import List, Dict
import re

st.set_page_config(page_title="电子病历AI问答系统", layout="wide")

def main():
    # 初始化文档存储
    doc_store = DocumentStore()
    
    # 添加实现原理说明
    st.sidebar.title("实现原理")
    st.sidebar.markdown("""
    本系统基于RAG（检索增强生成）实现智能病历分析，相比传统RAG有以下优势：
    
    1. **文档处理**：
       - 支持PDF、Word等格式的病历文档
       - 自动提取文本内容并保持格式
       - 建立患者与文档的关联关系
       - 支持本地持久化存储
    
    2. **查询处理优化**：
       - 基于患者姓名的精确查询，避免混淆不同患者信息
       - 基于预定义症状模式的语义匹配，提高召回率
       - 支持多种查询模式的智能识别，增强用户体验
    
    3. **智能分析增强**：
       - 根据不同查询类型动态生成专业提示词
       - 保持医疗术语的准确性和专业性
       - 提供结构化的分析结果
    
    4. **精准度提升**：
       - 不进行文档分块，避免上下文丢失
       - 保持病历的完整性，提高分析准确度
       - 支持跨文档的症状关联分析
    
    5. **传统RAG的局限性**：
       - 传统RAG通过文本分块可能割裂医疗信息
       - 向量相似度匹配可能忽略医学专业特性
       - 缺乏患者信息的关联性分析
    
    6. **本系统的改进**：
       - 以患者为中心的文档管理
       - 专业医疗术语的模式匹配
       - 完整病历的语义理解
       - 结构化的查询处理流程
    """)
    
    # 添加分隔线
    st.sidebar.markdown("---")
    
    # 添加侧边栏的预设问题
    st.sidebar.title("常见问题示例")
    
    # 预设问题列表
    preset_questions = [
        "患者蒲某某住院期间的情况",
        "患者蒲某某的诊断符合率是多少",
        "患者蒲某某出院时情况怎么样？",
        "患者蒲某某经过治疗出院时是否有好转，具体说出那些有好转，还有哪些问题？",
        "患者蒲某某入院检验项目白细胞数值为多少？患者复查检验项目白细胞数值为多少？",
        "请给出主诉有头晕症状的患者信息",
        "哪位患者检查白细胞数值高于3.12*10^9/L",
        "有几位患者有头晕症状？哪位患者海鲜过敏"
    ]
    
    # 直接在侧边栏显示问题列表
    for i, question in enumerate(preset_questions, 1):
        st.sidebar.markdown(f"{i}. {question}")
    
    # 主界面内容
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("电子病历AI问答系统")
        
        # 创建两个标签页：文档管理和查询分析
        tab1, tab2 = st.tabs(["文档管理", "查询分析"])
        
        with tab1:
            st.write("上传新的病历文档")
            uploaded_files = st.file_uploader("上传多个文档文件", accept_multiple_files=True)
            
            if uploaded_files:
                with st.spinner("正在处理文档..."):
                    for file in uploaded_files:
                        try:
                            content = process_documents([file])[0]
                            patient_name = file.name.split('.')[0]
                            if doc_store.add_document(patient_name, content):
                                st.success(f"成功处理并保存文件：{file.name}")
                        except Exception as e:
                            st.error(f"处理文件 {file.name} 时出错: {str(e)}")
            
            # 显示已保存的文档列表
            st.subheader("已保存的病历文档")
            saved_docs = doc_store.get_all_documents()
            for patient_name, content in saved_docs.items():
                with st.expander(f"📄 {patient_name}"):
                    st.text(content)
                    if st.button(f"删除 {patient_name}", key=f"del_{patient_name}"):
                        if doc_store.remove_document(patient_name):
                            st.success(f"成功删除 {patient_name} 的病历")
                            st.rerun()
        
        with tab2:
            # 初始化患者文档管理器
            patient_docs = PatientDocumentManager()
            # 加载保存的文档
            saved_docs = doc_store.get_all_documents()
            for patient_name, content in saved_docs.items():
                patient_docs.add_document(f"{patient_name}.pdf", content)
            
            # 用户查询输入
            query = st.text_input("请输入您的查询:")
            
            if query:
                with st.spinner("AI正在分析..."):
                    try:
                        response, referenced_docs = get_llm_response(query, patient_docs)
                        
                        # 显示分析结果
                        st.subheader("分析结果")
                        st.write(response)
                        
                        # 显示引用的文档内容
                        if referenced_docs:
                            st.subheader("相关病历内容")
                            for doc_name, content in referenced_docs:
                                patient_name = doc_name.split('.')[0]
                                with st.expander(f"📄 {patient_name} 的病历内容", expanded=False):
                                    st.markdown("---")
                                    highlighted_content = content
                                    if "头晕" in query:
                                        highlighted_content = highlighted_content.replace("头晕", "**头晕**")
                                    if "过敏" in query:
                                        highlighted_content = highlighted_content.replace("过敏", "**过敏**")
                                    if "海鲜" in query:
                                        highlighted_content = highlighted_content.replace("海鲜", "**海鲜**")
                                    st.markdown(highlighted_content)
                    except Exception as e:
                        st.error(f"处理查询时出错: {str(e)}")

    # 添加开发者信息到页面底部
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 10px;'>
            Developed by Huaiyuan Tan
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
