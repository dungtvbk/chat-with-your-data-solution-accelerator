from typing import Optional, Type
import hashlib
from urllib.parse import urlparse
from ..azureblobstorage import AzureBlobStorageClient
from urllib.parse import quote

class SourceDocument:
    def __init__(self, content: str, source: str, id: Optional[str] = None, title: Optional[str]= None, chunk: Optional[int] = None, offset: Optional[int] = None, page_number: Optional[int] = None):
        self.id = id
        self.content = content
        self.source = source
        self.title = title
        self.chunk = chunk
        self.offset = offset
        self.page_number = page_number
        
    def __str__(self):
        return f"SourceDocument(id={self.id}, title={self.title}, source={self.source}, chunk={self.chunk}, offset={self.offset}, page_number={self.page_number})"
    
    @classmethod
    def from_metadata(
        cls: Type['SourceDocument'],
        content: str,
        document_url: str,
        idx: int,
        metadata: dict,
    ) -> 'SourceDocument':   
        parsed_url = urlparse(document_url)
        file_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
        filename = parsed_url.path
        hash_key = hashlib.sha1(f"{file_url}_{idx}".encode("utf-8")).hexdigest()
        hash_key = f"doc_{hash_key}"
        sas_placeholder = "_SAS_TOKEN_PLACEHOLDER_" if 'blob.core.windows.net' in parsed_url.netloc else ""
        return cls(
            id = hash_key,
            content = content,
            source = f"{file_url}{sas_placeholder}",
            title = filename,
            chunk = idx,
            offset = metadata.get('offset'),
            page_number = metadata.get('page_number'),
        )
    
    def convert_to_langchain_document(self):
        from langchain.docstore.document import Document
        return Document(
            page_content=self.content,
            metadata={
                "id": self.id,
                "source": self.source,
                "title": self.title,
                "chunk": self.chunk,
                "offset": self.offset,
                "page_number": self.page_number,
            }
        )
        
    def get_filename(self, include_path=False):
        filename = self.source.replace('_SAS_TOKEN_PLACEHOLDER_', '').replace('http://', '')
        if include_path:
            filename = filename.split('/')[-1]
        else:
            filename = filename.split('/')[-1].split('.')[0]
        return filename
    
    def get_markdown_url(self):
        url = quote(self.source, safe=':/')
        if '_SAS_TOKEN_PLACEHOLDER_' in url:
            blob_client = AzureBlobStorageClient()
            container_sas = blob_client.get_container_sas()
            url = url.replace("_SAS_TOKEN_PLACEHOLDER_", container_sas)
        return f"[{self.title}]({url})"
        
