from ninja import NinjaAPI, Schema

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/users", "users.api.users_router")
api.add_router("/heatmaps", "heatmaps.api.heatmaps_router")
api.add_router("/ai_advisory", "ai_advisory.api.ai_advisory_router")
api.add_router("/weather", "weather.api.weather_router")
api.add_router("/pipelines", "pipelines.new_profile_script.creation_router")

@api.get("/hello", auth = JWTAuth())
def hello(request):
    # print(request)
    return {"message":"Hello World"}