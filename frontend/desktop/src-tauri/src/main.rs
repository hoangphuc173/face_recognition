#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Serialize, Deserialize};
use std::sync::{Mutex, Arc};

// A simple in-memory database for people
#[derive(Debug, Serialize, Deserialize, Clone)]
struct Person {
    id: u64,
    name: String,
    image_url: String, // For now, this will be a file path or a placeholder
}

// The shared application state
struct AppState {
    people: Arc<Mutex<Vec<Person>>>,
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn login(email: &str, password: &str) -> Result<String, String> {
    // Hardcoded credentials for demonstration
    if email == "admin@test.com" && password == "password" {
        Ok("Login successful!".to_string())
    } else {
        Err("Invalid email or password.".to_string())
    }
}

#[tauri::command]
fn get_people(state: tauri::State<AppState>) -> Result<Vec<Person>, String> {
    let people = state.people.lock().unwrap().clone();
    Ok(people)
}

#[tauri::command]
fn add_person(name: String, image_url: String, state: tauri::State<AppState>) -> Result<Vec<Person>, String> {
    let mut people = state.people.lock().unwrap();
    let new_id = people.iter().map(|p| p.id).max().unwrap_or(0) + 1;
    let new_person = Person {
        id: new_id,
        name,
        image_url,
    };
    people.push(new_person);
    Ok(people.clone())
}

#[tauri::command]
fn delete_person(id: u64, state: tauri::State<AppState>) -> Result<Vec<Person>, String> {
    let mut people = state.people.lock().unwrap();
    people.retain(|p| p.id != id);
    Ok(people.clone())
}

fn main() {
    let initial_people = vec![
        Person { id: 1, name: "John Doe".to_string(), image_url: "https://via.placeholder.com/150".to_string() },
        Person { id: 2, name: "Jane Smith".to_string(), image_url: "https://via.placeholder.com/150".to_string() },
    ];

    let app_state = AppState {
        people: Arc::new(Mutex::new(initial_people)),
    };

    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            greet,
            login,
            get_people,
            add_person,
            delete_person
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}