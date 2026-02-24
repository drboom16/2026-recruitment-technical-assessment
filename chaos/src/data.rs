use axum::{http::StatusCode, response::IntoResponse, Json};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub async fn process_data(Json(request): Json<DataRequest>) -> impl IntoResponse {
    // Calculate sums and return response
    let string_len = request.data.iter().filter(|x| x.is_string()).count();
    let int_sum = request.data.iter().filter(|x| x.is_number()).map(|x| x.as_i64().unwrap()).sum::<i64>();
    let response = DataResponse {
        string_len,
        int_sum,
    };

    (StatusCode::OK, Json(response))
}

#[derive(Deserialize)]
pub struct DataRequest {
    // Add any fields here
    pub data: Vec<Value>,
}

#[derive(Serialize)]
pub struct DataResponse {
    // Add any fields here
    pub string_len: u32,
    pub int_sum: i64,
}
