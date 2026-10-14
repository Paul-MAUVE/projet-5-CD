resource "aws_security_group" "oc_p5_ssh" {
  name        = "oc-p5-ssh"
  description = "SSH access for Ansible - OC Project 5"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "oc-p5-ssh"
  }
}

resource "aws_vpc_security_group_ingress_rule" "oc_p5_ssh" {
  security_group_id = aws_security_group.oc_p5_ssh.id
  description       = "SSH from my public IP"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = "88.173.192.170/32"
}

resource "aws_vpc_security_group_egress_rule" "oc_p5_outbound" {
  security_group_id = aws_security_group.oc_p5_ssh.id
  description       = "Allow outbound IPv4 traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "oc_p5_http" {
  security_group_id = aws_security_group.oc_p5_ssh.id
  description       = "HTTP access to Angular application"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}