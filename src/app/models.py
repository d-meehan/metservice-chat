from typing import Optional
from datetime import date, time

from pydantic import BaseModel, Field, ConfigDict

from utils.constants import QueryPeriodsEnum, QueryTypesEnum

class QueryClassification(BaseModel):
    """Model for weather queries."""    
    query_type: list[QueryTypesEnum] = Field(..., title='Weather query type',
        description='What type of query has the user sent?')
    location: Optional[str] = Field(None, title='Location',
        description='The location the user is asking about.')
    query_from_date: date = Field(..., title='First Date',
        description='The first day to request data for, formatted as :%Y-%m-%d')
    query_to_date: date = Field(..., title='Last Date',
        description='The last day to request data for, formatted as :%Y-%m-%d. Unless query_period is "multi-day", this should be the same as query_from_date.')
    query_period: list[QueryPeriodsEnum] = Field(..., title='Query period',
        description='The period of time the user is asking about. If they are ask for specific times select a period that includes that time: morning=6-11.59, afternoon=12-17.59, evening=18-23.59, night=0-5.59. If they are asking for multiple days or a week, select "multiple_days".')
class ModelResponseToWeatherQuery(QueryClassification):
    """Request model for weather queries."""
    response: str = Field(..., title='Response',
        description='Response from WeatherBot to the user query.')

class MetservicePointTimeRequest(BaseModel):
    """Required criteria for Metservice API call."""
    latitude: float
    longitude: float
    variables: list[str]
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
    hour: time
    variables: list[MetserviceVariable]

class MetservicePeriodSummary(BaseModel):
    """Model for period summary in Metservice API."""
    weather_data_types: list[QueryTypesEnum]
    period_types: list[QueryPeriodsEnum]
    date: date
    latitude: float
    longitude: float
    location: Optional[str] = None
    hour_summaries: list[MetserviceTimePointSummary]
