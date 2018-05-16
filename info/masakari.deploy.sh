cd /home/stack
sudo su - stack
git clone  https://github.com/openstack/python-masakariclient.git
cd python-masakariclient/
sudo python setup.py install
source ~/admin-openrc.sh
masakari  segment-list
cd /home/stack
git clone https://github.com/openstack/masakari-monitors.git
sudo mkdir -p /etc/masakarimonitors
cd masakari-monitors/
sudo python setup.py install
sudo tox -egenconfig
cd etc
cd etc/masakarimonitors
sudo cp hostmonitor.conf.sample  /etc/masakarimonitors/hostmonitor.conf
sudo cp processmonitor.conf.sample  /etc/masakarimonitors/processmonitor.conf
sudo cp masakarimonitors.conf.sample  /etc/masakarimonitors/masakarimonitors.conf
sudo cp process_list.yaml.sample /etc/masakarimonitors/process_list.yaml

masakari-processmonitor.sh /etc/masakarimonitors/processmonitor.conf /etc/masakarimonitors/proc.list
masakari-hostmonitor.sh /etc/masakarimonitors/hostmonitor.conf

###

##
masakari segment-create --name test1 --recovery-method auto --service-type auto
masakari host-create --name masakari-2 --segment-id test1 --type auto --control-attributes auto
masakari host-create --name web-server-1 --segment-id test1 --type auto --control-attributes auto

 2015  masakari host-list --segment-id test1
 2016  masakari host-delete --segment-id test1
 2017  masakari host-delete --segment-id test1 --id c9ee87ce-ffdd-4276-a2e3-e9a75e82be6a

 2018  masakari host-list --segment-id test1
masakari host-create --name web-server-1 --segment-id test1 --type auto --control-attributes auto
 2020  history

