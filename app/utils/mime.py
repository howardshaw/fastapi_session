from app.models.resource import ResourceType

def get_resource_type_from_mime(mime_type: str) -> ResourceType:
    """
    根据 MIME 类型判断资源类型
    
    Args:
        mime_type: MIME 类型字符串 (例如: 'image/jpeg', 'application/pdf')
        
    Returns:
        ResourceType: 对应的资源类型枚举值
    """
    # 获取主类型
    main_type = mime_type.split('/')[0].lower()
    
    # 根据主类型判断资源类型
    if main_type == 'image':
        return ResourceType.IMAGE
    elif main_type == 'video':
        return ResourceType.VIDEO
    elif main_type == 'audio':
        return ResourceType.AUDIO
    elif main_type == 'text':
        return ResourceType.TEXT
    elif mime_type in ['application/pdf']:
        return ResourceType.DOCUMENT
    elif mime_type in ['application/msword',
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      'application/vnd.ms-excel',
                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      'application/vnd.ms-powerpoint',
                      'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
        return ResourceType.DOCUMENT
    
    # 默认返回其他类型
    return ResourceType.OTHER 