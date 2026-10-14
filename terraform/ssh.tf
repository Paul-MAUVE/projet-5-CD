resource "aws_key_pair" "oc_p5" {
  key_name   = "oc-p5-key"
  public_key = file(pathexpand("~/.ssh/oc-p5-ec2.pub"))

  tags = {
    Name = "oc-p5-key"
  }
}