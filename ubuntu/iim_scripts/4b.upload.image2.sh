openstack image create --public \
 --disk-format qcow2 --container-format bare \
 --file ../xenial-server-cloudimg-amd64-disk1.img \
 --public \
 --property hw_qemu_guest_agent=no \
 xenial-server-cloudimg-no-agent
