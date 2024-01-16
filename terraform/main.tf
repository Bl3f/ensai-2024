provider "google" {
  project     = "ensai-2024"
  region      = "europe-west1"
  zone        = "europe-west1-b"
  credentials = "../ensai-2024-630e074aa45c.json"
}

resource "google_compute_instance" "christophe" {
  name         = "christophe"
  machine_type = "e2-standard-2"
  zone         = "europe-west1-b"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"

    access_config {
      // Ephemeral public IP
    }
  }
}

resource "google_storage_bucket" "bucket-functions" {
  name     = "christophe-functions"
  location = "EU"
}

resource "google_storage_bucket_object" "archive" {
  name   = "weather.zip"
  bucket = google_storage_bucket.bucket-functions.name
  source = "./functions/weather/weather.zip"
}

resource "google_cloudfunctions2_function" "function" {
  name        = "weather-christophe-tf"
  description = "Christophe function (from Terraform)"
  location = "europe-west1"

  build_config {
    runtime = "python312"
    entry_point = "hello_http"  # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket-functions.name
        object = google_storage_bucket_object.archive.name
      }
    }
  }

  service_config {
    max_instance_count  = 1
    available_memory    = "256M"
    timeout_seconds     = 60
  }
}

data "google_service_account" "christophe" {
  account_id = "christophe"
}

resource "google_cloud_scheduler_job" "job" {
  name             = "weather-job"
  description      = "Weather daily job"
  schedule         = "50 23 * * *"
  time_zone        = "Europe/Paris"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions2_function.function.service_config[0].uri

    oidc_token {
      service_account_email = data.google_service_account.christophe.email
    }
  }
}
