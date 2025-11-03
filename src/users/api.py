from typing import List
from datetime import datetime
from django.db import DatabaseError
from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth.hashers import make_password

import asyncio

from integrations.farm_crud_call import add_new_farm
from integrations.get_sensed_days import get_sensed_days
from users.models import User, Farm
from users.user_schemas import CreateUser, UserSchema
from users.farm_schemas import FarmCreateSchema, FarmResponseSchema
import logging

logger = logging.getLogger(__name__)
users_router = Router(tags=["Users"])

@users_router.post("/create_new_user", response=UserSchema)
def create_user(request, payload: CreateUser):
    """Create a new user"""
    if User.objects.filter(username=payload.username).exists():
        return {"detail": "Username already exists"}, 400
    if User.objects.filter(email=payload.email).exists():
        return {"detail": "Email already registered"}, 400

    user = User.objects.create(
        username=payload.username,
        email=payload.email,
        password=make_password(payload.password)  # hash password
    )
    return user

@users_router.get("/already_registered_farm", response = FarmResponseSchema, auth=JWTAuth())
def check_if_farm(request):
    try:
        farm = Farm.objects.get(user=request.user)
    except Farm.DoesNotExist:
        raise HttpError(404, "Farm not found for this user.")
    except DatabaseError as e:
        raise HttpError(500, f"Database error: {str(e)}")

    except Exception as e:
        # Safety net for unexpected exceptions
        raise HttpError(500, f"Unexpected error: {str(e)}")
    if farm:
        return FarmResponseSchema(
            field_id=farm.field_id,
            farm_email=farm.farm_email,
            field_name=farm.field_name,
            field_area=float(farm.field_area),
            crop=farm.crop,
            sowing_date=farm.sowing_date,
            last_sensed_day=farm.last_sensed_day,
            farm_coordinates=farm.farm_coordinates,
        )
    raise HttpError(404, "Farm Not Found")

@users_router.post("/create_new_farm", response=FarmResponseSchema, auth=JWTAuth())
def create_new_farm(request, payload: FarmCreateSchema):
    """Create a new farm"""
    try:
        farm = Farm.objects.filter(user=request.user).first()
        if farm:
            return FarmResponseSchema(
                field_id=farm.field_id,
                farm_email=farm.farm_email,
                field_name=farm.field_name,
                field_area=float(farm.field_area),
                crop=farm.crop,
                sowing_date=farm.sowing_date,
                last_sensed_day=farm.last_sensed_day,
                farm_coordinates=farm.farm_coordinates,
            )
        logger.info(f"Starting farm creation for user: {request.user.username}")
        logger.info(f"Payload: {payload.dict()}")
        
        # Step 1: Call add_new_farm
        logger.info("Calling add_new_farm...")
        res = asyncio.run(add_new_farm(
            crop_name=payload.crop,
            full_name=payload.field_name,
            date=str(payload.sowing_date),
            points=payload.farm_coordinates
        ))
        
        # logger.info(f"add_new_farm response status: {res.status_code}")
        # res_json = res.json()
        res_json = res
        logger.info(f"add_new_farm response JSON: {res_json}")
        
        if "error" in res_json:
            logger.error(f"Error in add_new_farm response: {res_json['error']}")
            raise HttpError(400, "Unable to add a new farm at the current moment")
        
        # Step 2: Extract field_id
        field_id = res_json.get("FieldID") or res_json.get("field_id")
        logger.info(f"Extracted field_id: {field_id}")
        
        if not field_id:
            logger.error(f"No field_id in response. Full response: {res_json}")
            raise HttpError(400, "No field_id returned from add_new_farm")
        
        # Step 3: Get sensed days
        try:
            logger.info(f"Calling get_sensed_days with field_id: {field_id}")
            last_sensed_day_response = asyncio.run(
                get_sensed_days(field_id=field_id)
            )
            logger.info(f"get_sensed_days response: {last_sensed_day_response}")
        except Exception as e:
            logger.error(f"Error in get_sensed_days: {str(e)}", exc_info=True)
            raise HttpError(400, f"Unable to get last sensed days: {str(e)}")
        
        if "error" in last_sensed_day_response:
            last_sensed_day = None
            logger.warning("Error in last_sensed_day_response, setting to None")
        else:
            last_sensed_day = last_sensed_day_response.get("last_sensed_day")
            logger.info(f"last_sensed_day: {last_sensed_day}")
        
        # Step 4: Create farm in database
        try:
            logger.info("Creating farm in database...")
            logger.info(f"field_id to use: {field_id}")
            logger.info(f"field_area from response: {res_json.get('field_area')}")
            date_obj = datetime.strptime(str(payload.sowing_date), "%Y-%m-%d").date()
            farm = Farm.objects.create(
                user=request.user,
                farm_email=payload.farm_email,
                farm_coordinates=payload.farm_coordinates,
                field_id=field_id,  # Use the extracted field_id, not res_json["field_id"]
                field_name=payload.field_name,
                field_area=res_json["field_area"],
                crop=payload.crop,
                sowing_date=date_obj,
                last_sensed_day=last_sensed_day,
            )
            logger.info(f"Farm created successfully with ID: {farm.id}")
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise HttpError(400, f"Unable to add farm to the database: {str(e)}")
        
        # Step 5: Return response
        logger.info("Preparing response...")
        return FarmResponseSchema(
            field_id=farm.field_id,
            farm_email=farm.farm_email,
            field_name=farm.field_name,
            field_area=float(farm.field_area),
            crop=farm.crop,
            sowing_date=farm.sowing_date,
            last_sensed_day=farm.last_sensed_day,
            farm_coordinates=farm.farm_coordinates,
        )
        
    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_new_farm: {str(e)}", exc_info=True)
        raise HttpError(400, f"Unable to create a farm at the current moment: {str(e)}")