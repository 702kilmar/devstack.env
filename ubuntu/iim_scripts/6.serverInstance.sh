#nova boot --flavor tic2 --image xenial-server-cloudimg --security-group default2 --key-name masakari1 --meta HA_Enabled=true iim1

#openstack server create --flavor tic2 --image xenial-server-cloudimg --security-group default2 --key-name masakari1 iim1
# Must set HA_Enabled=true

#nova boot --flavor tic2 --image xenial-server-cloudimg --security-group default2 --key-name masakari1 --meta HA_Enabled=true iim1

#openstack server create --flavor m1.tiny --image cirros-0.3.5-x86_64-disk --security-group default2 --key-name masakari1 c1

#openstack server delete c1

#nova boot --flavor m1.small --image xenial-server-cloudimg --security-group default2 --key-name masakari1  webclient

nova boot --flavor m1.small --image xenial-server-cloudimg --security-group default2 --key-name masakari1 --meta HA_Enabled=true --config-drive true web-server-1

nova boot --flavor m1.small --image xenial-server-cloudimg-no-agent --security-group default2 --key-name masakari1 --meta HA_Enabled=true --config-drive true web-client
