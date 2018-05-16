cd ~stack
git clone https://github.com/openstack/masakari-monitors.git
sudo mkdir -p /etc/masakarimonitors
cd masakari-monitors/
sudo python setup.py install
sudo tox -egenconfig
cd etc/masakarimonitors
sudo cp hostmonitor.conf.sample  /etc/masakarimonitors/hostmonitor.conf
sudo cp processmonitor.conf.sample  /etc/masakarimonitors/processmonitor.conf
sudo cp masakarimonitors.conf.sample  /etc/masakarimonitors/masakarimonitors.conf
sudo cp process_list.yaml.sample /etc/masakarimonitors/process_list.yaml 
