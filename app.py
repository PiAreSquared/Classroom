from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

SCOPES = ['https://www.googleapis.com/auth/classroom.courses', 'https://www.googleapis.com/auth/classroom.rosters', 'https://www.googleapis.com/auth/classroom.coursework.students']

def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)

    # Call the Classroom API
    results = service.courses().list(pageSize=1000).execute()
    courses = [result for result in results["courses"] if result["courseState"] == "ACTIVE"]
    classroom = {}

    if not courses:
        print('No courses found.')
    else:
        for course in courses:
            className = course['name']
            classroom[className] = {}
            students = service.courses().students().list(courseId = course["id"], pageSize=1000).execute()["students"]
            students = {student["userId"]: student["profile"]["name"]["fullName"] for student in students}
            courseWork = service.courses().courseWork().list(courseId = course["id"], pageSize=1000).execute()['courseWork']
            for work in courseWork:
                assignmentTitle = work["title"]
                classroom[className][assignmentTitle] = {}
                submissions = service.courses().courseWork().studentSubmissions().list(courseWorkId = work["id"], courseId = course["id"], pageSize=1000).execute()["studentSubmissions"]
                submissions = [submission for submission in submissions if submission["state"] == "RETURNED"]
                for submission in submissions:
                    max = [work["maxPoints"] for work in courseWork if work["id"] == submission["courseWorkId"]][0]
                    student = students[submission["userId"]]
                    score = str(submission["assignedGrade"]) + "/" + str(max)
                    classroom[className][assignmentTitle][student] = score
    
    print(json.dumps(classroom, indent=2))



if __name__ == '__main__':
    main()