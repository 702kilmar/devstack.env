openstack security group  create default2

openstack security group rule create --proto icmp --dst-port 0 default2
openstack security group rule create --proto tcp --dst-port 22 default2
