import streamlit as st
from utils.embedding import PatientDocumentManager, get_llm_response
from utils.document_processor import process_documents
import pandas as pd
from typing import List, Dict
import re

st.set_page_config(page_title="医疗文档分析系统", layout="wide")

def main():
    st.title("医疗文档分析系统")
    st.write("上传病历文档并提问")
    
    # 文件上传部分
    uploaded_files = st.file_uploader("上传多个文档文件", accept_multiple_files=True)
    
    if uploaded_files:
        # 初始化患者文档管理器
        patient_docs = PatientDocumentManager()
        
        # 处理上传的文档
        with st.spinner("正在处理文档..."):
            for file in uploaded_files:
                try:
                    content = process_documents([file])[0]  # 处理单个文件并获取内容
                    patient_docs.add_document(file.name, content)
                    st.success(f"成功处理文件：{file.name}")
                except Exception as e:
                    st.error(f"处理文件 {file.name} 时出错: {str(e)}")
        
        # 显示可用的患者列表
        st.subheader("已载入的病历文档")
        for patient_name in patient_docs.patient_docs.keys():
            with st.expander(f"📄 {patient_name}"):
                st.text(patient_docs.get_patient_content(patient_name))
        
        # 用户查询输入
        query = st.text_input("请输入您的查询:")
        
        if query:
            with st.spinner("AI正在分析..."):
                try:
                    response, referenced_docs = get_llm_response(query, patient_docs)
                    
                    # 显示分析结果
                    st.subheader("分析结果")
                    st.write(response)
                    
                    # 提取分析结果中提到的患者名字
                    mentioned_patients = set()
                    for match in re.finditer(r'[蒲周刘马杨]\w{1,2}某某', response):
                        mentioned_patients.add(match.group())
                    
                    # 显示相关病历内容
                    if mentioned_patients:  # 如果在分析结果中找到了患者名字
                        st.subheader("相关病历内容")
                        for patient in mentioned_patients:
                            content = patient_docs.get_patient_content(f"{patient}.pdf")
                            if content:
                                with st.expander(f"📄 {patient} 的病历内容", expanded=True):  # 默认展开
                                    st.markdown("---")
                                    # 尝试在内容中高亮关键信息
                                    if "头晕" in query:
                                        content = content.replace("头晕", "**头晕**")
                                    elif "过敏" in query:
                                        content = content.replace("过敏", "**过敏**")
                                    st.markdown(content)
                    
                except Exception as e:
                    st.error(f"处理查询时出错: {str(e)}")

if __name__ == "__main__":
    main()
