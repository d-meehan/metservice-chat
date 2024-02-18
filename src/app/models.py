from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from ..app.utils.constants import METSERVICE_VARIABLES

class ModelResponseToWeatherQuery(BaseModel):
    """Request model for weather queries."""
    response: str = Field(..., title='Response', description='Response from WeatherBot to the user query')
    weather_query_check: bool = Field(..., title='Weather query check', description='Is the user message a weather query?')
    sufficient_data_check: bool = Field(..., title='Sufficient data check', description='Does the data_store contain sufficient data to answer the query?')
    data_check_rationale: str = Field(..., title='Data check rationale', description='Reason for the result you have given for the sufficient_data_check')
    location: str
    variables: List[METSERVICE_VARIABLES] = Field(
        default_factory=list, title='Variables', description='List of weather variables allowed for the API call')
    start_time: datetime = Field(..., title='Start Time',
                                 description='The first time to request data for, formatted as %Y-%m-%dT%H:00:00Z')
    end_time: datetime = Field(..., title='End Time',
                               description='The last time to request data for, formatted as %Y-%m-%dT%H:00:00Z')
    interval: Literal['h', 'd'] = Field(..., title='Time interval',
                                        description='Time interval for the data, h = hour, d = day.')

    model_config = ConfigDict(arbritary_types_allowed=True)

class MetservicePointTimeRequest(BaseModel):
    """Required criteria for Metservice API call."""
    latitude: float
    longitude: float
    variables: List[str]
    from_datetime: str = Field(..., title='Start time',
        description='Start time for the data. formatted as %Y-%m-%dT%H:00:00Z')
    interval: Optional[str] = Field(
        None, title='Time interval', description='Time interval for the data. \
            For example, "1h" for hourly data, "3h" for 3 hour intervals etc.')
    repeat: Optional[int] = Field(None, title='Number of intervals',
        description='Number of instances to request the data for. \
            For example, if interval is "1h", "3" will request 3 hours of data.')

    model_config = ConfigDict(arbritary_types_allowed=True)

class Message(BaseModel):
    """Model for messages in GPT messages."""
    role: str
    content: str
    stamp: str
    avatar: str
    sent: bool

class MetserviceVariable(BaseModel):
    """Model for variable response in Metservice API."""
    name: str
    value: float = Field(..., title='Value', description='Value of the variable')
    units: str = Field(..., title='Units', description='Units of the variable')

class MetserviceTimePointSummary(BaseModel):
    """Model for time point summary in Metservice API."""
    time: str
    latitude: float
    longitude: float
    location: Optional[str] = None
    variables: List[MetserviceVariable]
