from nicegui import ui
from loguru import logger

class UserService:
    def __init__(self) -> None:
        self._user_longitude = None
        self._user_latitude = None

    async def user_longitude(self):
        if self._user_longitude is None:
            await self._get_user_location()
        return self._user_longitude
    
    async def user_latitude(self):
        if self._user_latitude is None:
            await self._get_user_location()
        return self._user_latitude

    async def _get_user_location(self):
        try:
            response = await ui.run_javascript('''
                return await new Promise((resolve, reject) => {
                    if (!navigator.geolocation) {
                        reject(new Error('Geolocation is not supported by your browser'));
                    } else {
                        navigator.geolocation.getCurrentPosition(
                            (position) => {
                                resolve({
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                });
                            },
                            () => {
                                reject(new Error('Unable to retrieve your location'));
                            }
                        );
                    }
                });
            ''', timeout=10.0)
            logger.info(f"User location: {response}")
            self._user_latitude = response['latitude']
            self._user_longitude = response['longitude']
            return None
        #TODO: Add a more specific error message
        except Exception as e:
            logger.error(f"Error getting user location: {e}")
            return None
