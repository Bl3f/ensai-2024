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