from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel, computed_field, Field
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Optional
import json 

app = FastAPI()


class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="Name of the patient", example="John Doe")] 
    city: Annotated[str, Field(..., description="City of the patient", example="New York")]
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient", example=30)] 
    gender: Annotated[Literal['male', 'female', 'other'], Field(..., description='Define your gender')] 
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in mtrs")] 
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kgs")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif 18.5 <= self.bmi < 24.9:
            return 'Normal weight'
        elif 25 <= self.bmi < 29.9: 
            return 'Overweight'
        else:
            return 'Obesity'

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120)]
    gender: Annotated[Optional[Literal['male', 'female', 'other']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

def load_data():
    with open('patients.json', 'r') as f:
        return json.load(f)
    
def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data, f)

@app.get('/')
def home():
    return {"message": "Welcome to the Patients app"}

@app.get('/patient')
def view_patient():
    data = load_data()
    return data

@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description="ID of the patient to retrieve",
                                        example="P001")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get('/sort')
def sort_patient(sort_by: str = Query(..., 
                                      description="Sort on the basis of height, weight or bmi"),
                                      order: str = Query('asc', 
                                                         description="Order can be asc or desc")):
    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort please select from {valid_fields}")
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Order should be asc or desc")
    
    data = load_data()
    sorted_order = True if order == 'desc' else False 

    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sorted_order)

    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    
    data[patient.id] = patient.model_dump(exclude=['id'])

    save_data(data)
    return JSONResponse(status_code=201, content={"message": "Patient created successfully"})

@app.put('/update/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient = data[patient_id]

    update_data = patient_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing_patient[key] = value 

    existing_patient['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient)

    existing_patient = patient_pydantic_obj.model_dump(exclude=['id'])

    data[patient_id] = existing_patient
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient updated successfully"})


@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})