from typing import List
import PyPDF2
import docx
import re
import streamlit as st
import pdfplumber
import io

def process_documents(files) -> List[str]:
    """处理上传的文档文件，支持中文PDF和Word格式"""
    documents = []
    
    for file in files:
        try:
            if file.name.lower().endswith('.pdf'):
                try:
                    # 将文件内容读入内存
                    file_bytes = io.BytesIO(file.read())
                    
                    # 使用pdfplumber处理中文PDF
                    with pdfplumber.open(file_bytes) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                        if text.strip():  # 确保提取到了文本
                            documents.append(text)
                        else:
                            st.warning(f"文件 '{file.name}' 未能提取到文本内容")
                            
                except Exception as e:
                    st.error(f"处理PDF文件 '{file.name}' 时出错: {str(e)}")
                    # 尝试使用PyPDF2作为备选方案
                    try:
                        file_bytes.seek(0)  # 重置文件指针
                        pdf_reader = PyPDF2.PdfReader(file_bytes)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                        if text.strip():
                            documents.append(text)
                        else:
                            st.warning(f"使用备选方案仍未能从文件 '{file.name}' 提取到文本内容")
                    except Exception as e2:
                        st.error(f"备选方案处理PDF文件 '{file.name}' 时也出错: {str(e2)}")
                    continue
                    
            elif file.name.lower().endswith('.docx'):
                try:
                    # 将文件内容读入内存
                    file_bytes = io.BytesIO(file.read())
                    doc = docx.Document(file_bytes)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    if text.strip():
                        documents.append(text)
                    else:
                        st.warning(f"文件 '{file.name}' 未能提取到文本内容")
                except Exception as e:
                    st.error(f"处理Word文件 '{file.name}' 时出错: {str(e)}")
                    continue
                    
            elif file.name.lower().endswith('.txt'):
                try:
                    # 读取文件内容
                    file_content = file.read()
                    # 尝试不同的编码方式
                    encodings = ['utf-8', 'gbk', 'gb2312']
                    text = None
                    
                    for encoding in encodings:
                        try:
                            if isinstance(file_content, bytes):
                                text = file_content.decode(encoding)
                            else:
                                text = file_content
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if text and text.strip():
                        documents.append(text)
                    else:
                        st.warning(f"文件 '{file.name}' 未能提取到文本内容")
                except Exception as e:
                    st.error(f"处理文本文件 '{file.name}' 时出错: {str(e)}")
                    continue
            else:
                st.warning(f"不支持的文件格式: {file.name}")
                continue
                
        except Exception as e:
            st.error(f"处理文件 '{file.name}' 时发生未知错误: {str(e)}")
            continue
    
    if not documents:
        st.warning("没有成功处理任何文档，请检查文件格式是否正确。")
    
    return documents

def chunk_documents(documents: List[str], chunk_size: int = None) -> List[str]:
    """将每个文档作为一个完整的块"""
    return documents  # 直接返回完整文档列表，不再分片
