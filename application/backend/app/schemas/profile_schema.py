from typing import Optional, List
from pydantic import BaseModel, Field

class AppointmentSchema(BaseModel):
    id: Optional[str] = None
    doctor: str
    specialty: str
    hospital: str
    date: str
    time: str
    type: str
    status: Optional[str] = "Confirmed"

class VitalSchema(BaseModel):
    id: Optional[str] = None
    name: str
    value: str
    unit: str
    status: str
    icon: Optional[str] = "activity"
    color: Optional[str] = "text-teal-400"

class ScheduleReminderSchema(BaseModel):
    id: Optional[str] = None
    name: str
    time: str
    dose: str
    taken: bool = False
    meal: Optional[str] = "After Meal"
    refills: Optional[str] = "30 refills left"
