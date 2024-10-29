import pickle
import os
from typing import Dict, Optional
import streamlit as st

class DocumentStore:
    def __init__(self, storage_path: str = "data/documents.pkl"):
        self.storage_path = storage_path
        self.documents = self._load_documents()
        
    def _load_documents(self) -> Dict:
        """从本地加载文档"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                st.error(f"加载文档时出错: {str(e)}")
                return {}
        return {}
    
    def save_documents(self, documents: Dict) -> bool:
        """保存文档到本地"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'wb') as f:
                pickle.dump(documents, f)
            return True
        except Exception as e:
            st.error(f"保存文档时出错: {str(e)}")
            return False
    
    def get_all_documents(self) -> Dict:
        """获取所有保存的文档"""
        return self.documents
    
    def add_document(self, patient_name: str, content: str) -> bool:
        """添加新文档"""
        try:
            self.documents[patient_name] = content
            return self.save_documents(self.documents)
        except Exception as e:
            st.error(f"添加文档时出错: {str(e)}")
            return False
    
    def remove_document(self, patient_name: str) -> bool:
        """删除文档"""
        try:
            if patient_name in self.documents:
                del self.documents[patient_name]
                return self.save_documents(self.documents)
            return False
        except Exception as e:
            st.error(f"删除文档时出错: {str(e)}")
            return False 