output "target_node_ip" {
  description = "IPv4 Address of the target node"
  value       = digitalocean_droplet.target_node.ipv4_address
}
