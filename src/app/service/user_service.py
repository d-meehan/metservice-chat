from nicegui import ui, app
from loguru import logger

class UserService:

    @staticmethod
    async def get_user_location():
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
            return response
        #TODO: Add a more specific error message
        except Exception as e:
            logger.error(f"Error getting user location: {e}")
            return None
