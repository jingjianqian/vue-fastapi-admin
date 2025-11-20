from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MiniprogramCreate(BaseModel):
    """爬虫提交小程序数据Schema"""
    # 必填字段
    source_id: int = Field(..., description="来源平台ID（如we123的ID）")
    name: str = Field(..., min_length=1, max_length=255, description="小程序名称")
    source_platform: str = Field(default="we123", description="来源平台")
    
    # 可选字段
    category: Optional[str] = Field(None, max_length=100, description="分类")
    description: Optional[str] = Field(None, description="小程序介绍")
    update_time_text: Optional[str] = Field(None, description="更新时间（原始文本）")
    view_count: Optional[str] = Field(None, description="查看次数")
    
    # 图片
    logo_url: Optional[str] = Field(None, alias="logo", description="Logo URL")
    logo_local_path: Optional[str] = Field(None, description="Logo本地路径")
    qrcode_url: Optional[str] = Field(None, description="详情页二维码图片URL")
    
    # 来源信息
    source_url: Optional[str] = Field(None, alias="url", description="来源URL")
    crawl_time: Optional[datetime] = Field(None, description="爬取时间")
    
    # 关联数据
    tags: List[str] = Field(default_factory=list, description="标签列表")
    screenshots: List[str] = Field(default_factory=list, description="截图URL列表")
    related_links: List[str] = Field(default_factory=list, description="关联链接列表")
    
    class Config:
        populate_by_name = True  # 允许使用别名


class MiniprogramBatchCreate(BaseModel):
    """批量提交小程序数据Schema"""
    items: List[MiniprogramCreate] = Field(..., description="小程序数据列表")


class MiniprogramResponse(BaseModel):
    """小程序数据响应Schema"""
    id: int
    source_id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    logo_url: Optional[str]
    qrcode_url: Optional[str]
    source_platform: str
    created_at: datetime
    updated_at: datetime
    
    tags: List[str] = []
    screenshots: List[dict] = []
    related_links: List[str] = []
    
    class Config:
        from_attributes = True
