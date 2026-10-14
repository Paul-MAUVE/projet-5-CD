resource "aws_instance" "oc_p5" {
  ami                    = "ami-0d618c1aec6a11c1c"
  instance_type          = "t3.micro"
  subnet_id              = data.aws_subnet.default.id
  key_name               = aws_key_pair.oc_p5.key_name
  vpc_security_group_ids = [aws_security_group.oc_p5_ssh.id]

  tags = {
    Name = "oc-p5-ec2"
  }
}