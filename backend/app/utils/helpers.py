import uuid
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime


def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def encode_base64(data: bytes) -> str:
    """Encode bytes to base64 string"""
    return base64.b64encode(data).decode('utf-8')


def decode_base64(data: str) -> bytes:
    """Decode base64 string to bytes"""
    return base64.b64decode(data.encode('utf-8'))


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)


def safe_json_loads(data: str) -> Any:
    """Safely deserialize JSON string"""
    try:
        return json.loads(data)
    except Exception:
        return None


def validate_file_type(filename: str, allowed_extensions: list) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    return any(filename.lower().endswith(ext.lower()) for ext in allowed_extensions)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    return filename


def create_data_preview(data: Dict[str, Any], max_rows: int = 5) -> Dict[str, Any]:
    """Create a preview of data for display"""
    preview = {
        "shape": data.get("shape", (0, 0)),
        "columns": data.get("columns", []),
        "sample_data": data.get("head", [])[:max_rows],
        "data_types": data.get("dtypes", {}),
        "null_counts": data.get("null_counts", {}),
        "numeric_columns": data.get("numeric_columns", []),
        "categorical_columns": data.get("categorical_columns", [])
    }
    return preview


def extract_chart_type_from_code(code: str) -> str:
    """Extract chart type from generated code"""
    code_lower = code.lower()
    
    chart_types = {
        "line": ["plt.plot", "sns.lineplot", "px.line"],
        "bar": ["plt.bar", "sns.barplot", "px.bar"],
        "scatter": ["plt.scatter", "sns.scatterplot", "px.scatter"],
        "pie": ["plt.pie", "px.pie"],
        "histogram": ["plt.hist", "sns.histplot", "px.histogram"],
        "heatmap": ["sns.heatmap", "px.imshow"],
        "box": ["plt.boxplot", "sns.boxplot", "px.box"],
        "violin": ["sns.violinplot", "px.violin"]
    }
    
    for chart_type, keywords in chart_types.items():
        if any(keyword in code_lower for keyword in keywords):
            return chart_type
    
    return "unknown"


def create_error_response(message: str, error_code: str = "UNKNOWN_ERROR") -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    }


def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
