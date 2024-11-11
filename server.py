# please run this in terminal : pip install fastapi uvicorn pydantic pandas numpy nltk

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import uvicorn
from typing import Dict, List, Optional
from process import count_items_same_order,remove_stopwords_nltk
from pymongo import MongoClient
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse



training_data = pd.read_csv("C://Users//lenovo//Desktop//teachtreckAI//roua//data.csv", encoding='utf-8') 

app = FastAPI()

training_data = pd.read_csv("C://Users//lenovo//Desktop//teachtreckAI//roua//data.csv", encoding='utf-8') # w hna zeda

current_question = {"domaine": None, "question": None, "correct_response": None}


    
class DomainRequest(BaseModel):
    domaine: str
    num_questions: int = 7

class ResponseRequest(BaseModel):
    user_responses: Dict[str, str] 
    examId:str
    userId: str 
   

@app.post("/ask_question/")
async def ask_question(request: DomainRequest):
    domaine = request.domaine
    num_questions = request.num_questions

    filtered_dataset = training_data[training_data['Domaine'] == domaine]

    if filtered_dataset.empty:
        return {"error": f"No questions available for the domain: {domaine}"}
    

    num_questions = min(num_questions, len(filtered_dataset))

    random_index = np.random.choice(filtered_dataset.index, size=num_questions, replace=False)
    random_questions = filtered_dataset.loc[random_index]
    
    questions_list = []
    for _, row in random_questions.iterrows():
        question = row['Question']
        correct_response = row['RÃ©ponse correcte']
        questions_list.append({
            "question": question,
            "correct_response": correct_response,
            "questionId": str(uuid.uuid4())
        })
    # correct_response = random_question['Réponse correcte']

    current_question["domaine"] = domaine
    current_question["question"] = [row['Question'] for _, row in random_questions.iterrows()]
    current_question["correct_response"] = [row['RÃ©ponse correcte'] for _, row in random_questions.iterrows()]

    return questions_list




client = MongoClient("mongodb://localhost:27017/")  # Adjust connection as needed
db = client["PfeBackFinal"]  # Replace with your actual database name
exams_collection = db["exams"]
responses_collection = db["answers"]
users_collection = db["users"] 



@app.post("/evaluate_response/")

async def evaluate_response(request: ResponseRequest):
    exam_id = request.examId
    user_id = request.userId
    user_responses = request.user_responses
    print("Received user_responses:", request.user_responses)  # Log received user responses
    print("Received examId:", request.examId) 

    # Ensure exam ID is valid
    if not ObjectId.is_valid(exam_id):
        return {"error": f"No exam found with examId: {exam_id}"}

    # Fetch the exam from the database
    exam = exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        return {"error": f"No exam found with examId: {exam_id}"}
    
    student = users_collection.find_one({"_id": ObjectId(user_id), "role": "STUDENT"})
    if not student:
        return {"error": f"No student found with userId: {user_id}"}

    evaluations = []
    total_score = 0

    # Loop through each user response and evaluate
    for question_id, user_response in user_responses.items():
        # Find the correct question in the exam by question ID
        question = next((q for q in exam['question'] if str(q.get('_id')) == str(question_id)), None)

        if question is None:
            print(f"Question with ID {question_id} not found in exam.")
            return {"error": f"No question found with questionId: {question_id}"}

        # Get the correct response for the question
        correct_response = question['correct_response']
        question_text = question['question']
        print(f"Correct response for question ID {question_id}: {correct_response}")

        # Process the responses
        user_response_keywords = remove_stopwords_nltk(user_response)
        correct_response_keywords = remove_stopwords_nltk(correct_response)

        # Calculate the score based on the user's response
        score = count_items_same_order(correct_response_keywords, user_response_keywords)
        score_ratio = score / len(correct_response_keywords) if len(correct_response_keywords) > 0 else 0

        # Append the evaluation result
        evaluations.append({
            "questionId": question_id,
            "user_response": user_response,
            "correct_response": correct_response,
            "question_text": question_text,
            "score": score,
            
            "score_ratio": score_ratio
        })

        total_score += score_ratio
        response_record = {
            "examId": exam_id,
            
            "examTitle": exam['title'],
            "examDescription": exam['description'],
            "examDomain": exam['domaine'],
            "total_score": total_score,
            
            "studentId": user_id,
            "studentUsername": student['username'],
           
           
            "evaluations": evaluations,
         
        }
    responses_collection.insert_one(response_record) 

    # Return the evaluation results and total score
    return {"evaluations": evaluations, "total_score": total_score}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # This allows your Angular app's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/get_exam_responses/{examId}")
async def get_exam_responses(examId: str):
    # Validate if the provided examId is a valid ObjectId
    if not ObjectId.is_valid(examId):
        return {"error": f"Invalid examId: {examId}"}

    # Fetch all responses related to the given examId
    responses =  list(responses_collection.find({"examId": examId}))

    # Convert the cursor to a list and return it

    return jsonable_encoder(responses, custom_encoder={ObjectId: str})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)