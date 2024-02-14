from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class GPTResponseToWeatherQuery(BaseModel):
    """Request model for weather queries."""
    response: str = Field(..., title='Response', description='Response from WeatherBot to the user query')
    weather_query_check: bool = Field(..., title='Weather query check', description='Is the user message a weather query?')
    sufficient_data_check: bool = Field(..., title='Sufficient data check', description='Does the data_store contain sufficient data to answer the query?')
    data_check_rationale: str = Field(..., title='Data check rationale', description='Reason for the result you have given for the sufficient_data_check')
    location: str
    variables: List[str]
    from_datetime: str = Field(..., title='Start time',
        description='Start time for the data. formatted as :%Y-%m-%dT00:00:00Z')
    interval: Optional[str] = Field(
        None, title='Time interval', description='Time interval for the data. \
            For example, "1h" for hourly data, "3h" for 3 hour intervals etc.')
    repeat: Optional[int] = Field(None, title='Number of intervals',
        description='Number of instances to request the data for. \
            For example, if interval is "1h", "3" will request 3 hours of data.')

    model_config = ConfigDict(arbritary_types_allowed=True)

class MetservicePointTimeRequest(BaseModel):
    """Required criteria for Metservice API call."""
    latitude: float
    longitude: float
    variables: List[str]
    from_datetime: str = Field(..., title='Start time',
        description='Start time for the data. formatted as :%Y-%m-%dT00:00:00Z')
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
    units: str
    value: float

class MetserviceTimePointSummary(BaseModel):
    """Model for time point summary in Metservice API."""
    time: str
    latitude: float
    longitude: float
    variables: List[MetserviceVariable]