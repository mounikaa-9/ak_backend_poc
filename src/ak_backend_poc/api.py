from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI()
api.register_controllers(NinjaJWTDefaultController)

# Guard to prevent duplicate registration
_routers_registered = False

def register_routers():
    global _routers_registered
    if _routers_registered:
        return
    
    # Register all routers here
    api.add_router("/users", "users.api.users_router")
    api.add_router("/heatmaps", "heatmaps.api.heatmaps_router")
    api.add_router("/ai_advisory", "ai_advisory.api.ai_advisory_router")
    api.add_router("/weather", "weather.api.weather_router")
    api.add_router("/pipelines", "pipelines.new_profile_script.creation_router")
    api.add_router("/crop_loss_analytics", "crop_loss_analytics.api.crop_loss_analytics_router")
    api.add_router("/testing", "testing.testing_script.testing_router")
    api.add_router("/pipelines/sync", "pipelines.sync.sync_new_profile.sync_creation_router")

    _routers_registered = True

# Call the function
register_routers()