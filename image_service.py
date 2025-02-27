# itegration with Cloudinary, image processing, upload images to the cloudinary
import cloudinary
import cloudinary.uploader

from typing import List, Optional
from fastapi import HTTPException, File, UploadFile, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Image, User
from app.services.security.auth_service import auth_serv
from app.database.connection import  get_conn_db
from app.config import settings


cloudinary.config(
    cloud_name=settings.CLD_NAME, 
    api_key=settings.CLD_API_KEY,   
    api_secret=settings.CLD_API_SECRET  
)

async def upload_image(description: str,
                      file: UploadFile = File(...),
                      tags: Optional[List[str]] = Query([]),
                      db: AsyncSession = Depends(get_conn_db),
                      current_user: User = Depends(auth_serv.get_current_user)
                      ) -> dict:

    if len(tags) > 5:
        raise HTTPException(status_code=400, detail="You can only add up to 5 tags.")
    
    # download image cloud cloudinary
    try:
        result = cloudinary.uploader.upload(file.file, folder=current_user.email)
        secure_url = result["secure_url"]
        #public_id = result["public_id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error uploading file to Cloudinary: " + str(e))

    # create new post/image in DB
    db_file = Image(image_url=secure_url,
                    description=description,
                    user_id="current_user.id",
                    #public_id=public_id
                    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return {
        "url": secure_url,
        "description": db_file.description,
        "user_id": db_file.user_id
    }

