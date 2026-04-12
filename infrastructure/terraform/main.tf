terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.34"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

resource "digitalocean_ssh_key" "deplock_key" {
  name       = "Deplock SSH Key"
  public_key = file(var.ssh_public_key_path)
}

resource "digitalocean_droplet" "target_node" {
  image    = "ubuntu-24-04-x64"
  name     = "deplock-target-node"
  region   = "fra1"
  size     = "s-1vcpu-1gb"
  ssh_keys = [digitalocean_ssh_key.deplock_key.fingerprint]

  connection {
    type        = "ssh"
    user        = "root"
    private_key = file(var.ssh_private_key_path)
    host        = self.ipv4_address
  }
}
