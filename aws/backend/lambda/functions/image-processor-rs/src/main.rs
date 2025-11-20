use aws_sdk_dynamodb::types::AttributeValue;
use aws_sdk_dynamodb::Client as DynamoDbClient;
use aws_sdk_rekognition::types::{Image, S3Object as RekognitionS3Object};
use aws_sdk_rekognition::Client as RekognitionClient;
use aws_sdk_s3::Client as S3Client;
use lambda_runtime::{service_fn, Error, LambdaEvent};
use serde::Deserialize;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::env;
use std::time::SystemTime;
use tokio::sync::OnceCell;
use tracing::{error, info, warn};

// Struct to hold shared AWS clients
struct AppClients {
    s3: S3Client,
    rekognition: RekognitionClient,
    dynamodb: DynamoDbClient,
}

// Global static OnceCell to ensure clients are initialized only once.
static CLIENTS: OnceCell<AppClients> = OnceCell::const_new();

/// Initializes and returns a reference to the AWS clients.
/// This function will only execute the initialization logic once.
async fn get_clients() -> Result<&'static AppClients, Error> {
    CLIENTS
        .get_or_try_init(|| async {
            info!("Initializing AWS clients...");
            let config = aws_config::load_from_env().await;
            Ok(AppClients {
                s3: S3Client::new(&config),
                rekognition: RekognitionClient::new(&config),
                dynamodb: DynamoDbClient::new(&config),
            })
        })
        .await
}

#[derive(Deserialize, Debug)]
struct S3Event {
    #[serde(rename = "Records")]
    records: Vec<S3Record>,
}

#[derive(Deserialize, Debug)]
struct S3Record {
    s3: S3Info,
}

#[derive(Deserialize, Debug)]
struct S3Info {
    bucket: S3Bucket,
    object: S3Object,
}

#[derive(Deserialize, Debug)]
struct S3Bucket {
    name: String,
}

#[derive(Deserialize, Debug)]
struct S3Object {
    key: String,
}

/// Main Lambda function handler
async fn function_handler(event: LambdaEvent<S3Event>) -> Result<Value, Error> {
    let rekognition_collection_id = env::var("AWS_REKOGNITION_COLLECTION")
        .map_err(|_| "Environment variable AWS_REKOGNITION_COLLECTION not set")?;
    let person_table_name = env::var("PERSON_TABLE")
        .map_err(|_| "Environment variable PERSON_TABLE not set")?;

    // Get shared clients
    let clients = get_clients().await?;

    for record in event.payload.records {
        let bucket_name = &record.s3.bucket.name;
        let object_key = &record.s3.object.key;
        info!("Processing image: s3://{}/{}", bucket_name, object_key);

        if let Err(e) = process_record(
            clients,
            bucket_name,
            object_key,
            &rekognition_collection_id,
            &person_table_name,
        )
        .await
        {
            error!("Error processing record: {:?}. Details: {}", record, e);
        }
    }

    Ok(json!({ "statusCode": 200, "body": "Processing complete" }))
}

/// Process a single S3 record
async fn process_record(
    clients: &AppClients,
    bucket_name: &str,
    object_key: &str,
    collection_id: &str,
    table_name: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // 1. Get metadata from S3 object
    let head_object = clients
        .s3
        .head_object()
        .bucket(bucket_name)
        .key(object_key)
        .send()
        .await?;

    let metadata = head_object.metadata().ok_or("No metadata found")?;
    let person_id = metadata
        .get("person_id")
        .ok_or(format!("Missing 'person_id' in S3 metadata for {}", object_key))?;

    // 2. Index face directly into Rekognition Collection
    let s3_object_for_rekognition = RekognitionS3Object::builder()
        .bucket(bucket_name)
        .name(object_key)
        .build();

    let image_for_rekognition = Image::builder()
        .s3_object(s3_object_for_rekognition)
        .build();

    let index_faces_output = clients
        .rekognition
        .index_faces()
        .collection_id(collection_id)
        .image(image_for_rekognition)
        .external_image_id(person_id)
        .max_faces(1)
        .send()
        .await?;

    let face_record = index_faces_output
        .face_records()
        .and_then(|fr| fr.first())
        .ok_or("No face detected or quality too low.")?;

    let face = face_record.face().ok_or("No face data in record")?;
    let face_id = face.face_id().ok_or("No FaceId in face data")?;

    // 3. Save person and face metadata to DynamoDB
    let timestamp = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)?
        .as_secs()
        .to_string();

    let mut item = HashMap::new();
    item.insert("PersonId".to_string(), AttributeValue::S(person_id.to_string()));
    item.insert("FaceId".to_string(), AttributeValue::S(face_id.to_string()));
    item.insert("CreatedAt".to_string(), AttributeValue::S(timestamp.clone()));
    item.insert("LastUpdatedAt".to_string(), AttributeValue::S(timestamp));
    if let Some(confidence) = face.confidence() {
        item.insert(
            "Confidence".to_string(),
            AttributeValue::N(confidence.to_string()),
        );
    }

    // Add other metadata from S3
    for (key, value) in metadata {
        if key != "person_id" {
            item.insert(key.clone(), AttributeValue::S(value.clone()));
        }
    }

    clients
        .dynamodb
        .put_item()
        .table_name(table_name)
        .set_item(Some(item))
        .send()
        .await?;

    info!("Successfully enrolled person '{}' with FaceId '{}'", person_id, face_id);

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .without_time()
        .init();

    let func = service_fn(function_handler);
    lambda_runtime::run(func).await?;
    Ok(())
}
