from fastapi import UploadFile, HTTPException, status
from app.core.storage import PublicMediaStorage
from typing import Optional, List, BinaryIO
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
IMAGE_CONTENT_TYPES = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 
    'image/svg+xml', 'image/svg'
]

MODEL_3D_EXTENSIONS = ['glb', 'gltf', 'obj', 'fbx', 'stl']
MODEL_3D_CONTENT_TYPES = [
    'model/gltf-binary', 'model/gltf+json', 'application/octet-stream',
    'application/x-tgif', 'model/obj', 'model/stl'
]

AR_EXTENSIONS = ['usdz', 'reality', 'arwt']
AR_CONTENT_TYPES = [
    'model/vnd.usdz+zip', 'application/octet-stream',
    'model/vnd.pixar.usd', 'application/vnd.apple.reality'
]

async def read_upload_file(file: UploadFile) -> BinaryIO:
    try:
        content = await file.read()
        return BytesIO(content)
    except Exception as e:
        logger.error(f"Error reading uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )

async def upload_product_file(file: UploadFile, product_id: int, file_type: str) -> str:
    if file is None:
        return None
        
    try:
        file_obj = await read_upload_file(file)
        
        allowed_extensions = None
        allowed_content_types = None
        
        if file_type == 'images':
            allowed_extensions = IMAGE_EXTENSIONS
            allowed_content_types = IMAGE_CONTENT_TYPES
            custom_path = f"products/{product_id}/images"
        elif file_type in ['models', '3d']:
            allowed_extensions = MODEL_3D_EXTENSIONS
            allowed_content_types = MODEL_3D_CONTENT_TYPES
            custom_path = f"products/{product_id}/models"
        elif file_type == 'ar':
            allowed_extensions = AR_EXTENSIONS
            allowed_content_types = AR_CONTENT_TYPES
            custom_path = f"products/{product_id}/ar"
        else:
            custom_path = f"products/{product_id}/{file_type}"
        
        storage = PublicMediaStorage(custom_path=custom_path)
        
        url = storage.save(
            file_obj, 
            name=file.filename, 
            content_type=file.content_type,
            allowed_extensions=allowed_extensions,
            allowed_content_types=allowed_content_types
        )
        
        return url
    except ValueError as e:
        logger.error(f"Validation error when uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

async def upload_product_image(file: UploadFile, product_id: int) -> str:
    return await upload_product_file(file, product_id, 'images')

async def upload_product_model_3d(file: UploadFile, product_id: int) -> str:
    return await upload_product_file(file, product_id, 'models')

async def upload_ar_file(file: UploadFile, product_id: int) -> str:
    return await upload_product_file(file, product_id, 'ar')