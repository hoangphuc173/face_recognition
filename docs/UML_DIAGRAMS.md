# UML Diagrams for Face Recognition System (All PlantUML)

This document contains **PlantUML** code for all diagrams. 

> [!IMPORTANT]
> **INSTRUCTIONS FOR DRAW.IO:**
> 1. Open [draw.io](https://app.diagrams.net/)
> 2. Go to **Arrange > Insert > Advanced > PlantUML**
> 3. Copy **ONLY** the code between the comments `' START COPYING HERE` and `' END COPYING HERE`.
> 4. **DO NOT** copy the ` ```plantuml ` or ` ``` ` lines.

## 1. Use Case Diagram

```plantuml
' START COPYING HERE
@startuml
left to right direction
skinparam packageStyle rectangle

actor "User" as U
actor "Admin" as A
actor "Staff" as S
actor "Guest" as G

package "Authentication" {
    usecase "Login" as UC1
    usecase "Register" as UC2
    usecase "Forgot Password" as UC3
    usecase "Manage Profile" as UC4
}

package "Face Recognition" {
    usecase "Enroll Face" as UC5
    usecase "Identify Face" as UC6
    usecase "Delete Face" as UC7
}

package "Administration" {
    usecase "Manage Users" as UC8
    usecase "View Access Logs" as UC9
}

U <|-- A
U <|-- S
U <|-- G

U --> UC1
U --> UC2
U --> UC3
U --> UC4

S --> UC5
S --> UC6

A --> UC5
A --> UC6
A --> UC7
A --> UC8
A --> UC9
@enduml
' END COPYING HERE
```

## 2. Architecture Diagram (AWS Style)

```plantuml
' START COPYING HERE
@startuml
!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v14.0/dist
!include AWSPuml/AWSCommon.puml
!include AWSPuml/General/User.puml
!include AWSPuml/Mobile/APIGateway.puml
!include AWSPuml/Compute/Lambda.puml
!include AWSPuml/Database/DynamoDB.puml
!include AWSPuml/Storage/SimpleStorageService.puml
!include AWSPuml/MachineLearning/Rekognition.puml
!include AWSPuml/SecurityIdentityCompliance/Cognito.puml
!include AWSPuml/SecurityIdentityCompliance/KeyManagementService.puml

title Face Recognition System Architecture

left to right direction

actor "User" as user
actor "Admin" as admin

package "AWS Cloud" {
    package "Public Zone" {
        APIGateway(api, "API Gateway", "REST API")
        Cognito(cognito, "Cognito User Pool", "Auth & Users")
    }

    package "Compute Layer (Serverless)" {
        Lambda(authFn, "Auth Handler", "User Mgmt")
        Lambda(enrollFn, "Enroll Handler", "Face Indexing")
        Lambda(identifyFn, "Identify Handler", "Face Search")
        Lambda(peopleFn, "People Handler", "Profile Mgmt")
        Lambda(loggingFn, "Logging Handler", "Access Logs")
    }

    package "Storage & Data Layer" {
        SimpleStorageService(rawBucket, "Raw Bucket", "Images")
        SimpleStorageService(processedBucket, "Processed Bucket", "Thumbnails")
        
        DynamoDB(usersTable, "Users Table", "Metadata")
        DynamoDB(logsTable, "Access Logs", "History")
        DynamoDB(profilesTable, "User Profiles", "Details")
        
        Rekognition(rekognition, "Rekognition", "Face Collection")
    }
    
    package "Security" {
        KeyManagementService(kms, "KMS", "Encryption Keys")
    }
}

user --> api : HTTPS
admin --> api : HTTPS

api --> authFn : /auth
api --> enrollFn : /enroll
api --> identifyFn : /identify
api --> peopleFn : /people
api --> loggingFn : /logs

authFn --> cognito : Auth/User Mgmt
authFn --> profilesTable : Read/Write

enrollFn --> rawBucket : Upload Image
enrollFn --> rekognition : IndexFaces
enrollFn --> usersTable : Save Metadata
enrollFn --> kms : Decrypt

identifyFn --> rekognition : SearchFacesByImage
identifyFn --> usersTable : Lookup User
identifyFn --> logsTable : Record Log

peopleFn --> usersTable : Update/Delete
peopleFn --> rekognition : DeleteFaces

loggingFn --> logsTable : Read Logs

@enduml
' END COPYING HERE
```

## 3. Sequence Diagram (Identify Face)

```plantuml
' START COPYING HERE
@startuml
actor User as U
participant "API Gateway" as API
participant "Identify Lambda" as L
participant "Rekognition" as R
participant "DynamoDB" as DB
participant "Logs DB" as LDB

U -> API: POST /identify (Image)
activate API
API -> L: Invoke Lambda
activate L

L -> R: SearchFacesByImage(Image)
activate R
R --> L: Face Matches (FaceId, Confidence)
deactivate R

alt Face Found
    L -> DB: GetItem(FaceId)
    activate DB
    DB --> L: User Details
    deactivate DB
    
    L -> LDB: PutItem(Log Entry)
    activate LDB
    LDB --> L: Success
    deactivate LDB
    
    L --> API: 200 OK (User Info)
    API --> U: Display User Info
else No Face Found
    L --> API: 404 Not Found
    API --> U: "Unknown Person"
end

deactivate L
deactivate API
@enduml
' END COPYING HERE
```

## 4. Deployment Diagram

```plantuml
' START COPYING HERE
@startuml
!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v14.0/dist
!include AWSPuml/AWSCommon.puml
!include AWSPuml/General/Client.puml
!include AWSPuml/NetworkingAndContentDelivery/CloudFront.puml
!include AWSPuml/Storage/SimpleStorageService.puml
!include AWSPuml/Mobile/APIGateway.puml
!include AWSPuml/Compute/Lambda.puml
!include AWSPuml/Database/DynamoDB.puml

title Deployment Diagram

node "Client Device" {
    Client(browser, "Web/Desktop App", "React/Electron")
}

package "AWS Cloud" {
    package "Frontend Hosting" {
        CloudFront(cf, "CloudFront", "CDN")
        SimpleStorageService(webBucket, "Web Bucket", "Static Assets")
    }

    package "Backend API" {
        APIGateway(api, "API Gateway", "Regional Endpoint")
        
        node "Lambda Functions" {
            Lambda(fn1, "Auth Function", "Python 3.11")
            Lambda(fn2, "Enroll Function", "Python 3.11")
            Lambda(fn3, "Identify Function", "Python 3.11")
        }
    }

    package "Data Persistence" {
        DynamoDB(db, "DynamoDB Tables", "On-Demand")
    }
}

browser --> cf : HTTPS (Frontend)
cf --> webBucket : Origin
browser --> api : HTTPS (API Calls)
api --> fn1
api --> fn2
api --> fn3
fn1 --> db
fn2 --> db
fn3 --> db

@enduml
' END COPYING HERE
```

## 5. Data Diagram (ERD)

```plantuml
' START COPYING HERE
@startuml
hide circle
skinparam linetype ortho

entity "USERS" as users {
  *UserId : string <<PK>>
  --
  FaceId : string <<FK>>
  FullName : string
  Email : string
  CreatedAt : string
}

entity "USER_PROFILES" as profiles {
  *UserId : string <<PK>>
  --
  Address : string
  PhoneNumber : string
  Department : string
  Role : string
}

entity "ACCESS_LOGS" as logs {
  *LogId : string <<PK>>
  --
  UserId : string <<FK>>
  Timestamp : string
  Confidence : float
  Action : string
}

entity "OTP_VERIFICATION" as otp {
  *Email : string <<PK>>
  --
  OTP : string
  TTL : int
}

users ||..|| profiles : "has details"
users ||..o{ logs : "generates"
users ||..o{ otp : "verifies"
@enduml
' END COPYING HERE
```
