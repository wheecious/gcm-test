data "external" "env" {
  program = ["${path.module}/env.sh"]
}

data "google_compute_default_service_account" "default" {
}

resource "google_compute_network" "vpc_network" {
  project                 = data.external.env.result["project"]
  name                    = "hamster-vpc-network"
  auto_create_subnetworks = false
  mtu                     = 1460
}

resource "google_compute_subnetwork" "subnetwork_1" {
  name          = "hamster-vpc-sub-network"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_instance_template" "inst_template_public" {
  name_prefix = "hamster-template-public"
  labels = {
    app-name         = "hamster"
    server-visiblity = "public"
  }

  tags = ["hamster-server-public"]

  disk {
    source_image = "ubuntu-os-cloud/ubuntu-2204-jammy-v20230606"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network    = google_compute_network.vpc_network.id
    subnetwork = google_compute_subnetwork.subnetwork_1.id
    # access_config block makes the instance public. Uncomment this to make the instance public.
    access_config {
      network_tier = "STANDARD"
      }
  }


  metadata = {
    startup-script = file("./startup.sh")
  }

  machine_type = "e2-micro"

  scheduling {
    preemptible                 = "true"
    automatic_restart           = "false"
    provisioning_model          = "SPOT"
    instance_termination_action = "STOP"
  }

  lifecycle {
    create_before_destroy = "true"
  }

  service_account {
    email   = data.google_compute_default_service_account.default.email
    scopes  = ["cloud-platform"]
  }
}

resource "google_compute_region_instance_group_manager" "mig_public" {
  name               = "hamster-managed-instance-group-public"
  base_instance_name = "hamster-server-public"


  version {
    instance_template = google_compute_instance_template.inst_template_public.self_link_unique
  }
  target_size = 1
  named_port {
  name = "hamster-port"
  port = 8080
  }
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ingress-from-iap"
  network = google_compute_network.vpc_network.id
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["35.235.240.0/20"]
}

resource "google_compute_backend_service" "backend_service_public" {
  name                  = "hamster-load-balancer-backend-public"
  protocol              = "HTTP"
  port_name             = "hamster-port"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 10
  enable_cdn            = false
  health_checks         = [google_compute_health_check.health_check_public.id]
  backend {
    group           = google_compute_region_instance_group_manager.mig_public.instance_group
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }
}


resource "google_compute_health_check" "health_check_public" {
  name = "hamster-load-balancer-hc-public"
  # request_path        = "/"
  # port                = "8080"
  check_interval_sec  = 10
  timeout_sec         = 20
  unhealthy_threshold = 2
  healthy_threshold   = 2
  http_health_check {
    port         = "8080"
    request_path = "/"
  }
}

resource "google_compute_target_http_proxy" "target_http_proxy_public" {
  name    = "hamster-load-balancer-proxy-public"
  url_map = google_compute_url_map.compute_url_map_public.id
}

resource "google_compute_url_map" "compute_url_map_public" {
  name            = "hamster-load-balancer-public"
  default_service = google_compute_backend_service.backend_service_public.id
}

resource "google_compute_global_forwarding_rule" "forwarding_rule_public" {
  name                  = "hamster-load-balancer-front-end-public"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "80"
  target                = google_compute_target_http_proxy.target_http_proxy_public.id
}

output "env" {
  value = data.external.env.result
}
